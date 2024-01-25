from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_create_tracking_from_scratch_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Создать новое отслеживание', callback_data='create_tracking_from_scratch')],
        [InlineKeyboardButton(text='🔙 В главное меню', callback_data='start')]
    ])

def skip_max_price_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Не указывать', callback_data='creating_tracking_skip_max_price')],
    ])

def edit_tracking_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📌 Откуда', callback_data='tracking_edit_from_city'),
            InlineKeyboardButton(text='🎯 Куда', callback_data='tracking_edit_to_city'),
        ], [
            InlineKeyboardButton(text='📆 Дата', callback_data='tracking_edit_date'),
            InlineKeyboardButton(text='💳 Цена до', callback_data='tracking_edit_max_price'),
        ],
        [InlineKeyboardButton(text='💾 Сохранить', callback_data='save_tracking')],
        [InlineKeyboardButton(text='🔙 Отмена', callback_data='start')]
    ])
