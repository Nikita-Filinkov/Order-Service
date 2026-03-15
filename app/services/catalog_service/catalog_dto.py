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

    class Config:
        extra = "ignore"
