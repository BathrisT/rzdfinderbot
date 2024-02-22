import traceback

from loguru import logger
from aiogram.types import Update


async def common_exception_handler(update: Update):
    logger.error(
        'Произошла неизвестная ошибка в боте:\n'
        f'{traceback.format_exc()}'
    )
