from uuid import uuid4

from app.logger import logger
from app.services.core.models import (
    OrderStatusEnum,
    EventTypeEnum,
    OutboxEvent,
    OutboxEventStatus,
)
from app.services.exceptions import WrongCallbackOrderId
from app.services.orders.infrastructure.unit_of_work import UnitOfWork
from app.services.orders.presentation.schemas import PaymentCallbackSchem


class PaymentCallbackUseCase:
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work

    async def __call__(self, callback: PaymentCallbackSchem) -> dict:
        async with self._unit_of_work() as uow:
            existing = await uow.inbox.get(callback.payment_id)
            if existing:
                return {"in_progres": f"{existing.response_data}"}

            order = await uow.orders.get_order(callback.order_id)
            if not order:
                raise WrongCallbackOrderId

            new_status = (
                OrderStatusEnum.PAID
                if callback.status == "succeeded"
                else OrderStatusEnum.CANCELLED
            )

            payload = {
                "order_id": str(order.id),
                "item_id": str(order.items[0].id),
                "quantity": order.quantity,
                "idempotency_key": str(uuid4()),
            }

            if new_status == OrderStatusEnum.PAID:
                event_type = EventTypeEnum.ORDER_PAID
                outbox_event_status = OutboxEventStatus.PENDING
            else:
                event_type = EventTypeEnum.ORDER_CANCELLED
                outbox_event_status = OutboxEventStatus.PROCESSED

            outbox_event = OutboxEvent(
                event_type=event_type,
                payload=payload,
                status=outbox_event_status,
            )
            logger.info(f"Created new outbox_event: {outbox_event.model_dump()}")
            await uow.outbox.create(outbox_event)

            await uow.orders.update_status(order.id, new_status)

            await uow.inbox.save(callback.payment_id, callback.model_dump(mode="json"))
            await uow.commit()

        return {"new_status": f"{new_status}"}
