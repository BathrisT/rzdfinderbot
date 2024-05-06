import datetime
from typing import Optional, Union
from pydantic import BaseModel


class TrackingCreateSchema(BaseModel):
    user_id: int

    from_city_name: str
    from_city_id: str
    from_city_site_code: str = None

    to_city_name: str
    to_city_id: str
    to_city_site_code: str = None

    date: datetime.date
    max_price: Optional[Union[int, float]] = None

    sw_enabled: bool = True
    sid_enabled: bool = True

    plaz_seats_plaz_down_enabled: bool = True
    plaz_seats_plaz_up_enabled: bool = True
    plaz_side_down_enabled: bool = True
    plaz_side_up_enabled: bool = True

    cupe_up_enabled: bool = True
    cupe_down_enabled: bool = True


class TrackingUpdateSchema(BaseModel):
    from_city_name: Optional[str] = None
    from_city_id: Optional[str] = None
    from_city_site_code: Optional[str] = None

    to_city_name: Optional[str] = None
    to_city_id: Optional[str] = None
    to_city_site_code: Optional[str] = None

    date: Optional[datetime.date] = None
    max_price: Optional[Union[int, float]] = None

    sw_enabled: Optional[bool] = None
    sid_enabled: Optional[bool] = None

    plaz_seats_plaz_down_enabled: Optional[bool] = None
    plaz_seats_plaz_up_enabled: Optional[bool] = None
    plaz_side_down_enabled: Optional[bool] = None
    plaz_side_up_enabled: Optional[bool] = None

    cupe_up_enabled: Optional[bool] = None
    cupe_down_enabled: Optional[bool] = None


    first_notification_sent_at: Optional[datetime.datetime] = None

    is_finished: Optional[bool] = None
    finished_at: Optional[datetime.datetime] = None
