import datetime
from typing import Union

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, User
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from sqlalchemy.ext.asyncio.session import AsyncSession

from config import Config
from cruds.trackings import TrackingManager
from keyboards.start import return_to_start_keyboard
from keyboards.trackings import start_create_tracking_from_scratch_kb, skip_max_price_kb, edit_tracking_kb, \
    back_to_tracking_kb, edit_max_price_kb, seats_found_kb
from models.users import UserModel
from schemas.trackings import TrackingCreateSchema, TrackingUpdateSchema
from states.editing_tracking import EditingTracking
from utils.add_messages_in_state_to_delete import add_messages_in_state_to_delete
from utils.filter_trains import filter_trains
from utils.rzd_links_generator import create_url_to_trains
from utils.rzd_parser import RZDParser

router = Router()

async def send_tracking_menu(
        user: User,
        bot: Bot,
        tracking_data: dict,
        additional_text: str = '',
        return_callback_data: str = 'start'
) -> Message:
    """
    tracking_data должна выглядеть так:

    {'from_city_name': 'Киров', 'from_city_id': '2060600', 'from_city_site_code': 'awd',
    'to_city_name': 'Москва', 'to_city_id': '2000000', 'to_city_site_code': 'awd1',
    'date': '2024-02-28', 'max_price': 1300.0}

    или

    'from_city_name': 'Киров', 'from_city_id': '2060600', 'from_city_site_code': 'awd',
    'to_city_name': 'Москва', 'to_city_id': '2000000', 'to_city_site_code': 'awd1',
    'date': '2024-02-28', 'max_price': None, 'tracking_id': 12}
    """

    tracking_id = tracking_data.get('tracking_id')

    from_city_name = tracking_data['from_city_name']
    from_city_id = tracking_data['from_city_id']
    from_city_site_code = tracking_data['from_city_site_code']

    to_city_name = tracking_data['to_city_name']
    to_city_id = tracking_data['to_city_id']
    to_city_site_code = tracking_data['to_city_site_code']

    date = datetime.date.fromisoformat(tracking_data['date']) if tracking_data['date'] else None
    max_price = tracking_data['max_price']

    text = ''
    if additional_text:
        text = (
            f'{additional_text}\n'
            f'----\n'
            f'\n'
        )

    if tracking_id is None:
        text += f'📗 Новое отслеживание:\n\n'
    else:
        text += f'📗 Отслеживание #{tracking_id}:\n\n'

    text += (
        '✏️ Вы можете <b>отредактировать отслеживание</b> нажав на одну из соответствующих кнопок ниже.\n'
        'Когда вы придете к финальной версии, необходимо <b>нажать на кнопку "Сохранить"</b>\n\n'
    )

    date_text = date.strftime("%d.%m.%Y") if date else 'необходимо указать'
    text += (
        f'<b>Откуда:</b> {from_city_name}\n'
        f'<b>Куда:</b> {to_city_name}\n'
        f'<b>Дата отправления:</b> {date_text}\n'
    )
    if max_price is not None:
        text += '<b>Цена до:</b> {:.2f}₽'.format(max_price)

    return await bot.send_message(
        chat_id=user.id,
        text=text,
        parse_mode='HTML',
        reply_markup=edit_tracking_kb(is_new_tracking=(tracking_id is None), return_callback_data=return_callback_data),
        disable_web_page_preview=True
    )

@router.callback_query(F.data == 'edit_tracking')
async def open_tracking(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    tracking_data = (await state.get_data())['tracking_data']
    sent_message = await send_tracking_menu(
        user=callback.from_user,
        bot=callback.bot,
        tracking_data=tracking_data,
    )

    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )


@router.callback_query(F.data == 'tracking_edit_from_city')
@router.callback_query(F.data == 'tracking_edit_to_city')
async def edit_city(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'tracking_edit_from_city':
        text = (
            f'<b>Введите город</b>, откуда будет отправляться поезд\n'
        )
        await state.set_state(EditingTracking.city_from)
    else:
        text = (
            f'Введите <b>город прибытия</b>\n'
        )
        await state.set_state(EditingTracking.city_to)

    sent_message = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=back_to_tracking_kb()
    )

    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )


@router.message(StateFilter(EditingTracking.city_from, EditingTracking.city_to))
async def handle_edit_city(
        message: Message,
        state: FSMContext,
        rzd_parser: RZDParser
):
    current_state = await state.get_state()

    # ищем указанный город
    cities = await rzd_parser.get_cities_by_query(message.text)
    # если не нашли, то просим ввести снова
    if len(cities) == 0:
        city_type_text = 'отправления' if current_state == EditingTracking.city_from else 'прибытия'
        text = (
            f'Мы не смогли распознать город {city_type_text} :(\n\n'
            f'Пожалуйста, попробуйте указать его снова, используя его <b>полное название</b>\n'
        )
        sent_message = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=text,
            parse_mode='HTML'
        )
        await add_messages_in_state_to_delete(
            query=message,
            state=state,
            messages=[sent_message],
            delete_prev_messages=True
        )
        return

    selected_city = cities[0]
    tracking_data: dict = (await state.get_data())['tracking_data']

    if current_state == EditingTracking.city_from:
        tracking_data.update({
            'from_city_name': selected_city.name,
            'from_city_id': selected_city.station_code,
            'from_city_site_code': selected_city.site_code
        })
    else:
        tracking_data.update({
            'to_city_name': selected_city.name,
            'to_city_id': selected_city.station_code,
            'to_city_site_code': selected_city.site_code
        })
    await state.update_data({'tracking_data': tracking_data})

    sent_message = await send_tracking_menu(
        user=message.from_user,
        bot=message.bot,
        tracking_data=tracking_data,
        additional_text=f'<b>Город '
                        f'{"отправления" if current_state == EditingTracking.city_from else "прибытия"} '
                        f'успешно изменён</b>'
    )
    await add_messages_in_state_to_delete(
        query=message,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )
@router.callback_query(F.data == 'tracking_edit_date')
async def edit_date(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.set_state(EditingTracking.date)
    text = (
        f'Укажите <b>дату, на которую необходимо установить отслеживание (дату отправления поезда)</b>\n\n'
        f'Формат: ДД.ММ.ГГГГ или ДД.ММ\n'
        f'Пример: {datetime.datetime.utcnow().strftime("%d.%m.%Y")}\n'
    )
    sent_message = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=back_to_tracking_kb()
    )

    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )

@router.message(StateFilter(EditingTracking.date))
async def handle_edit_date(
        message: Message,
        state: FSMContext
):
    error_text_ending = (
        f'\n'
        f'Формат: ДД.ММ.ГГГГ или ДД.ММ\n'
        f'Пример: {datetime.datetime.utcnow().strftime("%d.%m.%Y")}\n'
    )

    # Проверка на формат введенной даты (попытка спарсить)
    date_parsed = False
    try:
        date = datetime.datetime.strptime(message.text, '%d.%m.%Y')
        date_parsed = True
    except ValueError:
        try:
            date = datetime.datetime.strptime(f'{message.text}.{datetime.date.today().year}', '%d.%m.%Y')
            date_parsed = True
        except ValueError:
            pass

    if not date_parsed:
        text = (
            '<b>Вы указали дату в неверном формате.</b> Укажите её снова, используя описанный нами формат\n'
            f'{error_text_ending}'
        )
        sent_message = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=text,
            parse_mode='HTML'
        )
        await add_messages_in_state_to_delete(
            query=message,
            state=state,
            messages=[sent_message],
            delete_prev_messages=True
        )
        return

    # Проверка на то, что дата ещё не прошла
    if (date + datetime.timedelta(days=1)) < datetime.datetime.utcnow():
        text = (
            '<b>Вы указали дату, которая уже прошла.</b> Пожалуйста, укажите будущую дату для отслеживания\n'
            f'{error_text_ending}'
        )
        sent_message = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=text,
            parse_mode='HTML'
        )
        await add_messages_in_state_to_delete(
            query=message,
            state=state,
            messages=[sent_message],
            delete_prev_messages=True
        )
        return

    # Проверка на то, что дата в пределах 6 месяцев от сегодня
    if date > datetime.datetime.utcnow() + datetime.timedelta(days=180):
        text = (
            '<b>Вы указали слишком далёкую дату.</b> '
            'Пожалуйста, укажите дату, которая будет в пределах 6 месяцев от текущего дня\n'
            f'{error_text_ending}'
        )
        sent_message = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=text,
            parse_mode='HTML'
        )
        await add_messages_in_state_to_delete(
            query=message,
            state=state,
            messages=[sent_message],
            delete_prev_messages=True
        )
        return

    tracking_data: dict = (await state.get_data())['tracking_data']
    tracking_data.update({
        'date': date.date().isoformat()
    })
    await state.set_state(None)
    await state.update_data({'tracking_data': tracking_data})

    sent_message = await send_tracking_menu(
        user=message.from_user,
        bot=message.bot,
        tracking_data=tracking_data,
        additional_text='<b>Дата отслеживания успешно обновлена</b>'
    )
    await add_messages_in_state_to_delete(
        query=message,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )


@router.callback_query(F.data == 'tracking_edit_max_price')
async def edit_max_price(
        callback: CallbackQuery,
        state: FSMContext
):
    await state.set_state(EditingTracking.max_price)
    text = (
        'Введите <b>максимальную цену</b>, за которую готовы купить билет, или <b>нажмите на кнопку "не указывать"</b>'
    )
    sent_message = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode='HTML',
        disable_web_page_preview=True,
        reply_markup=edit_max_price_kb()
    )
    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )

@router.callback_query(F.data == 'set_null_edit_max_price')
@router.message(StateFilter(EditingTracking.max_price))
async def handle_edit_max_price(
        message_or_callback: Union[Message, CallbackQuery],
        state: FSMContext
):
    if type(message_or_callback) is CallbackQuery:
        max_price = None
    else:
        try:
            max_price = float(message_or_callback.text)
        except ValueError:
            text = (
                'Неверный формат данных, необходимо указать числом <b>максимальную цену, за которую готовы купить билет.</b> '
                'Вы можете пропустить этот этап, нажав на кнопку ниже\n'
            )
            sent_message = await message_or_callback.bot.send_message(
                chat_id=message_or_callback.from_user.id,
                text=text,
                parse_mode='HTML',
                reply_markup=skip_max_price_kb()
            )
            await add_messages_in_state_to_delete(
                query=message_or_callback,
                state=state,
                messages=[sent_message],
                delete_prev_messages=True
            )
            return

    tracking_data: dict = (await state.get_data())['tracking_data']
    tracking_data.update({
        'max_price': max_price
    })
    await state.update_data({'tracking_data': tracking_data})

    sent_message = await send_tracking_menu(
        user=message_or_callback.from_user,
        bot=message_or_callback.bot,
        tracking_data=tracking_data
    )

    await add_messages_in_state_to_delete(
        query=message_or_callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )

    await state.set_state(None)

@router.callback_query(F.data == 'save_tracking')
async def save_tracking(
        callback: CallbackQuery,
        current_user: UserModel,
        state: FSMContext,
        config: Config,
        session: AsyncSession,
        rzd_parser: RZDParser
):
    tracking_data = (await state.get_data())['tracking_data']
    if tracking_data['date'] is None:
        await callback.answer(
            text='❌ Для сохранения необходимо указать дату отправления',
            show_alert=True
        )
        return

    # Проверка наличие билетов. Если их много (определить что такое много),
    #  то выводим ссылку на покупку и не ставим отслеживание
    sent_message = await send_tracking_menu(
        user=callback.from_user,
        bot=callback.bot,
        tracking_data=tracking_data,
        additional_text='<b>ℹ️ Проверяем данные...</b>'
    )
    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )

    trains_on_this_route = await rzd_parser.get_trains(
        from_city_id=tracking_data['from_city_id'],
        to_city_id=tracking_data['to_city_id'],
        date=datetime.date.fromisoformat(tracking_data['date'])
    )
    specific_trains = filter_trains(
        trains=trains_on_this_route,
        max_price=tracking_data['max_price']
    )
    if len(specific_trains) > 0:
        url = create_url_to_trains(
            from_city_site_code=tracking_data["from_city_site_code"],
            to_city_site_code=tracking_data["to_city_site_code"],
            date=tracking_data["date"]
        )
        text = (
            '<b>✅ Найдено больше одного места по вашему запросу,</b> нажмите на кнопку ниже чтобы перейти на сайт РЖД'
            '\n\n'
            '<i>Отслеживание, из-за текущего наличия мест, не сохранено</i>'
        )
        sent_message = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            parse_mode='HTML',
            reply_markup=seats_found_kb(rzd_url=url)
        )
        await add_messages_in_state_to_delete(
            query=callback,
            state=state,
            messages=[sent_message],
            delete_prev_messages=True
        )
        return

    # Сохраняем отслеживание

    tracking_manager = TrackingManager(session=session)

    # Если отслеживание новое

    if 'tracking_id' not in tracking_data:
        # проверка на то, что ещё не существует аналогичного отслеживания
        repeated_tracking = await tracking_manager.get_by_unique_value(
            user_id=current_user.id,
            from_city_name=tracking_data['from_city_name'],
            from_city_id=tracking_data['from_city_id'],
            from_city_site_code=tracking_data['from_city_site_code'],
            to_city_name=tracking_data['to_city_name'],
            to_city_id=tracking_data['to_city_id'],
            to_city_site_code=tracking_data['to_city_site_code'],
            date=datetime.date.fromisoformat(tracking_data['date']),
            max_price=tracking_data.get('max_price'),
            is_finished=False
        )

        if repeated_tracking is not None:
            sent_message = await send_tracking_menu(
                user=callback.from_user,
                bot=callback.bot,
                tracking_data=tracking_data,
                additional_text=f'<b>❌ Активное отслеживание с такими данными уже существует.</b>\n'
                                f'<a href="'
                                f'https://t.me/{config.tg_bot.username}?start=tracking_open_{repeated_tracking.id}'
                                f'">'
                                f'Вот его номер: #{repeated_tracking.id} (кликабельно)'
                                f'</a>'
            )
            await add_messages_in_state_to_delete(
                query=callback,
                state=state,
                messages=[sent_message],
                delete_prev_messages=True
            )
            return

        tracking = await tracking_manager.create(TrackingCreateSchema(
            user_id=current_user.id,
            from_city_name=tracking_data['from_city_name'],
            from_city_id=tracking_data['from_city_id'],
            from_city_site_code=tracking_data['from_city_site_code'],
            to_city_name=tracking_data['to_city_name'],
            to_city_id=tracking_data['to_city_id'],
            to_city_site_code=tracking_data['to_city_site_code'],
            date=tracking_data['date'],
            max_price=tracking_data.get('max_price')
        ))
        tracking_data['tracking_id'] = tracking.id
        saved_text = '<b>✅ Отслеживание успешно создано</b>'
    else:
        # проверка на то, что отслеживание принадлежит этому юзеру
        this_tracking = await tracking_manager.get(tracking_data['tracking_id'])
        if current_user.id != this_tracking.user_id:
            return

        await tracking_manager.update(
            obj_id=tracking_data['tracking_id'],
            obj_in=TrackingCreateSchema(
                user_id=current_user.id,
                from_city_name=tracking_data['from_city_name'],
                from_city_id=tracking_data['from_city_id'],
                from_city_site_code=tracking_data['from_city_site_code'],
                to_city_name=tracking_data['to_city_name'],
                to_city_id=tracking_data['to_city_id'],
                to_city_site_code=tracking_data['to_city_site_code'],
                date=tracking_data['date'],
                max_price=tracking_data.get('max_price')
            )
        )
        saved_text = '<b>✅ Отслеживание обновлено</b>'

    await session.commit()

    state_data = await state.get_data()
    state_data['tracking_data'] = tracking_data
    await state.set_data(state_data)

    sent_message = await send_tracking_menu(
        user=callback.from_user,
        bot=callback.bot,
        tracking_data=tracking_data,
        additional_text=saved_text
    )
    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )

@router.callback_query(F.data == 'finish_tracking')
async def finish_tracking(
        callback: CallbackQuery,
        current_user: UserModel,
        state: FSMContext,
        session: AsyncSession
):
    tracking_manager = TrackingManager(session=session)
    tracking_data = (await state.get_data())['tracking_data']

    this_tracking = await tracking_manager.get(tracking_data['tracking_id'])
    if current_user.id != this_tracking.user_id:
        return

    await tracking_manager.update(
        obj_id=tracking_data['tracking_id'],
        obj_in=TrackingUpdateSchema(is_finished=True)
    )
    await session.commit()

    text = f'📕 Отслеживание #{this_tracking.id} успешно удалено'
    sent_message = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode='HTML',
        reply_markup=return_to_start_keyboard()
    )
    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )
