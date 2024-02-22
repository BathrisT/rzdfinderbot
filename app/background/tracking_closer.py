import asyncio
import datetime
import traceback

from loguru import logger
from aiogram import Bot

from cruds.trackings import TrackingManager
from database import async_session_maker
from models.trackings import TrackingModel
from schemas.trackings import TrackingUpdateSchema

# TODO: проверить
class TrackingCloser:
    def __init__(self, aiogram_bot_token: str, tg_bot_username: str):
        self._aiogram_bot = Bot(token=aiogram_bot_token)
        self._tg_bot_username = tg_bot_username

    @staticmethod
    async def close_tracking(tracking_id: int):
        async with async_session_maker() as session:
            tracking_manager = TrackingManager(session=session)
            await tracking_manager.update(
                obj_id=tracking_id,
                obj_in=TrackingUpdateSchema(
                    is_finished=True,
                    finished_at=datetime.datetime.utcnow()
                )
            )
            await session.commit()

    async def send_tracking_closed_notification(self, deleted_tracking: TrackingModel, user_id: int):
        text = (
            f'<b>📕 Отслеживание #{deleted_tracking.id}</b> было отключено\n\n'
            f'<b>ℹ️ Информация об отслеживании:</b>\n'
            f'Откуда: {deleted_tracking.from_city_name}\n'
            f'Куда: {deleted_tracking.to_city_name}\n'
            f'Дата: {deleted_tracking.date.strftime("%d.%m.%Y")}\n\n'
            f'Вы можете <a href="https://t.me/{self._tg_bot_username}?start=tracking_copy_{deleted_tracking.id}">'
            f'повторно создать отслеживание с теми же данными'
            f'</a>'
        )
        try:
            await self._aiogram_bot.send_message(
                text=text,
                chat_id=user_id,
                disable_web_page_preview=True,
                parse_mode='HTML'
            )
        except Exception:  # TODO: заменить на более частную обработку
            pass

    async def handle_tracking(self, tracking: TrackingModel):
        filters_without_notifications = [
            # проверка на бан юзера
            tracking.user.is_banned,
            # проверка на то, что у юзера никогда не было подписки (на всякий случай)
            tracking.user.subscription_expires_at is None,
            # проверка на то, что у юзера нет подписки уже больше 3 дней
            tracking.user.subscription_expires_at is not None and (
                    datetime.datetime.utcnow() > tracking.user.subscription_expires_at + datetime.timedelta(days=3)
            )
        ]
        filters_with_notifications = [
            # проверка на то что прошло больше дня с оповещения и юзер не нажал ни на одну из кнопок
            tracking.first_notification_sent_at is not None and (
                    datetime.datetime.utcnow() > tracking.first_notification_sent_at + datetime.timedelta(days=1)
            ),
        ]

        if any(filters_without_notifications + filters_with_notifications):
            logger.info(f'Tracking #{tracking.id} closed')
            await self.close_tracking(tracking_id=tracking.id)

        if any(filters_with_notifications):
            await self.send_tracking_closed_notification(deleted_tracking=tracking, user_id=tracking.user_id)

    async def cycle(self):
        # Получаем все отслеживания
        async with async_session_maker() as session:
            tracking_manager = TrackingManager(session=session)
            trackings = await tracking_manager.get_all_tracking(only_active=True)

        for tracking in trackings:
            try:
                await self.handle_tracking(tracking)
            except Exception:
                logger.error(f'Error while handle close tracking #{tracking.id}: \n'
                             f'{traceback.format_exc()}')

    async def start(self):
        logger.info('Background TrackingDBCloser started')

        while True:
            logger.debug('Завершен круг очереди удаления')
            try:
                await self.cycle()
            except Exception:
                logger.error(f'Global error in cycle of close trackings: \n'
                             f'{traceback.format_exc()}')
            await asyncio.sleep(60)
