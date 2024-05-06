import datetime

from pydantic import BaseModel, Field


class City(BaseModel):
    name: str
    region: str
    station_code: str = Field(alias='expressCode')
    site_code: str = Field(alias='busCode')


class Train(BaseModel):
    train_number: str = Field(alias='DisplayTrainNumber')
    departure_date: datetime.datetime = Field(alias='DepartureDateTime')
    arrival_date: datetime.datetime = Field(alias='ArrivalDateTime')

    from_city_id: str = Field(alias='OriginStationCode')
    from_city_name: str = Field(alias='OriginName')

    to_city_id: str = Field(alias='DestinationStationCode')
    to_city_name: str = Field(alias='DestinationName')

    # СВ
    sw_seats: int
    sw_min_price: float

    # Сидячие места
    sid_seats: int
    sid_min_price: float

    # Плацкарт
    plaz_min_price: float = 9999999999999999
    # [Плац] плацкарт нижнее:
    plaz_seats_plaz_down_seats: int
    # [Плац] плацкарт верхнее:
    plaz_seats_plaz_up_seats: int
    # [Плац] Боковое верхнее:
    plaz_side_down_seats: int
    # [Плац] Боковое нижнее:
    plaz_side_up_seats: int

    # Купе
    cupe_min_price: float = 9999999999999999
    # [Купе] Верхнее:
    cupe_up_seats: int
    # [Купе] Нижнее:
    cupe_down_seats: int
