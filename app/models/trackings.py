import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, ForeignKey, DECIMAL

from database import Base

if TYPE_CHECKING:
    from models.users import UserModel


class TrackingModel(Base):
    __tablename__ = 'trackings'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # tg id
    user_id = mapped_column(BigInteger, ForeignKey('users.id', ondelete='CASCADE'))

    from_city_name: Mapped[str] = mapped_column()
    from_city_id: Mapped[str] = mapped_column()
    from_city_site_code: Mapped[str] = mapped_column()

    to_city_name: Mapped[str] = mapped_column()
    to_city_id: Mapped[str] = mapped_column()
    to_city_site_code: Mapped[str] = mapped_column()

    date: Mapped[datetime.date] = mapped_column()
    max_price: Mapped[Optional[int]] = mapped_column(DECIMAL, nullable=True)

    # Флаги фильтрации по св, сид
    sw_enabled: Mapped[bool] = mapped_column(server_default='TRUE')
    sid_enabled: Mapped[bool] = mapped_column(server_default='TRUE')

    # Флаги фильтрации по плацкартным местам
    plaz_seats_plaz_down_enabled: Mapped[bool] = mapped_column(server_default='TRUE')
    plaz_seats_plaz_up_enabled: Mapped[bool] = mapped_column(server_default='TRUE')
    plaz_side_down_enabled: Mapped[bool] = mapped_column(server_default='TRUE')
    plaz_side_up_enabled: Mapped[bool] = mapped_column(server_default='TRUE')

    # Флаги фильтрации по купе местам
    cupe_up_enabled: Mapped[bool] = mapped_column(server_default='TRUE')
    cupe_down_enabled: Mapped[bool] = mapped_column(server_default='TRUE')

    first_notification_sent_at: Mapped[Optional[datetime.datetime]] = mapped_column()

    is_finished: Mapped[bool] = mapped_column(server_default='FALSE')
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column()

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)

    user: Mapped['UserModel'] = relationship()
