from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard_without_subscription() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить подписку', callback_data='create_invoice')],
        [
            InlineKeyboardButton(text='🗂 Отзывы', url='https://t.me/folkross'),
            InlineKeyboardButton(text='📗 Канал', url='https://t.me/folkross')
        ],
        [InlineKeyboardButton(text='🧑‍💻 Поддержка', url='https://t.me/folkross')]
    ])


def return_to_start_keyboard(text='🔙 В главное меню'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data='start')],
    ])
