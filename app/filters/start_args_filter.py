import datetime
from typing import Union, Optional

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from models.users import UserModel


class StartArgsFilter(BaseFilter):
    """
    Фильтр по наличию/отсутствию аргумента при вызове команды (/start awd)
    """

    def __init__(self, finding_startswith: Optional[str] = None):
        """
        :param finding_startswith:
        - если None, то проверяем отсутствие аргументов
        - если строка, то ищем наличие её в самом начале первого аргумента
        """
        self._finding_startswith = finding_startswith

    async def __call__(self, message: Message, current_user: UserModel) -> bool:
        args = message.text.split()

        if len(args) == 1 and self._finding_startswith is not None:
            return False

        if len(args) != 1 and self._finding_startswith is None:
            return False

        if len(args) == 1 and self._finding_startswith is None:
            return True

        return args[1].startswith(self._finding_startswith)

