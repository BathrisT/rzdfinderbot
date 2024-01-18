from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio.session import AsyncSession

from config import Config
from cruds.trackings import TrackingManager
from keyboards.trackings import start_create_ticket_from_scratch
from models.users import UserModel
from utils.add_messages_in_state_to_delete import add_messages_in_state_to_delete

# TODO: повесить фильтр, что чел оплатил подписку
router = Router()


# TODO: фильтр на то, что у юзера есть хотя бы одно отслеживание в бд
@router.callback_query(F.data == 'create_tracking')
async def start_create_tracking(
        callback: CallbackQuery,
        current_user: UserModel,
        state: FSMContext,
        config: Config,
        session: AsyncSession
):
    tracking_manager = TrackingManager(session=session)
    user_trackings = await tracking_manager.get_user_trackings(user_id=callback.from_user.id, only_active=False)

    #  TODO: проверка на количество уже созданных отслеживаний. Если уже больше 10, то нельзя

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
            text += f'<b>Цена до:</b> {tracking.max_price}₽\n'

        if len(added_trackings) == 4:
            break

    sent_message = await callback.bot.send_message(
        chat_id=callback.from_user.id,
        text=text,
        parse_mode='HTML',
        reply_markup=start_create_ticket_from_scratch(),
        disable_web_page_preview=True
    )

    await add_messages_in_state_to_delete(
        query=callback,
        state=state,
        messages=[sent_message],
        delete_prev_messages=True
    )
