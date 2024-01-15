import datetime
from typing import Union

from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.message import Message
from filters.subscription_filter import SubscriptionFilter

from keyboards.start import start_keyboard_without_subscription
from models.users import UserModel
from utils.add_messages_in_state_to_delete import add_messages_in_state_to_delete

router = Router()


@router.callback_query(F.data == 'start', SubscriptionFilter(checking_for_lack=True))
@router.message(Command('start'), SubscriptionFilter(checking_for_lack=True))
async def start_without_subscription(query: Union[Message, CallbackQuery], state: FSMContext):
    text = (
'''
🚅 Приветствуем вас в боте по поиску/отслеживанию билетов РЖД

<b>💫 Этот бот поможет вам купить билеты на маршруты, где всё уже раскуплено. Как это устроено:</b>

1. <b>Вы создаете заявку</b>, в которой указываете маршрут поезда, дату и максимальную цену
2. <b>Мы сразу же обрабатываем эту заявку.</b> После этого бот будет автоматически присылать вам оповещения о появлении только что сданных (или новых) билетов на поезда по вашей заявке
3. <b>Вам приходит оповещение.</b> Теперь ваша задача как можно быстрее перейти по ссылке и купить появившееся место

Отслеживание работает по подписке в 100Р/месяц и станет доступно сразу после оплаты по кнопке ниже
'''
    )
    sent_message = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=text,
        parse_mode='HTML',
        reply_markup=start_keyboard_without_subscription(),
        disable_web_page_preview=True
    )
    await add_messages_in_state_to_delete(
        query=query,
        state=state,
        messages=[sent_message]
    )

@router.callback_query(F.data == 'start', SubscriptionFilter(checking_for_lack=False))
@router.message(Command('start'), SubscriptionFilter(checking_for_lack=False))
async def start_with_subscription(query: Union[Message, CallbackQuery], current_user: UserModel, state: FSMContext):
    text = (
        f'Ваша подписка оплачена до \n'
        f'{current_user.subscription_expires_at.isoformat()}'
    )

    sent_message = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=text,
        parse_mode='HTML',
        disable_web_page_preview=True
    )
    await add_messages_in_state_to_delete(
        query=query,
        state=state,
        messages=[sent_message]
    )
