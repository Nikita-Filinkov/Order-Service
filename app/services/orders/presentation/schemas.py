from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.services.core.models import OrderStatusEnum, Order


class CreateOrderSchem(BaseModel):
    user_id: str
    quantity: int
    item_id: UUID
    idempotency_key: str


class ResponseOrderSchem(BaseModel):
    id: UUID
    user_id: str
    quantity: int
    item_id: UUID
    status: OrderStatusEnum
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, order: Order) -> "ResponseOrderSchem":
        item = order.items[0] if order.items else None
        return cls(
            id=order.id,
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=item.id if item else None,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


class PaymentCallbackSchem(BaseModel):
    payment_id: str
    order_id: UUID
    status: str  # "succeeded" или "failed"
    amount: Decimal
    error_message: Optional[str] = None
