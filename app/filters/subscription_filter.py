import datetime
from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from models.users import UserModel


class SubscriptionFilter(BaseFilter):
    def __init__(self, checking_for_lack: bool = False):
        """
        :param checking_for_lack: если True, то проверяем отсутствие подписки, а не наличие
        """
        self.lack_check_function = lambda el: not el if checking_for_lack else el

    async def __call__(self, query: Union[Message, CallbackQuery], current_user: UserModel) -> bool:
        return self.lack_check_function(
            current_user.subscription_expires_at is not None and
            (datetime.datetime.utcnow() <= current_user.subscription_expires_at)
        )
