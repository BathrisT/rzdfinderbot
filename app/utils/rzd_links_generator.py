import datetime
from typing import Union


def create_url_to_trains(
        from_city_site_code: str,
        to_city_site_code: str,
        date: Union[datetime.date, str]
):
    if type(date) is datetime.date:
        date = date.isoformat()
    url = f'https://ticket.rzd.ru/searchresults/v/1/{from_city_site_code}/{to_city_site_code}/{date}'
    return url
