from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select, not_, update
from sqlalchemy.orm import selectinload

from cruds.base_manager import BaseManager
from models.trackings import TrackingModel
from schemas.trackings import TrackingCreateSchema, TrackingUpdateSchema


class TrackingManager(BaseManager[TrackingModel, TrackingCreateSchema, TrackingUpdateSchema]):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session
        )

    async def get_user_trackings(self, user_id: int, only_active=True) -> list[TrackingModel]:
        filters = [TrackingModel.user_id == user_id]
        if only_active:
            filters.append(not_(TrackingModel.is_finished))
        query = select(TrackingModel).where(*filters).order_by(TrackingModel.created_at.desc())
        return (await self._session.scalars(query)).all()

    async def get_all_tracking(self, only_active=True) -> list[TrackingModel]:
        query = select(TrackingModel)
        if only_active:
            query = query.where(not_(TrackingModel.is_finished))
        query = query.order_by(TrackingModel.created_at.desc()).options(selectinload(TrackingModel.user))
        return (await self._session.scalars(query)).all()

    async def clear_first_notification_date(self, tracking_id: int) -> None:
        query = update(TrackingModel).where(TrackingModel.id == tracking_id).values(first_notification_sent_at=None)
        await self._session.execute(query)

    async def get_user_trackings_with_not_answered_notification(self, user_id: int):
        filters = [
            TrackingModel.user_id == user_id,
            not_(TrackingModel.is_finished),
            TrackingModel.first_notification_sent_at != None
        ]
        query = select(TrackingModel).where(*filters).order_by(TrackingModel.created_at.desc()).options(selectinload(TrackingModel.user))
        return (await self._session.scalars(query)).all()
