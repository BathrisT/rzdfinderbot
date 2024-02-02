import datetime
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from cruds.trackings import TrackingManager
from database import async_session_maker
from models.users import UserModel


class AtLeastOneTrackingExistsFilter(BaseFilter):
    def __init__(self, check_for_lack: bool = False):
        self._check_for_lack = check_for_lack

    async def __call__(self, query: Union[Message, CallbackQuery], current_user: UserModel) -> bool:
        async with async_session_maker() as session:
            tracking_manager = TrackingManager(session=session)
            user_trackings = await tracking_manager.get_user_trackings(user_id=current_user.id, only_active=False)

        if self._check_for_lack:
            return len(user_trackings) == 0
        else:
            return len(user_trackings) != 0
