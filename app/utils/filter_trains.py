from typing import Union, Optional

from schemas.rzd_parser import Train


def check_min_price(max_price: Optional[Union[int, float]], min_price_on_train: Union[int, float]):
    return max_price is None or min_price_on_train <= max_price

def filter_trains(
        trains: list[Train],
        max_price: Union[int, float]
) -> list[Train]:
    specific_trains = []
    for train in trains:
        # train.sw_seats, train.cupe_seats, train.plaz_seats, train.sid_seats
        if train.sw_seats > 1 and check_min_price(max_price, train.sw_min_price):
            specific_trains.append(train)
        elif train.cupe_seats > 1 and check_min_price(max_price, train.cupe_min_price):
            specific_trains.append(train)
        elif train.plaz_seats > 1 and check_min_price(max_price, train.plaz_min_price):
            specific_trains.append(train)
        elif train.sid_min_price > 1 and check_min_price(max_price, train.sid_min_price):
            specific_trains.append(train)
    return specific_trains
