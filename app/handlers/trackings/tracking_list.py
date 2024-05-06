from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio.session import AsyncSession

from config import Config
from cruds.trackings import TrackingManager
from filters.start_args_filter import StartArgsFilter
from handlers.trackings.editing_tracking import send_tracking_menu
from keyboards.trackings import active_trackings_not_found_kb, get_ending_kb_elements_for_tracking_list
from models.trackings import TrackingModel
from utils.add_messages_in_state_to_delete import add_messages_in_state_to_delete
from utils.paginator.paginator import Paginator


router = Router()

def get_row_text_from_tracking_object(tracking: TrackingModel, index: int, tg_bot_username: str):
    text = (
        '\n'
        f'<a href="https://t.me/{tg_bot_username}?start=tracking_open_{tracking.id}">'
        f'🚅 Отслеживание #{tracking.id} на {tracking.date.strftime("%d.%m.%Y")}: </a>\n'
        f'<b>Откуда:</b> {tracking.from_city_name}\n'
        f'<b>Куда:</b> {tracking.to_city_name}'
    )
    if tracking.max_price:
        text += '\n<b>Цена до:</b> {:.2f}₽'.format(tracking.max_price)
    return text


@router.callback_query(F.data == 'tracking_list')
async def tracking_list(
        callback: CallbackQuery,
        state: FSMContext,
        session: AsyncSession,
        config: Config
):
    tracking_manager = TrackingManager(session=session)
    user_trackings = await tracking_manager.get_user_trackings(user_id=callback.from_user.id, only_active=True)

    # если нет активных отслеживаний
    if len(user_trackings) == 0:
        text = '❌ У вас нет ни одного активного отслеживания. <b>Создайте новое, нажав на кнопку ниже</b>'
        sent_message = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            parse_mode='HTML',
            reply_markup=active_trackings_not_found_kb(),
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
        f"Вот список ваших <b>активных отслеживаний</b>:\n\n"
        f"<i>ℹ️ для того, чтобы открыть полную информацию об отслеживании, нажмите на подзаголовок</i>\n"
        "{rows_text}\n"
        "<i>Страница {page_number} из {pages_count}</i>"
    )

    paginator = Paginator(
        objects=user_trackings,
        get_row_text_from_object_func=lambda obj, i: get_row_text_from_tracking_object(obj, i, config.tg_bot.username),
        formatted_text_for_page=text,
        page_size=3,
        parse_mode='HTML',
        ending_kb_elements=get_ending_kb_elements_for_tracking_list()
    )

    sent_message = await paginator.send_message(
        chat_id=callback.from_user.id,
        bot_instance=callback.bot
    )

    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )


@router.message(Command('start'), StartArgsFilter(finding_startswith='tracking_open_'))
async def open_specific_tracking(
        message: Message,
        state: FSMContext,
        session: AsyncSession
):
    tracking_id = int(message.text.split('tracking_open_')[-1])
    tracking_manager = TrackingManager(session=session)
    tracking = await tracking_manager.get(obj_id=tracking_id)
    if tracking.user_id != message.from_user.id:
        return

    tracking_data = {
        'tracking_id': tracking_id,
        'from_city_name': tracking.from_city_name,
        'from_city_id': tracking.from_city_id,
        'from_city_site_code': tracking.from_city_site_code,
        'to_city_name': tracking.to_city_name,
        'to_city_id': tracking.to_city_id,
        'to_city_site_code': tracking.to_city_site_code,
        'date': tracking.date.isoformat(),
        'max_price': float(tracking.max_price) if tracking.max_price is not None else None,

        'sw_enabled': tracking.sw_enabled,
        'sid_enabled': tracking.sid_enabled,

        'plaz_seats_plaz_down_enabled': tracking.plaz_seats_plaz_down_enabled,
        'plaz_seats_plaz_up_enabled': tracking.plaz_seats_plaz_up_enabled,
        'plaz_side_down_enabled': tracking.plaz_side_down_enabled,
        'plaz_side_up_enabled': tracking.plaz_side_up_enabled,
        'cupe_up_enabled': tracking.cupe_up_enabled,
        'cupe_down_enabled': tracking.cupe_down_enabled
    }

    state_data = await state.get_data()
    state_data['tracking_data'] = tracking_data
    await state.set_data(state_data)

    sent_message = await send_tracking_menu(
        user=message.from_user,
        bot=message.bot,
        tracking_data=tracking_data,
        return_callback_data='tracking_list'
    )

    await add_messages_in_state_to_delete(
        query=message,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )
