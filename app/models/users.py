import datetime
from typing import Optional

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)  # tg id

    first_name: Mapped[str] = mapped_column()  # имя в тг
    last_name: Mapped[Optional[str]] = mapped_column()  # фамилия в тг
    username: Mapped[Optional[str]] = mapped_column()  # username в тг
    is_banned: Mapped[bool] = mapped_column(default=False)  # забанен ли в боте

    subscription_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column()  # Когда истекает подписка
    last_expire_notification_sent_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        server_default='FALSE'
    )  # Дата последней нотификаций об истечении подписки

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
