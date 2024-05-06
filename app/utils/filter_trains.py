from typing import Union, Optional

from schemas.rzd_parser import Train


def check_min_price(max_price: Optional[Union[int, float]], min_price_on_train: Union[int, float]):
    return max_price is None or min_price_on_train <= max_price

def filter_trains_by_tracking(
        trains: list[Train],
        sw_enabled: bool,
        sid_enabled: bool,

        plaz_seats_plaz_down_enabled: bool,
        plaz_seats_plaz_up_enabled: bool,
        plaz_side_down_enabled: bool,
        plaz_side_up_enabled: bool,
        cupe_up_enabled: bool,
        cupe_down_enabled: bool,
        max_price: Union[int, float],

        min_seats: int = 1
) -> list[Train]:
    specific_trains = []
    for train in trains:

        # Фильтрация по СВ
        if sw_enabled and train.sw_seats >= min_seats and check_min_price(max_price, train.sw_min_price):
            specific_trains.append(train)

        # Фильтрация по сидячим местам
        elif sid_enabled and train.sid_seats >= min_seats and check_min_price(max_price, train.sid_min_price):
            specific_trains.append(train)

        # Фильтрация по купе
        elif cupe_up_enabled and train.cupe_up_seats >= min_seats and check_min_price(max_price, train.cupe_min_price):
            specific_trains.append(train)
        elif cupe_down_enabled and train.cupe_down_seats >= min_seats and check_min_price(max_price, train.cupe_min_price):
            specific_trains.append(train)

        # Фильтрация по плацкарту
        elif plaz_seats_plaz_down_enabled and train.plaz_seats_plaz_down_seats >= min_seats and check_min_price(max_price, train.cupe_min_price):
            specific_trains.append(train)
        elif plaz_seats_plaz_up_enabled and train.plaz_seats_plaz_up_seats >= min_seats and check_min_price(max_price, train.cupe_min_price):
            specific_trains.append(train)
        elif plaz_side_down_enabled and train.plaz_side_down_seats >= min_seats and check_min_price(max_price, train.cupe_min_price):
            specific_trains.append(train)
        elif plaz_side_up_enabled and train.plaz_side_up_seats >= min_seats and check_min_price(max_price, train.cupe_min_price):
            specific_trains.append(train)

        if train.train_number == '077Ы':
            print('077Ы', train)

    return specific_trains

