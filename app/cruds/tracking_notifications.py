from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from cruds.base_manager import BaseManager
from models.tracking_notifications import TrackingNotificationModel
from schemas.tracking_notifications import TrackingNotificationCreateSchema, TrackingNotificationUpdateSchema


class TrackingNotificationManager(
    BaseManager[TrackingNotificationModel, TrackingNotificationCreateSchema, TrackingNotificationUpdateSchema]
):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session
        )

    async def get_last_notification_by_tracking_id(self, tracking_id: int):
        query = select(TrackingNotificationModel).where(
            TrackingNotificationModel.tracking_id == tracking_id
        ).order_by(TrackingNotificationModel.created_at.desc())
        return await self._session.scalar(query)
