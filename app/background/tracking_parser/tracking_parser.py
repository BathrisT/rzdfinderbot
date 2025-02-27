import asyncio
import datetime
import traceback
from json import JSONDecodeError
from queue import Queue

import aiohttp
from aiogram import Bot
from loguru import logger

from cruds.tracking_notifications import TrackingNotificationManager
from cruds.trackings import TrackingManager
from database import async_session_maker
from keyboards.trackings import found_seats_notification_kb
from models.trackings import TrackingModel
from schemas.rzd_parser import Train
from schemas.tracking_notifications import TrackingNotificationCreateSchema
from schemas.trackings import TrackingUpdateSchema
from utils.filter_trains import filter_trains_by_tracking, check_min_price
from utils.rzd_links_generator import create_url_to_trains
from utils.rzd_parser import RZDParser
from .exceptions import TrackingFinishedException


class TrackingParser:
    def __init__(
            self,
            aiogram_bot_token: str,
            limit_of_parallel_handlers: int = 15,
    ):
        self._limit_of_parallel_handlers = limit_of_parallel_handlers
        self._current_parallel_handlers = 0
        self._aiogram_bot = Bot(token=aiogram_bot_token)

        self._last_connection_statuses: list[bool] = []
        self._length_of_last_connection_statuses = 10

    async def _get_tracking(
            self,
            queue_tracking_ids: Queue,
            mapping_id_to_tracking: dict[int, TrackingModel]
    ) -> TrackingModel:
        """Получение отслеживания из очереди для последующей обработки"""
        tracking_id: int = queue_tracking_ids.get(block=False)
        if tracking_id not in mapping_id_to_tracking:
            raise TrackingFinishedException(tracking_id=tracking_id)
        return mapping_id_to_tracking[tracking_id]

    async def _put_tracking(
            self,
            tracking: TrackingModel,
            queue_tracking_ids: Queue,
            mapping_id_to_tracking: dict[int, TrackingModel]
    ) -> None:
        """Занесение отслеживания в очередь после его обработки"""
        if tracking.id not in mapping_id_to_tracking:
            raise TrackingFinishedException(tracking_id=tracking.id)
        queue_tracking_ids.put(tracking.id)

    @staticmethod
    def _generate_notification_text_from_trains(tracking: TrackingModel, trains: list[Train]) -> str:
        text = f'<b>⚡️ Важно! Найдены подходящие билеты (#{tracking.id}) ⚡️</b>\n\n'
        for i, train in enumerate(trains):
            rzd_train_url = create_url_to_trains(
                from_city_site_code=tracking.from_city_site_code,
                to_city_site_code=tracking.to_city_site_code,
                date=tracking.date,
                train_number=train.train_number
            )
            train_text = (
                f'<a href="{rzd_train_url}">Поезд {train.train_number}{" (кликабельно)" if i == 0 else ""}:</a>\n'
                f'<b>📆 Дата:</b> {train.departure_date.strftime("%d.%m.%Y %H:%M")}\n'
                f'<b>📌 Откуда:</b> {train.from_city_name}\n'
                f'<b>🎯 Куда:</b> {train.to_city_name}\n'
            )
            prices_row = '💳 '
            available_filtered_seats = []
            if tracking.sw_enabled and train.sw_seats >= 1 and check_min_price(tracking.max_price, train.sw_min_price):
                available_filtered_seats.append(f'<b>СВ [{train.sw_seats}]</b> - {int(train.sw_min_price)}₽')
            if tracking.sid_enabled and train.sid_seats >= 1 and check_min_price(tracking.max_price, train.sid_min_price):
                available_filtered_seats.append(f'<b>Сид [{train.sid_seats}]</b> - {int(train.sid_min_price)}₽')

            s = tracking.cupe_up_enabled * train.cupe_up_seats + tracking.cupe_down_enabled * train.cupe_down_seats
            if any((tracking.cupe_up_enabled, tracking.cupe_down_enabled)) and s >= 1 and \
                    check_min_price(tracking.max_price, train.cupe_min_price):
                available_filtered_seats.append(f'<b>Купе [{s}]</b> - {int(train.cupe_min_price)}₽')

            s = (
                    tracking.plaz_seats_plaz_down_enabled * train.plaz_seats_plaz_down_seats +
                    tracking.plaz_seats_plaz_up_enabled * train.plaz_seats_plaz_up_seats +
                    tracking.plaz_side_down_enabled * train.plaz_side_down_seats +
                    tracking.plaz_side_up_enabled * train.plaz_side_up_seats
            )
            if any((tracking.plaz_seats_plaz_down_enabled, tracking.plaz_seats_plaz_up_enabled,
                    tracking.plaz_side_down_enabled, tracking.plaz_side_up_enabled)) and s >= 1 and \
                    check_min_price(tracking.max_price, train.plaz_min_price):
                available_filtered_seats.append(f'<b>Плац [{s}]</b> - {int(train.plaz_min_price)}₽')

            prices_row += ', '.join(available_filtered_seats)
            train_text += f'{prices_row}\n\n'
            text += train_text
        deactivate_tracking_time = (
                tracking.first_notification_sent_at + datetime.timedelta(hours=24) - datetime.datetime.utcnow()
        )
        text += (
            f'------\n'
            f'❗️После удачной/неудачной покупки, <b>нажмите на одну из кнопок ниже</b>, в соответствии с тем, взяли вы билет или нет. '
            f'Если вы ничего не выберите, <b>отслеживание перестанет быть активным через '
            f'{str(deactivate_tracking_time).split(".")[0]}</b>'
        )
        return text

    async def _handle_tracking(
            self,
            tracking: TrackingModel,
    ):

        rzd_parser = RZDParser()
        trains = await rzd_parser.get_trains(
            from_city_id=tracking.from_city_id,
            to_city_id=tracking.to_city_id,
            date=tracking.date
        )
        filtered_trains = filter_trains_by_tracking(
            trains=trains,
            max_price=tracking.max_price,
            sw_enabled=tracking.sw_enabled,
            sid_enabled=tracking.sid_enabled,
            plaz_seats_plaz_down_enabled=tracking.plaz_seats_plaz_down_enabled,
            plaz_seats_plaz_up_enabled=tracking.plaz_seats_plaz_up_enabled,
            plaz_side_down_enabled=tracking.plaz_side_down_enabled,
            plaz_side_up_enabled=tracking.plaz_side_up_enabled,
            cupe_up_enabled=tracking.cupe_up_enabled,
            cupe_down_enabled=tracking.cupe_down_enabled,
            min_seats=1
        )
        async with async_session_maker() as session:
            tracking_manager = TrackingManager(session=session)
            tracking_notification_manager = TrackingNotificationManager(session=session)

            # Проверка предыдущей нотификации.
            #  Если в течение 5 минут уже была нотификация по этому отслеживанию, то не отправляем
            last_notification_by_tracking = await tracking_notification_manager.get_last_notification_by_tracking_id(
                tracking_id=tracking.id
            )
            notification_waited_flag = (
                    last_notification_by_tracking is None
                    or (datetime.datetime.utcnow() - datetime.timedelta(
                minutes=5)) > last_notification_by_tracking.created_at
            )
            if notification_waited_flag and len(filtered_trains) > 0:
                # Сохраняем информацию о первой нотификации об отслеживании
                if tracking.first_notification_sent_at is None:
                    await tracking_manager.update(
                        obj_id=tracking.id,
                        obj_in=TrackingUpdateSchema(first_notification_sent_at=datetime.datetime.utcnow())
                    )
                    tracking = await tracking_manager.get(tracking.id)
                sent_message = await self._aiogram_bot.send_message(
                    chat_id=tracking.user_id,
                    text=self._generate_notification_text_from_trains(tracking=tracking, trains=filtered_trains),
                    parse_mode='HTML',
                    disable_web_page_preview=True,
                    reply_markup=found_seats_notification_kb(tracking_id=tracking.id)
                )
                #  Сохраняем информацию о нотификации
                await tracking_notification_manager.create(TrackingNotificationCreateSchema(
                    tracking_id=tracking.id,
                    user_id=tracking.user_id,
                    telegram_message_id=sent_message.message_id
                ))
                logger.info(f'tracking #{tracking.id} sent notification')
            await session.commit()

        logger.debug(f'#{tracking.id} handled')

    async def _handle_tracking_with_exception_handling(
            self,
            queue_tracking_ids: Queue,
            mapping_id_to_tracking: dict[int, TrackingModel]
    ):

        self._current_parallel_handlers += 1
        try:
            tracking = await self._get_tracking(
                queue_tracking_ids=queue_tracking_ids,
                mapping_id_to_tracking=mapping_id_to_tracking
            )
        except TrackingFinishedException:
            self._current_parallel_handlers -= 1
            return

        try:
            await self._handle_tracking(tracking=tracking)
            self._last_connection_statuses = self._last_connection_statuses[::-1][:self._length_of_last_connection_statuses] + [True]
        except asyncio.exceptions.TimeoutError:
            # Информацию о каждой ошибке подключения не присылаем
            self._last_connection_statuses = self._last_connection_statuses[::-1][:self._length_of_last_connection_statuses] + [False]
            if len(self._last_connection_statuses) == self._length_of_last_connection_statuses and not any(self._last_connection_statuses):
                logger.error(f'Произошла ошибка подключения к серверу РЖД ({self._length_of_last_connection_statuses} подряд)')
                self._last_connection_statuses = []
        except JSONDecodeError as exc:
            logger.error(f'Ошибка декодирования ответа от сервера: \n{exc.doc}')
        except Exception:
            logger.error(f'Произошла неизвестная ошибка:\n {traceback.format_exc()}')

        try:
            await self._put_tracking(
                tracking=tracking,
                queue_tracking_ids=queue_tracking_ids,
                mapping_id_to_tracking=mapping_id_to_tracking
            )
        except TrackingFinishedException:
            pass

        self._current_parallel_handlers -= 1

    async def one_cycle(
            self,
            queue_tracking_ids: Queue,
            mapping_id_to_tracking: dict[int, TrackingModel]
    ):
        async with async_session_maker() as session:
            tracking_manager = TrackingManager(session=session)
            trackings = await tracking_manager.get_all_tracking(only_active=True)

        # Обновляем текущие трекинги + добавляем новые
        for tracking in trackings:
            if tracking.is_finished:
                continue
            if tracking.user.is_banned:
                continue
            if datetime.datetime.utcnow() > tracking.user.subscription_expires_at:
                continue
            # Если этого трекинга нет в обработке
            if tracking.id not in mapping_id_to_tracking:
                logger.info(f'Tracking #{tracking.id} added')
                queue_tracking_ids.put(tracking.id)  # добавляем в конец очереди
            # Обновляем/Создаем объект трекинга в маппинге для будущей обработки
            mapping_id_to_tracking[tracking.id] = tracking

        # Удаляем финишированные трекинги
        tracking_ids_from_database = set(map(lambda tracking: tracking.id, trackings))
        deleted_tracking_ids = list(filter(
            lambda tracking_id: tracking_id not in tracking_ids_from_database,
            mapping_id_to_tracking
        ))
        for deleted_tracking_id in deleted_tracking_ids:
            del mapping_id_to_tracking[deleted_tracking_id]

        # Проходимся по очереди отслеживаний
        i = 0
        while i < len(trackings):
            if self._current_parallel_handlers < self._limit_of_parallel_handlers and not queue_tracking_ids.empty():
                asyncio.create_task(self._handle_tracking_with_exception_handling(
                    queue_tracking_ids=queue_tracking_ids,
                    mapping_id_to_tracking=mapping_id_to_tracking
                ))
                i += 1
            await asyncio.sleep(0.01)

    async def start(self):
        logger.info('Background TrackingParser started')
        queue_tracking_ids: Queue = Queue()  # Очередь, которая используется для обработки отслеживаний
        mapping_id_to_tracking: dict[int, TrackingModel] = dict()  # {12: TrackingModel()}

        while True:
            #  logger.debug('Завершен круг очереди отслеживаний')

            try:
                await self.one_cycle(
                    queue_tracking_ids=queue_tracking_ids,
                    mapping_id_to_tracking=mapping_id_to_tracking
                )
            except Exception:
                logger.error(f'Global error in cycle of TrackingParser: \n'
                             f'{traceback.format_exc()}')
