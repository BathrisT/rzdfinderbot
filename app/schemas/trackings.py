import datetime
from typing import Optional
from pydantic import BaseModel


class TrackingCreateSchema(BaseModel):
    user_id: int
    from_city_id: str
    to_city_id: str
    date: datetime.date
    max_price: Optional[int]


class TrackingUpdateSchema(BaseModel):
    from_city_id: Optional[str]
    to_city_id: Optional[str]
    date: Optional[datetime.date]
    max_price: Optional[int]

    first_notification_sent_at: Optional[datetime.datetime]

    is_finished: Optional[bool]
    finished_at: Optional[datetime.datetime]

    created_at: datetime.datetime
