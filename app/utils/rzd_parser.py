import asyncio
import json
from datetime import datetime
from typing import Optional

from loguru import logger
import aiohttp
import fake_useragent

from schemas.rzd_parser import City, Train


class RZDParser:
    @staticmethod
    def _get_new_session() -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            headers={
                'User-Agent': fake_useragent.UserAgent().random,
                'Origin': 'https://ticket.rzd.ru',
                'Host': 'ticket.rzd.ru',
                'Referer': 'https://ticket.rzd.ru'
            },
            base_url='https://ticket.rzd.ru',
            timeout=aiohttp.ClientTimeout(total=5, connect=5)
        )

    async def get_cities_by_query(self, query: str) -> list[City]:
        async with self._get_new_session() as session:
            response = await session.get(
                url='/api/v1/suggests',
                params={
                    'Query': query,
                    'TransportType': 'bus,avia,rail,aeroexpress,suburban,boat',
                    'GroupResults': 'true',
                    'RailwaySortPriority': 'true',
                    'MergeSuburban': 'true'
                }
            )
            response_text = await response.text()
            logger.debug(
                f'Запрос к api/v1/suggests. Query: "{query}"; \n'
                f'Ответ: "{response_text[:150]}..."'
            )
            response_data = json.loads(response_text)

        if len(response_data) == 0:
            return []

        cities = response_data['city']
        return [City.model_validate(city) for city in cities if 'expressCode' in city and 'busCode' in city]

    async def get_trains(
            self,
            from_city_id: str,
            to_city_id: str,
            date: datetime.date
    ) -> list[Train]:
        async with self._get_new_session() as session:
            response = await session.post(
                url='/apib2b/p/Railway/V1/Search/TrainPricing?service_provider=B2B_RZD',
                json={
                    "Origin": from_city_id,
                    "Destination": to_city_id,
                    "DepartureDate": date.isoformat(),
                    "TimeFrom": 0,
                    "TimeTo": 24,
                    "CarGrouping": "DontGroup",
                    "GetByLocalTime": True,
                    "SpecialPlacesDemand": "StandardPlacesAndForDisabledPersons",
                    "CarIssuingType": "PassengersAndBaggage"
                }
            )
            response_text = await response.text()
            logger.debug(
                f'Запрос к /apib2b/p/Railway/V1/Search/TrainPricing?service_provider=B2B_RZD; \n'
                f'Ответ: "{response_text[:150]}..."'
            )
            response_data = json.loads(response_text)

        if 'Trains' not in response_data:
            logger.error(f'Ржд отдал неверный ответ: {response_data}')

        trains: list[Train] = []

        for train_json in response_data['Trains']:

            # СВ
            sw_seats: int = 0
            sw_min_price: float = 9999999999999999

            # Плацкарт
            plaz_min_price: float = 9999999999999999
            # [Плац] плацкарт нижнее:
            plaz_seats_plaz_down_seats: int = 0
            # [Плац] плацкарт верхнее:
            plaz_seats_plaz_up_seats: int = 0
            # [Плац] Боковое верхнее:
            plaz_side_down_seats: int = 0
            # [Плац] Боковое нижнее:
            plaz_side_up_seats: int = 0

            # Купе
            cupe_min_price: float = 9999999999999999
            # [Купе] Верхнее:
            cupe_up_seats: int = 0
            # [Купе] Нижнее:
            cupe_down_seats: int = 0

            # Сидячие места
            sid_seats: int = 0
            sid_min_price: float = 9999999999999999

            for t in train_json['CarGroups']:
                if t.get('HasPlacesForDisabledPersons'):
                    continue
                if t['CarTypeName'] == 'ПЛАЦ':
                    plaz_seats_plaz_down_seats += int(t['LowerPlaceQuantity'])
                    plaz_seats_plaz_up_seats += int(t['UpperPlaceQuantity'])
                    plaz_side_down_seats += int(t['LowerSidePlaceQuantity'])
                    plaz_side_up_seats += int(t['UpperSidePlaceQuantity'])
                    plaz_min_price = min(plaz_min_price, float(t['MinPrice']))
                elif t['CarTypeName'] == 'КУПЕ':
                    cupe_up_seats += int(t['UpperPlaceQuantity'])
                    cupe_down_seats += int(t['LowerPlaceQuantity'])
                    cupe_min_price = min(cupe_min_price, float(t['MinPrice']))
                elif t['CarTypeName'] == 'СВ':
                    sw_seats += int(t['TotalPlaceQuantity'])
                    sw_min_price = min(sw_min_price, float(t['MinPrice']))
                elif t['CarTypeName'] == 'СИД':
                    sid_seats += int(t['PlaceQuantity'])
                    sid_min_price = min(sid_min_price, float(t['MinPrice']))

            trains.append(
                Train(
                    DisplayTrainNumber=train_json['DisplayTrainNumber'],
                    DepartureDateTime=train_json['DepartureDateTime'],
                    ArrivalDateTime=train_json['ArrivalDateTime'],
                    OriginStationCode=train_json['OriginStationCode'],
                    OriginName=train_json['OriginName'],
                    DestinationStationCode=train_json['DestinationStationCode'],
                    DestinationName=train_json['DestinationName'],

                    sw_seats=sw_seats,
                    sw_min_price=sw_min_price,

                    plaz_min_price=plaz_min_price,
                    plaz_seats_plaz_down_seats=plaz_seats_plaz_down_seats,
                    plaz_seats_plaz_up_seats=plaz_seats_plaz_up_seats,
                    plaz_side_down_seats=plaz_side_down_seats,
                    plaz_side_up_seats=plaz_side_up_seats,

                    cupe_min_price=cupe_min_price,
                    cupe_down_seats=cupe_down_seats,
                    cupe_up_seats=cupe_up_seats,

                    sid_seats=sid_seats,
                    sid_min_price=sid_min_price
                ))
        return trains


async def main():
    parser = RZDParser()

    data = await parser.get_trains(
        from_city_id='2060600',
        to_city_id='2060000',
        date=datetime.fromisoformat('2024-05-13T00:00:00')
    )
    from pprint import pprint
    for t in data:
        print(t)


if __name__ == '__main__':
    asyncio.run(main())
