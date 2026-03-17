import hashlib
import json
from uuid import UUID
from app.services.core.models import OrderStatusEnum
from app.services.exceptions import OrderNotFoundError
from app.services.orders.infrastructure.unit_of_work import UnitOfWork


class HandleShippingEventUseCase:
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work

    async def execute(self, event: dict):
        event_type = event.get("event_type")
        order_id = UUID(event["order_id"])

        if event_type == "order.shipped":
            idempotency_key = f"shipped_{event['shipment_id']}"
        elif event_type == "order.cancelled":
            payload_str = json.dumps(event, sort_keys=True)
            idempotency_key = (
                f"cancelled_{hashlib.sha256(payload_str.encode()).hexdigest()}"
            )
        else:
            return

        async with self._unit_of_work() as uow:
            existing = await uow.inbox.get(idempotency_key)
            if not existing:
                return
            order = await uow.orders.get_order(order_id)
            if not order:
                raise OrderNotFoundError

            if event_type == "order.shipped":
                new_status = OrderStatusEnum.SHIPPED
            elif event_type == "order.cancelled":
                new_status = OrderStatusEnum.CANCELLED

            await uow.orders.update_status(order.id, new_status)
            await uow.commit()
