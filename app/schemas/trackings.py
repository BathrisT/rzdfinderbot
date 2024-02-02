import datetime
from typing import Optional, Union
from pydantic import BaseModel


class TrackingCreateSchema(BaseModel):
    user_id: int

    from_city_name: str
    from_city_id: str

    to_city_name: str
    to_city_id: str

    date: datetime.date
    max_price: Optional[Union[int, float]] = None


class TrackingUpdateSchema(BaseModel):
    from_city_name: Optional[str] = None
    from_city_id: Optional[str] = None

    to_city_name: Optional[str] = None
    to_city_id: Optional[str] = None

    date: Optional[datetime.date] = None
    max_price: Optional[Union[int, float]] = None

    first_notification_sent_at: Optional[datetime.datetime] = None

    is_finished: Optional[bool] = None
    finished_at: Optional[datetime.datetime] = None
