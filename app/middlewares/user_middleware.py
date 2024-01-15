from typing import Callable, Awaitable, Any

from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, TelegramObject, User
from cruds.users import UserManager
from database import async_session_maker

from models.users import UserModel
from schemas.users import UserCreateSchema, UserUpdateSchema


class UserMiddleware(BaseMiddleware):
    """
    Мидлварь, которая проверяет заблокирован ли юзер, и добавляет его объект в контекст (+ создает, если нужно)
    """
    @staticmethod
    async def _add_current_user_to_context(
            context_data: dict
    ) -> UserModel:
        event_from_user: User = context_data['event_from_user']

        async with async_session_maker() as session:
            user_crud = UserManager(session=session)

            current_user = await user_crud.get(obj_id=event_from_user.id)
            if current_user is None:
                current_user = await user_crud.create(UserCreateSchema(
                    id=event_from_user.id,
                    first_name=event_from_user.first_name,
                    last_name=event_from_user.last_name,
                    username=event_from_user.username
                ))
            else:
                await user_crud.update(
                    obj_id=event_from_user.id,
                    obj_in=UserUpdateSchema(
                        first_name=event_from_user.first_name,
                        last_name=event_from_user.last_name,
                        username=event_from_user.username
                    )
                )
            await session.commit()

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
        # Если юзер забанен - доступ к боту заблокирован
        if current_user.is_banned:
            return

        return await handler(event, data)
