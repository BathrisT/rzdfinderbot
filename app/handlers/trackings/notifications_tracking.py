import aiogram.exceptions
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio.session import AsyncSession

from cruds.trackings import TrackingManager
from keyboards.start import return_to_start_keyboard
from models.users import UserModel
from schemas.trackings import TrackingUpdateSchema
from utils.add_messages_in_state_to_delete import add_messages_in_state_to_delete


router = Router()

@router.callback_query(F.data.startswith('failed_notification_'))
@router.callback_query(F.data.startswith('success_notification_'))
async def on_click_success_notification_button(
        callback: CallbackQuery,
        current_user: UserModel,
        state: FSMContext,
        session: AsyncSession
):
    await callback.answer()
    tracking_manager = TrackingManager(session=session)
    tracking_id = int(callback.data.split('_')[-1])
    tracking = await tracking_manager.get(obj_id=tracking_id)
    if not tracking or tracking.is_finished or tracking.user_id != current_user.id:
        text = '❌ Отслеживание не найдено. Возможно оно уже завершено'
        sent_message = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            parse_mode='HTML',
            reply_markup=return_to_start_keyboard(),
            reply_to_message_id=callback.message.message_id
        )
        await add_messages_in_state_to_delete(
            query=callback,
            state=state,
            messages=[sent_message],
            delete_prev_messages=True
        )
        return

    await tracking_manager.clear_first_notification_date(tracking_id=tracking_id)
    if callback.data.startswith('success_notification_'):
        await tracking_manager.update(obj_id=tracking_id, obj_in=TrackingUpdateSchema(is_finished=True))
        text = (
            f'<b>💫 Отслеживание #{tracking_id} помечено как успешное</b>\n\n'
            'Мы рады что помогли вам взять билет. Спасибо за пользование сервисом!'
        )
    else:
        text = (
            f'<b>📗 Отслеживание #{tracking_id} оставлено активным</b>\n\n'
            '<b>ℹ️ Совет:</b> чтобы успеть взять билет, включите оповещения в боте и действуйте быстро'
        )
    await session.commit()

    try:
        await callback.message.edit_text(
            text=callback.message.html_text.split('------')[0] + '------\n' + text,
            parse_mode='HTML',
            reply_markup=return_to_start_keyboard()
        )
    except Exception:
        sent_message = await callback.bot.send_message(
            chat_id=callback.from_user.id,
            text=text,
            parse_mode='HTML',
            reply_markup=return_to_start_keyboard(),
            reply_to_message_id=callback.message.message_id
        )
        await add_messages_in_state_to_delete(
            query=callback,
            state=state,
            messages=[sent_message],
            delete_prev_messages=True
        )
