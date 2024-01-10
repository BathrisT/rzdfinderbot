from functools import lru_cache

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


class Config(BaseSettings):
    database: DataBase
    redis: Redis
    tg_bot: TgBot

    model_config = SettingsConfigDict(
        env_file=('.env', '../.env'),
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        extra='ignore'
    )


@lru_cache
def get_config():
    return Config()
