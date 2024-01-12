from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def create_invoice_keyboard(invoice_link: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Заплатить 100,00 RUB', url=invoice_link, pay=True)],
        [InlineKeyboardButton(text='🔙 В главное меню', callback_data='start')]
    ])
