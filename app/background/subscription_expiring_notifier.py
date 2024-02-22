import asyncio
import datetime
import traceback
from typing import Literal

from loguru import logger
from aiogram import Bot

from cruds.users import UserManager
from database import async_session_maker
from models.users import UserModel
from schemas.users import UserUpdateSchema


# TODO: проверить
class SubscriptionExpiringNotifier:
    def __init__(self, aiogram_bot_token: str, tg_bot_username: str):
        self._aiogram_bot = Bot(token=aiogram_bot_token)
        self._tg_bot_username = tg_bot_username

    async def send_notification(self, notification_type: Literal['3d', '1d', 'after'], user: UserModel):
        text: str = None
        if notification_type == '3d':
            text = (
                'ℹ️ Через <b>3 дня</b> у вас закончится подписка\n\n'
                'Вы можете продлить её сейчас, чтобы сохранить все ваши отслеживания'
            )
        elif notification_type == '1d':
            text = (
                '❗️Через <b>1 день</b> у вас закончится подписка\n\n'
                'Продлите её сейчас, чтобы сохранить все ваши отслеживания'
            )
        elif notification_type == 'after':
            text = (
                '📕 <b>Подписка на сервис закончилась.</b> Через <b>2 дня</b> мы завершим ваши активные отслеживания.\n'
                '💫 Чтобы <b>вернуть доступ к возможностям бота</b>, необходимо продлите подписку.\n\n'
                '<b>Спасибо за пользование сервисом</b>'
            )
        try:
            await self._aiogram_bot.send_message(
                text=text,
                chat_id=user.id,
                disable_web_page_preview=True,
                parse_mode='HTML'
            )
        except Exception:  # TODO: заменить на более частную обработку
            pass

    async def handle_user(self, user: UserModel):
        notification_for_3_days_flag = (
                (
                        (datetime.datetime.utcnow() - datetime.timedelta(days=2))
                        > user.subscription_expires_at >
                        (datetime.datetime.utcnow() - datetime.timedelta(days=3))
                ) and (
                        user.last_expire_notification_sent_at is None
                        or
                        user.last_expire_notification_sent_at < (
                                datetime.datetime.utcnow() - datetime.timedelta(days=1))
                )
        )
        notification_for_1_day_flag = (
                (
                        (datetime.datetime.utcnow() - datetime.timedelta(hours=24))
                        > user.subscription_expires_at >
                        (datetime.datetime.utcnow() - datetime.timedelta(hours=23))
                ) and (
                        user.last_expire_notification_sent_at is None
                        or
                        user.last_expire_notification_sent_at < (
                                    datetime.datetime.utcnow() - datetime.timedelta(hours=2))
                )
        )
        notification_after_expired_subscription_flag = (
                (
                        user.subscription_expires_at < (datetime.datetime.utcnow() - datetime.timedelta(hours=1))
                ) and (
                        user.last_expire_notification_sent_at is None
                        or
                        user.last_expire_notification_sent_at < (
                                datetime.datetime.utcnow() - datetime.timedelta(hours=2))
                )
        )
        if notification_for_3_days_flag:
            await self.send_notification(notification_type='3d', user=user)
        if notification_for_1_day_flag:
            await self.send_notification(notification_type='1d', user=user)
        if notification_after_expired_subscription_flag:
            await self.send_notification(notification_type='after', user=user)

        if any([notification_for_3_days_flag, notification_for_1_day_flag,
                notification_after_expired_subscription_flag]):
            async with async_session_maker() as session:
                user_manager = UserManager(session=session)
                await user_manager.update(
                    obj_id=user.id,
                    obj_in=UserUpdateSchema(last_expire_notification_sent_at=datetime.datetime.utcnow())
                )
                await session.commit()

    async def cycle(self):
        # Получаем всех юзеров
        async with async_session_maker() as session:
            user_manager = UserManager(session=session)
            users = await user_manager.get_multi(limit=10000000)

        for user in users:
            try:
                await self.handle_user(user)
            except Exception:
                logger.error(f'Error in subscription_expiring_notifier #{user.id}: \n'
                             f'{traceback.format_exc()}')

    async def start(self):
        logger.info('Background SubscriptionExpiringNotifier started')

        while True:
            logger.debug('Завершен круг отправки нотификаций об окончании подписки')
            try:
                await self.cycle()
            except Exception:
                logger.error(f'Global error in cycle of SubscriptionExpiringNotifier: \n'
                             f'{traceback.format_exc()}')
            await asyncio.sleep(20)
