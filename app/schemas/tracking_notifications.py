from pydantic import BaseModel

from typing import Optional


class TrackingNotificationCreateSchema(BaseModel):
    tracking_id: int
    user_id: int
    train_number: Optional[str] = None


class TrackingNotificationUpdateSchema(BaseModel):
    train_number: Optional[str] = None
