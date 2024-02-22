import asyncio
import datetime
import traceback
from json import JSONDecodeError
from queue import Queue

from aiogram import Bot
from httpx import TimeoutException
from loguru import logger

from cruds.tracking_notifications import TrackingNotificationManager
from cruds.trackings import TrackingManager
from database import async_session_maker
from keyboards.trackings import found_seats_notification_kb
from models.trackings import TrackingModel
from schemas.rzd_parser import Train
from schemas.tracking_notifications import TrackingNotificationCreateSchema
from schemas.trackings import TrackingUpdateSchema
from utils.filter_trains import filter_trains, check_min_price
from utils.rzd_links_generator import create_url_to_trains
from utils.rzd_parser import RZDParser
from .exceptions import TrackingFinishedException


# TODO: обработка ошибок  # class logging
# TODO: подумать что делать с таймаутом
class TrackingParser:
    def __init__(
            self,
            aiogram_bot_token: str,
            limit_of_parallel_handlers: int = 15,
    ):
        self._limit_of_parallel_handlers = limit_of_parallel_handlers
        self._current_parallel_handlers = 0
        self._aiogram_bot = Bot(token=aiogram_bot_token)

        self._connection_errors_counter = 0

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
            # train.sw_seats, train.cupe_seats, train.plaz_seats, train.sid_seats
            if train.sw_seats >= 1 and check_min_price(tracking.max_price, train.sw_min_price):
                available_filtered_seats.append(f'<b>СВ [{train.sw_seats}]</b> - {int(train.sw_min_price)}₽')
            if train.cupe_seats >= 1 and check_min_price(tracking.max_price, train.cupe_min_price):
                available_filtered_seats.append(f'<b>Купе [{train.cupe_seats}]</b> - {int(train.cupe_min_price)}₽')
            if train.plaz_seats >= 1 and check_min_price(tracking.max_price, train.plaz_min_price):
                available_filtered_seats.append(f'<b>Плац [{train.plaz_seats}]</b> - {int(train.plaz_min_price)}₽')
            if train.sid_seats >= 1 and check_min_price(tracking.max_price, train.sid_min_price):
                available_filtered_seats.append(f'<b>Сид [{train.sid_seats}]</b> - {int(train.sid_min_price)}₽')
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
            queue_tracking_ids: Queue,
            mapping_id_to_tracking: dict[int, TrackingModel]
    ):
        tracking = await self._get_tracking(
            queue_tracking_ids=queue_tracking_ids,
            mapping_id_to_tracking=mapping_id_to_tracking
        )
        rzd_parser = RZDParser()
        trains = await rzd_parser.get_trains(
            from_city_id=tracking.from_city_id,
            to_city_id=tracking.to_city_id,
            date=tracking.date
        )
        await rzd_parser.close_session()
        filtered_trains = filter_trains(
            trains=trains,
            max_price=tracking.max_price
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
                await self._aiogram_bot.send_message(
                    chat_id=tracking.user_id,
                    text=self._generate_notification_text_from_trains(tracking=tracking, trains=filtered_trains),
                    parse_mode='HTML',
                    disable_web_page_preview=True,
                    reply_markup=found_seats_notification_kb(tracking_id=tracking.id)
                )
                #  Сохраняем информацию о нотификации
                await tracking_notification_manager.create(TrackingNotificationCreateSchema(
                    tracking_id=tracking.id,
                    user_id=tracking.user_id
                ))
            await session.commit()

        logger.debug(f'#{tracking.id} handled')

        await self._put_tracking(
            tracking=tracking,
            queue_tracking_ids=queue_tracking_ids,
            mapping_id_to_tracking=mapping_id_to_tracking
        )

    async def _handle_tracking_with_exception_handling(
            self,
            queue_tracking_ids: Queue,
            mapping_id_to_tracking: dict[int, TrackingModel]
    ):
        self._current_parallel_handlers += 1
        try:
            await self._handle_tracking(
                queue_tracking_ids=queue_tracking_ids,
                mapping_id_to_tracking=mapping_id_to_tracking
            )
        except TrackingFinishedException:
            pass
        except TimeoutException:
            # Информацию о каждой ошибке подключения не присылаем
            self._connection_errors_counter += 1
            if self._connection_errors_counter == 10:
                logger.error(f'Произошла ошибка подключения к серверу РЖД')
                self._connection_errors_counter = 0
        except JSONDecodeError as exc:
            logger.error(f'Ошибка декодирования ответа от сервера: \n{exc.doc}')
        except Exception:
            logger.error(f'Произошла неизвестная ошибка:\n {traceback.format_exc()}')
        self._current_parallel_handlers -= 1

    async def start(self):
        logger.info('Background TrackingParser started')
        queue_tracking_ids: Queue = Queue()  # Очередь, которая используется для обработки отслеживаний
        mapping_id_to_tracking: dict[int, TrackingModel] = dict()  # {12: TrackingModel()}

        while True:
            logger.debug('Завершен круг очереди отслеживаний')
            # Получаем все отслеживания
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
