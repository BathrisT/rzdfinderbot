from sqlalchemy.ext.asyncio.session import AsyncSession

from cruds.base_manager import BaseManager
from models.invoices import InvoiceModel
from schemas.invoices import InvoiceCreateSchema, InvoiceUpdateSchema


class InvoiceManager(BaseManager[InvoiceModel, InvoiceCreateSchema, InvoiceUpdateSchema]):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session
        )
