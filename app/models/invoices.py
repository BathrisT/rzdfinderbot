import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.users import UserModel


class InvoiceModel(Base):
    __tablename__ = 'invoices'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # tg id
    user_id = mapped_column(BigInteger, ForeignKey('users.id', ondelete='SET NULL'))

    is_payment_successful: Mapped[bool] = mapped_column()
    payment_status: Mapped[Optional[str]] = mapped_column()
    payment_comment: Mapped[Optional[str]] = mapped_column()

    created_at: Mapped[datetime.datetime] = mapped_column()
    updated_at: Mapped[datetime.datetime] = mapped_column()

    user: Mapped['UserModel'] = relationship()
