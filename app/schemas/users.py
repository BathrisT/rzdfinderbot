import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    id: int  # tg id

    first_name: str  # имя в тг
    last_name: Optional[str] = None  # фамилия в тг
    username: Optional[str] = None  # username в тг


class UserUpdateSchema(BaseModel):
    first_name: Optional[str] = None  # имя в тг
    last_name: Optional[str] = None  # фамилия в тг
    username: Optional[str] = None  # username в тг

    is_banned: Optional[bool] = None  # забанен ли в боте

    subscription_expires_at: Optional[datetime.datetime] = None
    last_expire_notification_sent_at: Optional[datetime.datetime] = None
