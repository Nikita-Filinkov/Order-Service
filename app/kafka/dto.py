from uuid import UUID

from pydantic import BaseModel


class ProducePaidEventDTO(BaseModel):
    """Событие для публикации оплаты"""

    event_type: str
    order_id: str
    item_id: str
    quantity: int
    idempotency_key: UUID
