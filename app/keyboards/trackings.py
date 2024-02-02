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

def edit_tracking_kb(is_new_tracking: bool, return_callback_data: str = 'start'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📌 Откуда', callback_data='tracking_edit_from_city'),
            InlineKeyboardButton(text='🎯 Куда', callback_data='tracking_edit_to_city'),
        ], [
            InlineKeyboardButton(text='📆 Дата', callback_data='tracking_edit_date'),
            InlineKeyboardButton(text='💳 Цена до', callback_data='tracking_edit_max_price'),
        ],
        [InlineKeyboardButton(
            text='💾 Сохранить',
            callback_data='save_tracking'
        )],
        [InlineKeyboardButton(text='🔙 Отмена', callback_data=return_callback_data)]
    ])

def back_to_tracking_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 Вернуться к отслеживанию', callback_data='edit_tracking')],
    ])

def edit_max_price_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Не указывать (обнулить)', callback_data='set_null_edit_max_price')],
        [InlineKeyboardButton(text='🔙 Вернуться к отслеживанию', callback_data='edit_tracking')],
    ])

def active_trackings_not_found_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➕ Новое отслеживание', callback_data='create_tracking')],
        [InlineKeyboardButton(text='🔙 Вернуться в меню', callback_data='start')]
    ])

def get_ending_kb_elements_for_tracking_list():
    return [
        [InlineKeyboardButton(text='➕ Новое отслеживание', callback_data='create_tracking')],
        [InlineKeyboardButton(text='🔙 Вернуться в меню', callback_data='start')]
    ]