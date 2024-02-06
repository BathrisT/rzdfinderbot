import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.trackings import TrackingModel
    from models.users import UserModel


class TrackingNotificationModel(Base):
    __tablename__ = 'tracking_notifications'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # tg id

    tracking_id = mapped_column(BigInteger, ForeignKey('trackings.id', ondelete='CASCADE'))
    user_id = mapped_column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'))
    train_number: Mapped[Optional[str]] = mapped_column()  # TODO: мб удалить

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)

    tracking: Mapped['TrackingModel'] = relationship()
    user: Mapped['UserModel'] = relationship()
