from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def go_to_current_trackings_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='⏱ Текущие отслеживания', callback_data='tracking_list')],
        [InlineKeyboardButton(text='🔙 В главное меню', callback_data='start')]
    ])

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
    save_row = [InlineKeyboardButton(
            text='💾 Сохранить',
            callback_data='save_tracking'
    )]

    if not is_new_tracking:
        save_row.append(
            InlineKeyboardButton(
                text='❌ Удалить',
                callback_data='finish_tracking'
            )
        )

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📌 Откуда', callback_data='tracking_edit_from_city'),
            InlineKeyboardButton(text='🎯 Куда', callback_data='tracking_edit_to_city'),
        ], [
            InlineKeyboardButton(text='📆 Дата', callback_data='tracking_edit_date'),
            InlineKeyboardButton(text='💳 Цена до', callback_data='tracking_edit_max_price'),
        ],
        save_row,
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

def seats_found_kb(rzd_url: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='▶️ Перейти на сайт РЖД', url=rzd_url)],
        [InlineKeyboardButton(text='🔙 Вернуться к отслеживанию', callback_data='edit_tracking')],
        [InlineKeyboardButton(text='🔙 Вернуться в меню', callback_data='start')]
    ])

def found_seats_notification_kb(
        tracking_id: int
):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🟢 Я успел взять билет', callback_data=f'success_notification_{tracking_id}')],
        [InlineKeyboardButton(text='🔴 Я не смог взять билет', callback_data=f'failed_notification_{tracking_id}')]
    ])
