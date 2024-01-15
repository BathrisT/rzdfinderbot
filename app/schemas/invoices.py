from typing import Optional

from pydantic import BaseModel

class InvoiceCreateSchema(BaseModel):
    user_id: int

    is_payment_successful: bool = False
    payment_status: Optional[str] = None
    payment_comment: Optional[str] = None


class InvoiceUpdateSchema(BaseModel):
    is_payment_successful: Optional[bool] = None
    payment_status: Optional[str] = None
    payment_comment: Optional[str] = None
