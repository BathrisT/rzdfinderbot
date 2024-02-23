import asyncio
import sys

from background.subscription_expiring_notifier import SubscriptionExpiringNotifier
from loguru import logger

import models.users  # noqa
from logger_handlers.telegram_handler import TelegramBotHandler
from background.tracking_closer import TrackingCloser
from background.tracking_parser.tracking_parser import TrackingParser

from config import Config

async def main():
    loop = asyncio.get_event_loop()

    config = Config()
    # setup logger

    logger.remove()
    logger.add(sys.stdout, level="INFO")

    logger_tg_handler = TelegramBotHandler(
        bot_token=config.service_notifications.bot_token,
        chat_id=config.service_notifications.chat_id,
        project_name=config.service_notifications.project_name
    )
    logger.add(logger_tg_handler.notify, level='ERROR')

    config = Config()
    tracking_parser = TrackingParser(aiogram_bot_token=config.tg_bot.token, limit_of_parallel_handlers=5)
    tracking_closer = TrackingCloser(aiogram_bot_token=config.tg_bot.token, tg_bot_username=config.tg_bot.username)
    subscription_handler = SubscriptionExpiringNotifier(aiogram_bot_token=config.tg_bot.token)

    loop.create_task(tracking_closer.start())
    loop.create_task(tracking_parser.start())
    loop.create_task(subscription_handler.start())

    while True:
        await asyncio.sleep(1)


if __name__ == '__main__':
    asyncio.run(main())
