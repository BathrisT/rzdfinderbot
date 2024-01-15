from sqlalchemy.ext.asyncio.session import AsyncSession

from cruds.base_manager import BaseManager
from models.trackings import TrackingModel
from schemas.trackings import TrackingCreateSchema, TrackingUpdateSchema


class TrackingManager(BaseManager[TrackingModel, TrackingCreateSchema, TrackingUpdateSchema]):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session
        )
