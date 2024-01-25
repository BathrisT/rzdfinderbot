import datetime

from pydantic import BaseModel, Field


class City(BaseModel):
    name: str
    region: str
    station_code: str = Field(alias='expressCode')


class Train(BaseModel):
    train_number: str = Field(alias='DisplayTrainNumber')
    departure_date: datetime.datetime = Field(alias='DepartureDateTime')
    arrival_date: datetime.datetime = Field(alias='ArrivalDateTime')

    from_city_id: str = Field(alias='OriginStationCode')
    from_city_name: str = Field(alias='OriginName')

    to_city_id: str = Field(alias='DestinationStationCode')
    to_city_name: str = Field(alias='DestinationName')

    sw_seats: int
    sw_min_price: float

    plaz_seats: int
    plaz_min_price: float

    cupe_seats: int
    cupe_min_price: float

    sid_seats: int
    sid_min_price: float
