from functools import lru_cache
from typing import Union

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataBase(BaseModel):
    user: str
    password: str
    host: str
    port: int
    name: str


class Redis(BaseModel):
    password: str
    host: str
    port: int


class TgBot(BaseModel):
    token: str
    username: str

class Links(BaseModel):
    reviews_link: str
    channel_link: str
    support_link: str

class Payment(BaseModel):
    provider_token: str

class ServiceNotifications(BaseModel):
    bot_token: str
    chat_id: Union[int, str]
    project_name: str

class Config(BaseSettings):
    database: DataBase
    redis: Redis
    tg_bot: TgBot
    links: Links
    payment: Payment
    service_notifications: ServiceNotifications

    model_config = SettingsConfigDict(
        env_file=('.env', '../.env'),
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        extra='ignore'
    )


@lru_cache
def get_config():
    return Config()
