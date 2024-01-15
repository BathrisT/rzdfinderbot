from typing import Optional

from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    id: int  # tg id

    first_name: str  # имя в тг
    last_name: Optional[str]  # фамилия в тг
    username: Optional[str]  # username в тг


class UserUpdateSchema(BaseModel):
    first_name: Optional[str]  # имя в тг
    last_name: Optional[str]  # фамилия в тг
    username: Optional[str]  # username в тг

    is_banned: Optional[bool]  # забанен ли в боте
