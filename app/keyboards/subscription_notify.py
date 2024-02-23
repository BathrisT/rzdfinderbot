from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def subscription_notify_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить подписку', callback_data='create_invoice')],
        [InlineKeyboardButton(text='🔙 В главное меню', callback_data='start')],
    ])
