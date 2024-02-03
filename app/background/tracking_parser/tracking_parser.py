import asyncio
import datetime
import random
from queue import Queue

from utils.filter_trains import filter_trains
from utils.rzd_parser import RZDParser
from .exceptions import TrackingFinishedException
from cruds.trackings import TrackingManager
from database import async_session_maker
from models.trackings import TrackingModel


class TrackingParser:
    def __init__(self, limit_of_parallel_handlers: int = 15):
        self._limit_of_parallel_handlers = limit_of_parallel_handlers
        self._current_parallel_handlers = 0

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

    async def _handle_tracking(
            self,
            queue_tracking_ids: Queue,
            mapping_id_to_tracking: dict[int, TrackingModel]
    ):
        tracking = await self._get_tracking(
            queue_tracking_ids=queue_tracking_ids,
            mapping_id_to_tracking=mapping_id_to_tracking
        )

        #print(f'{datetime.datetime.now()}: #{tracking.id} start')
        rzd_parser = RZDParser()
        trains = await rzd_parser.get_trains(
            from_city_id=tracking.id,
            to_city_id=tracking.id,
            date=tracking.date
        )
        await rzd_parser.close_session()
        filtered_trains = filter_trains(
            trains=trains,
            max_price=tracking.max_price
        )
        await asyncio.sleep(random.randint(1, 1))
        print(f'{datetime.datetime.now()}: #{tracking.id} finish')

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
        except TrackingFinishedException as exc:
            print(f'Tracking #{exc.tracking_id} finished')
        self._current_parallel_handlers -= 1

    async def start(self):
        print('Background TrackingParser started')
        queue_tracking_ids: Queue = Queue()  # Очередь, которая используется для обработки отслеживаний
        mapping_id_to_tracking: dict[int, TrackingModel] = dict()  # {12: TrackingModel()}

        while True:
            print('handled all')  # TODO
            # Получаем все отслеживания
            async with async_session_maker() as session:
                tracking_manager = TrackingManager(session=session)
                trackings = await tracking_manager.get_all_tracking(only_active=True)

            # Обновляем текущие трекинги + добавляем новые
            for tracking in trackings:
                if tracking.is_finished:
                    continue
                # Если этого трекинга нет в обработке
                if tracking.id not in mapping_id_to_tracking:
                    print(f'Tracking #{tracking.id} added')
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
                await asyncio.sleep(0.1)

