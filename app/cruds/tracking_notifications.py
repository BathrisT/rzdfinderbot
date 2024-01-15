from sqlalchemy.ext.asyncio.session import AsyncSession

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
