import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage, Redis

from config import get_config
from handlers.start import router as start_router
from handlers.invoices import router as invoices_router
from handlers.trackings import router as trackings_router
from utils.paginator.paginator import router as paginator_router
from middlewares.session_middleware import SQLAlchemySessionMiddleware
from middlewares.user_middleware import UserMiddleware
from utils.rzd_parser import RZDParser

logger = logging.getLogger(__name__)


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


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format=u'%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger.info("Starting bot")

    config = get_config()

    storage = RedisStorage(
        redis=Redis(host=config.redis.host, port=config.redis.port, db=5, password=config.redis.password)
    )
    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(storage=storage)

    # TODO: # Добавить мидлварь ржд парсера
    rzd_parser = RZDParser()

    setup_middlewares(dp)
    setup_routers(dp)

    try:
        await dp.start_polling(bot, config=config, rzd_parser=rzd_parser)
    finally:
        await rzd_parser.close_session()


if __name__ == '__main__':
    asyncio.run(main())
