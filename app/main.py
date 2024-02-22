import asyncio

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage, Redis
from loguru import logger

from logger_handlers.telegram_handler import TelegramBotHandler
from config import get_config
from exception_handlers.common_exception_handler import common_exception_handler
from handlers.invoices import router as invoices_router
from handlers.start import router as start_router
from handlers.trackings import router as trackings_router
from middlewares.session_middleware import SQLAlchemySessionMiddleware
from middlewares.user_middleware import UserMiddleware
from utils.paginator.paginator import router as paginator_router
from utils.rzd_parser import RZDParser


def setup_middlewares(dp: Dispatcher):
    # Мидлварь которая проверяет блокировку юзера и добавляет его в контекст
    dp.message.outer_middleware.register(UserMiddleware())
    dp.callback_query.outer_middleware.register(UserMiddleware())
    # Мидлварь которая добавляет сессию бд в контекст
    dp.message.middleware.register(SQLAlchemySessionMiddleware())
    dp.callback_query.middleware.register(SQLAlchemySessionMiddleware())
    # TODO: # Добавить мидлварь ржд парсера


def setup_routers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(paginator_router)

    dp.include_router(invoices_router)
    dp.include_router(trackings_router)

def setup_error_handlers(dp: Dispatcher):
    dp.errors.register(common_exception_handler)

async def main():
    config = get_config()

    # setup logger
    logger_tg_handler = TelegramBotHandler(
        bot_token=config.service_notifications.bot_token,
        chat_id=config.service_notifications.chat_id,
        project_name=config.service_notifications.project_name
    )
    logger.add(logger_tg_handler.notify, level='ERROR')
    logger.info('Starting bot')

    storage = RedisStorage(
        redis=Redis(host=config.redis.host, port=config.redis.port, db=5, password=config.redis.password)
    )
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(storage=storage)

    # TODO: # Добавить мидлварь ржд парсера
    rzd_parser = RZDParser()

    setup_middlewares(dp)
    setup_routers(dp)
    setup_error_handlers(dp)

    try:
        await dp.start_polling(bot, config=config, rzd_parser=rzd_parser)
    finally:
        await rzd_parser.close_session()
        await logger.complete()


if __name__ == '__main__':
    asyncio.run(main())
