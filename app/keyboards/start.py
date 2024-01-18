from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard_without_subscription() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить подписку', callback_data='create_invoice')],
        [
            InlineKeyboardButton(text='🗂 Отзывы', url='https://t.me/folkross'), # TODO: ссылки брать из конфига
            InlineKeyboardButton(text='📗 Канал', url='https://t.me/folkross')   # TODO: ссылки брать из конфига
        ],
        [InlineKeyboardButton(text='🧑‍💻 Поддержка', url='https://t.me/folkross')]   # TODO: ссылки брать из конфига
    ])

def start_keyboard_with_subscription() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⏱ Текущие отслеживания', callback_data='tracking_list')],
        [InlineKeyboardButton(text='➕ Новое отслеживание', callback_data='create_tracking')],
    ])

def return_to_start_keyboard(text='🔙 В главное меню'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=text, callback_data='start')],
    ])
