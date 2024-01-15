from typing import Optional

from database import Base


class InvoiceCreateSchema(Base):
    user_id: int

    is_payment_successful: bool = False
    payment_status: Optional[str]
    payment_comment: Optional[str]


class InvoiceUpdateSchema(Base):
    is_payment_successful: Optional[bool]
    payment_status: Optional[str]
    payment_comment: Optional[str]
