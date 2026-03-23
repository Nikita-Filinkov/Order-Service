import asyncio
import hashlib
import json
from uuid import UUID

from app.metics.metrics import orders_shipped_total
from app.services.core.models import OrderStatusEnum
from app.services.exceptions import OrderNotFoundError
from app.services.notifications_service.application.tasks import (
    send_status_notification,
)
from app.services.notifications_service.infrastructure.client import NotificationClient
from app.services.orders.infrastructure.unit_of_work import UnitOfWork


class HandleShippingEventUseCase:
    """Класс для обработки событий от Shipping Service"""

    def __init__(
        self, unit_of_work: UnitOfWork, notification_client: NotificationClient
    ):
        self._unit_of_work = unit_of_work
        self.notification_client = notification_client

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
            if existing:
                return
            order = await uow.orders.get_order(order_id)
            if not order:
                raise OrderNotFoundError

            reason = event.get("reason")
            if event_type == "order.shipped":
                new_status = OrderStatusEnum.SHIPPED
            elif event_type == "order.cancelled":
                new_status = OrderStatusEnum.CANCELLED

            await uow.orders.update_status(order.id, new_status)
            await uow.inbox.save(idempotency_key, response_data={})

            await uow.commit()
            if new_status == OrderStatusEnum.SHIPPED:
                orders_shipped_total.inc()

            asyncio.create_task(
                send_status_notification(
                    notification_client=self.notification_client,
                    order_id=str(order.id),
                    status=new_status,
                    idempotency_key=f"notification_{new_status}_{idempotency_key}",
                    reason=reason,
                )
            )
