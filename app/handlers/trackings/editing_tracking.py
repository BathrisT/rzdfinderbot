import datetime
from typing import Union

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, User
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StateFilter
from sqlalchemy.ext.asyncio.session import AsyncSession

from config import Config
from cruds.trackings import TrackingManager
from keyboards.trackings import start_create_tracking_from_scratch_kb, skip_max_price_kb, edit_tracking_kb
from models.users import UserModel
from states.creating_tracking import CreatingTracking
from utils.add_messages_in_state_to_delete import add_messages_in_state_to_delete
from utils.rzd_parser import RZDParser

# TODO: повесить фильтр, что чел оплатил подписку
router = Router()

async def send_tracking_menu(user: User, bot: Bot, tracking_data: dict) -> Message:
    """
    tracking_data должна выглядеть так:

    {'from_city_name': 'Киров', 'from_city_id': '2060600', 'to_city_name': 'Москва', 'to_city_id': '2000000',
    'date': '2024-02-28', 'max_price': 1300.0}

    или

    {'from_city_name': 'Киров', 'from_city_id': '2060600', 'to_city_name': 'Москва', 'to_city_id': '2000000',
    'date': '2024-02-28', 'max_price': None, 'tracking_id': 12}
    """

    tracking_id = tracking_data.get('tracking_id')

    from_city_name = tracking_data['from_city_name']
    from_city_id = tracking_data['from_city_id']

    to_city_name = tracking_data['to_city_name']
    to_city_id = tracking_data['to_city_id']

    date = datetime.date.fromisoformat(tracking_data['date'])
    max_price = tracking_data['max_price']

    text = '📗 Новое отслеживание:\n\n'
    if tracking_id is not None:
        text = f'📗 Отслеживание #{tracking_id}:\n\n'

    text += (
        '✏️ Вы можете <b>отредактировать отслеживание</b> нажав на одну из соответствующих кнопок ниже.\n'
        'Когда вы придете к финальной версии, необходимо <b>нажать на кнопку "Сохранить"</b>\n\n'
    )

    text += (
        f'<b>Откуда:</b> {from_city_name}\n'
        f'<b>Куда:</b> {to_city_name}\n'
        f'<b>Дата отправления:</b> {date.strftime("%d.%m.%Y")}\n'
    )
    if max_price is not None:
        text += f'<b>Цена до:</b> {max_price}₽'

    return await bot.send_message(
        chat_id=user.id,
        text=text,
        parse_mode='HTML',
        reply_markup=edit_tracking_kb(),
        disable_web_page_preview=True
    )
