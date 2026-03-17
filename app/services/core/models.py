from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class OrderStatusEnum(StrEnum):
    """Статусы заказов"""

    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class Item(BaseModel):
    """Value Object - товар в заказе"""

    id: UUID
    name: str
    price: Decimal


class Order(BaseModel):
    """Entity - заказ"""

    id: UUID
    user_id: str
    items: list[Item]
    quantity: int
    status: OrderStatusEnum
    status_history: list[OrderStatusEnum]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def can_be_cancelled(self) -> bool:
        """Бизнес-правило: можно отменить только NEW или PAID"""
        return self.status in (OrderStatusEnum.NEW, OrderStatusEnum.PAID)

    def calculate_total(self) -> Decimal:
        """Бизнес-логика: расчет суммы"""
        return sum((item.price for item in self.items), Decimal("0"))


class EventTypeEnum(StrEnum):
    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_SHIPPED = "order.shipped"
    ORDER_CANCELLED = "order.cancelled"


class OutboxEventStatus(StrEnum):
    """Статусы event in Outbox"""

    PENDING = "PENDING"
    SENT = "SENT"
    FAULT = "FAULT"
    PROCESSED = "PROCESSED"


class OutboxEvent(BaseModel):
    """Событие для публикации"""

    event_type: EventTypeEnum
    payload: dict
    status: OutboxEventStatus
