from typing import Callable, Awaitable, Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject, User

from cruds.admins import admin_crud
from cruds.users import user_crud
from models.users import UserModel
from schemas.users import UserCreateSchema


class UserMiddleware(BaseMiddleware):
    @staticmethod
    async def _add_current_user_to_context(
            context_data: dict
    ) -> UserModel:
        event_from_user: User = context_data['event_from_user']

        current_user = await user_crud.get(obj_id=event_from_user.id)
        if current_user is None:
            current_user = await user_crud.create(UserCreateSchema(
                id=event_from_user.id,
                first_name=event_from_user.first_name,
                last_name=event_from_user.last_name,
                username=event_from_user.username
            ))
        context_data["current_user"] = current_user
        return current_user

    async def __call__(
            self,
            handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any]
    ) -> Any:
        current_user = await self._add_current_user_to_context(
            context_data=data
        )
        # Если юзер забанен и не админ - доступ к боту заблокирован
        if current_user.is_banned:
            admin = await admin_crud.get(current_user.id)
            if not admin:
                return

        return await handler(event, data)
