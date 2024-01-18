from typing import Callable, Awaitable, Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject
from database import async_session_maker


class SQLAlchemySessionMiddleware(BaseMiddleware):
    """
    Мидлварь, которая создает сессию, далее сессию можно получить в хендлере
    """

    async def __call__(
            self,
            handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any]
    ) -> Any:
        async with async_session_maker() as session:
            data['session'] = session
            result = await handler(event, data)
        return result
