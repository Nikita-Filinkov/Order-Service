from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel


class OrderStatusEnum(StrEnum):
    """Статусы заказов"""
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class Item(BaseModel):
    """Value Object - товар в заказе"""

    id: str
    name: str
    price: Decimal


class Order(BaseModel):
    """Entity - заказ"""

    id: str
    user_id: str
    items: list[Item]
    amount: Decimal
    status: OrderStatusEnum
    status_history: list[OrderStatusEnum]

    def can_be_cancelled(self) -> bool:
        """Бизнес-правило: можно отменить только NEW или PAID"""
        return self.status in (OrderStatusEnum.NEW, OrderStatusEnum.PAID)

    def calculate_total(self) -> Decimal:
        """Бизнес-логика: расчет суммы"""
        return sum(
            (item.price for item in self.items),
            Decimal('0')
        )


class EventTypeEnum(StrEnum):
    ORDER_CREATED = "ORDER.CREATED"
    ORDER_PAID = "ORDER.PAID"
    ORDER_SHIPPED = "ORDER.SHIPPED"


class OutboxEventStatus(BaseModel):
    """Статусы event in Outbox"""
    PENDING = "PENDING"
    SENT = "SENT"
    FAULT = "FAULT"


class OutboxEvent(BaseModel):
    """Событие для публикации"""
    id: str
    event_type: EventTypeEnum
    payload: dict
    status: OutboxEventStatus
    created_at: datetime
