import asyncio
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
            timeout=aiohttp.ClientTimeout(total=5)
        )

    async def get_cities_by_query(self, query: str) -> list[City]:
        async with self._get_new_session() as session:
            response = await session.get(
                url='api/v1/suggests',
                params={
                    'Query': query,
                    'TransportType': 'bus,avia,rail,aeroexpress,suburban,boat',
                    'GroupResults': True,
                    'RailwaySortPriority': True,
                    'MergeSuburban': True
                }
            )
            response_text = await response.text()
            logger.debug(
                f'Запрос к api/v1/suggests. Query: "{query}"; \n'
                f'Ответ: "{response_text[:150]}..."'
            )
            response_data = await response.json()

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
            data = await response.json()

        if 'Trains' not in data:
            logger.error(f'Ржд отдал неверный ответ: {data}')

        trains: list[Train] = []

        for train_json in data['Trains']:
            sw_seats: int = 0
            sw_min_price: float = 9999999999999999

            plaz_seats: int = 0
            plaz_min_price: float = 9999999999999999

            cupe_seats: int = 0
            cupe_min_price: float = 9999999999999999

            sid_seats: int = 0
            sid_min_price: float = 9999999999999999

            for t in train_json['CarGroups'][:-1]:
                if t['CarTypeName'] == 'ПЛАЦ':
                    plaz_seats += int(t['TotalPlaceQuantity'])
                    plaz_min_price = min(plaz_min_price, float(t['MinPrice']))
                elif t['CarTypeName'] == 'СВ':
                    sw_seats += int(t['TotalPlaceQuantity'])
                    sw_min_price = min(sw_min_price, float(t['MinPrice']))
                elif t['CarTypeName'] == 'КУПЕ':
                    cupe_seats += int(t['TotalPlaceQuantity'])
                    cupe_min_price = min(cupe_min_price, float(t['MinPrice']))
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
                    plaz_seats=plaz_seats,
                    plaz_min_price=plaz_min_price,
                    cupe_seats=cupe_seats,
                    cupe_min_price=cupe_min_price,
                    sid_seats=sid_seats,
                    sid_min_price=sid_min_price
                ))
        return trains


async def main():
    parser = RZDParser()

    # data = await parser.get_trains(
    #     from_city_id='2060600',
    #     to_city_id='2060000',
    #     date=datetime.fromisoformat('2024-01-13T00:00:00')
    # )
    # from pprint import pprint
    # for t in data:
    #     print(t)


if __name__ == '__main__':
    asyncio.run(main())
