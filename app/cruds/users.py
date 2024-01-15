from sqlalchemy.ext.asyncio.session import AsyncSession

from cruds.base_manager import BaseManager
from models.users import UserModel
from schemas.users import UserCreateSchema, UserUpdateSchema


class UserManager(BaseManager[UserModel, UserCreateSchema, UserUpdateSchema]):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session
        )
