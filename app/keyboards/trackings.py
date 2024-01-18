from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_create_ticket_from_scratch():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Создать новое отслеживание', callback_data='create_ticket_from_scratch')],
        [InlineKeyboardButton(text='🔙 В главное меню', callback_data='start')]
    ])
