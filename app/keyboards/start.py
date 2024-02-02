from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_keyboard_without_subscription(
        reviews_link: str,
        channel_link: str,
        support_link: str
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить подписку', callback_data='create_invoice')],
        [
            InlineKeyboardButton(text='🗂 Отзывы', url=reviews_link),
            InlineKeyboardButton(text='📗 Канал', url=channel_link)
        ],
        [InlineKeyboardButton(text='🧑‍💻 Поддержка', url=support_link)]
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
