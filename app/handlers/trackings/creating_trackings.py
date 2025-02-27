import datetime
from typing import Union

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, CommandObject, Command
from sqlalchemy.ext.asyncio.session import AsyncSession

from config import Config
from cruds.trackings import TrackingManager
from filters.at_least_one_tracking_exists_filter import AtLeastOneTrackingExistsFilter
from filters.start_args_filter import StartArgsFilter
from handlers.trackings.editing_tracking import send_tracking_menu
from keyboards.trackings import start_create_tracking_from_scratch_kb, skip_max_price_kb, go_to_current_trackings_kb
from models.users import UserModel
from states.creating_tracking import CreatingTracking
from utils.add_messages_in_state_to_delete import add_messages_in_state_to_delete
from utils.rzd_parser import RZDParser

router = Router()


@router.callback_query(F.data == 'create_tracking', AtLeastOneTrackingExistsFilter())
async def start_create_tracking_with_existing_trackings(
        callback: CallbackQuery,
        current_user: UserModel,
        state: FSMContext,
        config: Config,
        session: AsyncSession
):
    tracking_manager = TrackingManager(session=session)
    user_trackings = await tracking_manager.get_user_trackings(user_id=callback.from_user.id, only_active=False)

    #  проверка на количество уже созданных отслеживаний. Если уже больше 5, то нельзя
    if len(list(filter(lambda tracking: not tracking.is_finished, user_trackings))) >= 5:
        text = (
            '❌ Вы уже создали максимальное количество активных отслеживаний. '
            '<b>Удалите одно из текущих отслеживаний</b>, чтобы создать новое'
        )

        sent_message = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            parse_mode='HTML',
            reply_markup=go_to_current_trackings_kb(),
            disable_web_page_preview=True
        )

        await add_messages_in_state_to_delete(
            query=callback,
            state=state,
            messages=[sent_message],
            delete_prev_messages=True
        )
        return

    text = (
        f"Вы можете выбрать отслеживание из предыдущих, затем его отредактировать. "
        f"Или создать новое отслеживание, нажав на кнопку внизу сообщения. "
        f"<b>Вот список предыдущих отслеживаний</b>:\n\n"
        f"<i>ℹ️ для того, чтобы скопировать предыдущее отслеживание, нажмите на подзаголовок</i>\n"
    )

    # Сюда добавляем трекинги в формате (from_city_id, to_city_id, max_price
    added_trackings = set()

    for tracking in user_trackings:
        current_tracking_tuple = (tracking.from_city_id, tracking.to_city_id, tracking.max_price)

        # Если этот маршрут уже выводили в списке предыдущих маршрутов
        if current_tracking_tuple in added_trackings:
            continue

        added_trackings.add(current_tracking_tuple)

        text += (
            '\n'
            f'<a href="https://t.me/{config.tg_bot.username}?start=tracking_copy_{tracking.id}">'
            f'💾 Отслеживание от {tracking.created_at.strftime("%d.%m.%Y")}: </a>\n'
            f'<b>Откуда:</b> {tracking.from_city_name}\n'
            f'<b>Куда:</b> {tracking.to_city_name}\n'
        )
        if tracking.max_price:
            text += '<b>Цена до:</b> {:.2f}₽\n'.format(tracking.max_price)

        if len(added_trackings) == 4:
            break

    sent_message = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode='HTML',
        reply_markup=start_create_tracking_from_scratch_kb(),
        disable_web_page_preview=True
    )

    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )


@router.message(Command('start'), StartArgsFilter(finding_startswith='tracking_copy_'))
async def new_tracking_from_other(
        message: Message,
        command: CommandObject,
        current_user: UserModel,
        state: FSMContext,
        config: Config,
        session: AsyncSession
):
    await state.set_state(None)

    tracking_id = int(command.args.split('_')[-1])

    tracking_manager = TrackingManager(session=session)
    tracking = await tracking_manager.get(obj_id=tracking_id)

    tracking_data = {
        'from_city_name': tracking.from_city_name,
        'from_city_id': tracking.from_city_id,
        'from_city_site_code': tracking.from_city_site_code,
        'to_city_name': tracking.to_city_name,
        'to_city_id': tracking.to_city_id,
        'to_city_site_code': tracking.to_city_site_code,
        'date': None,
        'max_price': float(tracking.max_price) if tracking.max_price else None,

        'sw_enabled': tracking.sw_enabled,
        'sid_enabled': tracking.sid_enabled,

        'plaz_seats_plaz_down_enabled': tracking.plaz_seats_plaz_down_enabled,
        'plaz_seats_plaz_up_enabled': tracking.plaz_seats_plaz_up_enabled,
        'plaz_side_down_enabled': tracking.plaz_side_down_enabled,
        'plaz_side_up_enabled': tracking.plaz_side_up_enabled,
        'cupe_up_enabled': tracking.cupe_up_enabled,
        'cupe_down_enabled': tracking.cupe_down_enabled,

        'not_saved_flag': True
    }

    state_data = await state.get_data()
    state_data['tracking_data'] = tracking_data
    await state.set_data(state_data)

    sent_message = await send_tracking_menu(
        user=message.from_user,
        bot=message.bot,
        tracking_data=tracking_data
    )

    await add_messages_in_state_to_delete(
        query=message,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )


def _get_current_stage_text(current_stage: int):
    return (
        f'———\n'
        f'<i>Шаг {current_stage} из {len(CreatingTracking.__states__)}</i>'
    )


@router.callback_query(F.data == 'create_tracking', AtLeastOneTrackingExistsFilter(check_for_lack=True))
@router.callback_query(F.data == 'create_tracking_from_scratch')
async def start_create_tracking_from_scratch(
        callback: CallbackQuery,
        state: FSMContext
):
    text = (
        f'<b>Введите город</b>, откуда будет отправляться поезд\n'
        f'{_get_current_stage_text(1)}'
    )
    sent_message = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode='HTML'
    )

    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )

    await state.set_state(CreatingTracking.city_from)
    # Заносим данные для отслеживания. Далее будем обновлять
    await state.update_data({
        'tracking_data': {
            'from_city_name': None,
            'from_city_id': None,
            'from_city_site_code': None,

            'to_city_name': None,
            'to_city_id': None,
            'to_city_site_code': None,

            'date': None,
            'max_price': None,

            'sw_enabled': True,
            'sid_enabled': True,

            'plaz_seats_plaz_down_enabled': True,
            'plaz_seats_plaz_up_enabled': True,
            'plaz_side_down_enabled': True,
            'plaz_side_up_enabled': True,
            'cupe_up_enabled': True,
            'cupe_down_enabled': True,

            'not_saved_flag': True
        }
    })


@router.message(F.text, StateFilter(CreatingTracking.city_from, CreatingTracking.city_to))
async def handle_city(
        message: Message,
        state: FSMContext,
        rzd_parser: RZDParser
):
    current_state = await state.get_state()
    if current_state == CreatingTracking.city_from:
        current_stage_number = 1
    else:
        current_stage_number = 2

    # ищем указанный город
    cities = await rzd_parser.get_cities_by_query(message.text)
    # если не нашли, то просим ввести снова
    if len(cities) == 0:
        city_type_text = 'отправления' if current_state == CreatingTracking.city_from else 'прибытия'
        text = (
            f'Мы не смогли распознать город {city_type_text} :(\n\n'
            f'Пожалуйста, попробуйте указать его снова, используя его <b>полное название</b>\n'
            f'{_get_current_stage_text(current_stage_number)}'
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

    if current_state == CreatingTracking.city_from:
        text = (
            f'Отлично, мы получили город, откуда будет отправляться поезд\n'
            f'\n'
            f'Теперь введите <b>город прибытия</b>\n'
            f'{_get_current_stage_text(2)}'
        )
        tracking_data.update({
            'from_city_name': selected_city.name,
            'from_city_id': selected_city.station_code,
            'from_city_site_code': selected_city.site_code
        })
    else:
        text = (
            f'Отлично, мы получили город прибытия\n'
            f'\n'
            f'Сейчас укажите <b>дату, на которую необходимо отслеживание (дату отправления поезда)</b>\n\n'
            f'Формат: ДД.ММ.ГГГГ или ДД.ММ\n'
            f'Пример: {datetime.datetime.utcnow().strftime("%d.%m.%Y")}\n'
            f'{_get_current_stage_text(3)}'
        )
        tracking_data.update({
            'to_city_name': selected_city.name,
            'to_city_id': selected_city.station_code,
            'to_city_site_code': selected_city.site_code
        })

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

    if current_state == CreatingTracking.city_from:
        await state.set_state(CreatingTracking.city_to)
    else:
        await state.set_state(CreatingTracking.date)

    await state.update_data({'tracking_data': tracking_data})


@router.message(F.text, StateFilter(CreatingTracking.date))
async def handle_date(
        message: Message,
        state: FSMContext,
):
    error_text_ending = (
        f'\n'
        f'Формат: ДД.ММ.ГГГГ или ДД.ММ\n'
        f'Пример: {datetime.datetime.utcnow().strftime("%d.%m.%Y")}\n'
        f'{_get_current_stage_text(3)}'
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

    text = (
        'Дата успешно принята!\n\n'
        'Теперь введите <b>максимальную цену, за которую готовы купить билет.</b> '
        'Вы можете пропустить этот этап, нажав на кнопку ниже\n'
        f'{_get_current_stage_text(4)}'
    )

    sent_message = await message.bot.send_message(
        chat_id=message.from_user.id,
        text=text,
        parse_mode='HTML',
        reply_markup=skip_max_price_kb()
    )
    await add_messages_in_state_to_delete(
        query=message,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )

    tracking_data: dict = (await state.get_data())['tracking_data']
    tracking_data.update({
        'date': date.date().isoformat()
    })
    await state.set_state(CreatingTracking.max_price)
    await state.update_data({'tracking_data': tracking_data})


@router.callback_query(F.data == 'creating_tracking_skip_max_price')
@router.message(F.text, StateFilter(CreatingTracking.max_price))
async def handle_max_price(
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
                f'{_get_current_stage_text(4)}'
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
