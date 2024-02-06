import datetime
from typing import Union

from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types.callback_query import CallbackQuery
from aiogram.types.message import Message
from sqlalchemy.ext.asyncio.session import AsyncSession

from config import Config
from cruds.trackings import TrackingManager
from filters.start_args_filter import StartArgsFilter
from filters.subscription_filter import SubscriptionFilter

from keyboards.start import start_keyboard_without_subscription, start_keyboard_with_subscription
from models.users import UserModel
from utils.add_messages_in_state_to_delete import add_messages_in_state_to_delete

router = Router()


@router.callback_query(F.data == 'start', SubscriptionFilter(checking_for_lack=True))
@router.message(Command('start'), StartArgsFilter(finding_startswith=None), SubscriptionFilter(checking_for_lack=True))
async def start_without_subscription(
        query: Union[Message, CallbackQuery],
        state: FSMContext,
        config: Config
):
    await state.set_state(None)

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
        reply_markup=start_keyboard_without_subscription(
            reviews_link=config.links.reviews_link,
            channel_link=config.links.channel_link,
            support_link=config.links.support_link,
        ),
        disable_web_page_preview=True
    )
    await add_messages_in_state_to_delete(
        query=query,
        state=state,
        messages=[sent_message]
    )

# TODO: сделать хендлер, если у юзера есть неотмеченные нотификации,
#  то отправляем информацию о них и об обязательности отметок
@router.callback_query(F.data == 'start', SubscriptionFilter(checking_for_lack=False))
@router.message(Command('start'), StartArgsFilter(finding_startswith=None), SubscriptionFilter(checking_for_lack=False))
async def start_with_subscription(
        query: Union[Message, CallbackQuery],
        current_user: UserModel,
        state: FSMContext,
        session: AsyncSession,
        config: Config
):
    await state.set_state(None)

    tracking_manager = TrackingManager(session=session)
    user_trackings = await tracking_manager.get_user_trackings(user_id=current_user.id, only_active=True)
    text = (
f'''
🚅 Вы находитесь в главном меню бота по поиску/отслеживанию билетов РЖД

<b>💫 Этот бот поможет вам купить билеты на маршруты, где всё уже раскуплено. Как это устроено:</b>

1. <b>Вы создаете заявку</b>, в которой указываете маршрут поезда, дату и максимальную цену
2. <b>Мы сразу же обрабатываем эту заявку.</b> После этого бот будет автоматически присылать вам оповещения о появлении только что сданных (или новых) билетов на поезда по вашей заявке
3. <b>Вам приходит оповещение.</b> Теперь ваша задача как можно быстрее перейти по ссылке и купить появившееся место

🗂 <b>Текущие активные отслеживания:</b> {len(user_trackings)} шт
🎫 <b>Подписка оплачена до:</b> {current_user.subscription_expires_at.strftime('%d.%m.%Y %H:%M')}

<a href='{config.links.reviews_link}'>Отзывы</a> | <a href='{config.links.channel_link}'>Канал</a> | <a href='{config.links.support_link}'>Поддержка</a>
'''
    )
    sent_message = await query.bot.send_message(
        chat_id=query.from_user.id,
        text=text,
        parse_mode='HTML',
        reply_markup=start_keyboard_with_subscription(),
        disable_web_page_preview=True
    )
    await add_messages_in_state_to_delete(
        query=query,
        state=state,
        messages=[sent_message]
    )
