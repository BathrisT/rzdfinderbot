from pydantic import BaseModel

from typing import Optional


class TrackingNotificationCreateSchema(BaseModel):
    tracking_id: int
    user_id: int
    train_number: Optional[str] = None
    telegram_message_id: int


class TrackingNotificationUpdateSchema(BaseModel):
    train_number: Optional[str] = None
    telegram_message_id: int
