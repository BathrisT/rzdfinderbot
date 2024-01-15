import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.redis import RedisStorage, Redis

from config import get_config
from handlers.start import router as start_router
from handlers.invoices import router as invoices_router
from middlewares.user_middleware import UserMiddleware

logger = logging.getLogger(__name__)


def setup_middlewares(dp: Dispatcher):
    dp.message.register(UserMiddleware())
    dp.callback_query.register(UserMiddleware())


def setup_routers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(invoices_router)


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

    setup_middlewares(dp)
    setup_routers(dp)

    await dp.start_polling(bot, config=config)


if __name__ == '__main__':
    asyncio.run(main())
