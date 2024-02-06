import datetime
from typing import Union, Optional


def create_url_to_trains(
        from_city_site_code: str,
        to_city_site_code: str,
        date: Union[datetime.date, str],
        train_number: Optional[str] = None
):
    if type(date) is datetime.date:
        date = date.isoformat()
    url = f'https://ticket.rzd.ru/searchresults/v/1/{from_city_site_code}/{to_city_site_code}/{date}?aim=social-media'
    if train_number:
        url += f'&trainNumber={train_number}'
    return url
