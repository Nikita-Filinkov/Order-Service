from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.orders.core.models import OrderStatusEnum


class OrderDTO(BaseModel):
    id: UUID
    user_id: int
    quantity: int
    item_id: UUID
    status: OrderStatusEnum
