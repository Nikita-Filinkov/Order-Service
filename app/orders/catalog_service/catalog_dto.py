from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ItemDTO(BaseModel):
    """DTO - Item"""

    id: UUID
    name: str
    price: Decimal
    available_qty: int
    created_at: datetime
    updated_at: datetime

    class Config:
        extra = "ignore"


