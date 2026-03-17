import asyncio
from uuid import uuid4

from app.logger import logger
from app.services.catalog_service.exceptions import (
    CatalogTemporaryError,
    NotItemException,
    QuantityException,
)
from app.services.core.models import Order, OrderStatusEnum, OutboxEvent, EventTypeEnum
from app.services.notifications_service.application.tasks import (
    send_status_notification,
)
from app.services.notifications_service.infrastructure.client import NotificationClient
from app.services.orders.application.exceptions import PaymentCreationError
from app.services.orders.infrastructure.unit_of_work import UnitOfWork
from app.services.orders.presentation.schemas import CreateOrderSchem
from app.services.catalog_service.infrastructure.catalog import CatalogClient
from app.config import settings
from app.services.payment_service.dto import CreatePaymentRequestDTO
from app.services.payment_service.exceptions import PaymentTemporaryError, PaymentError
from app.services.payment_service.infrastructure.client import PaymentClient


class CreateOrderUseCase:
    """Класс для создания заказа"""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        catalog_client: CatalogClient,
        payment_client: PaymentClient,
        notification_client: NotificationClient,
    ):
        self._unit_of_work = unit_of_work
        self.catalog_client = catalog_client
        self.payment_client = payment_client
        self.payment_callback_url = (
            settings.callback_url + "/api/orders/payment-callback"
        )
        self.notification_client = notification_client

    async def __call__(self, data_order: CreateOrderSchem) -> Order:

        idempotency_key = data_order.idempotency_key

        async with self._unit_of_work() as uow:
            existing = await uow.inbox.get(idempotency_key=str(idempotency_key))
            if existing:
                response_data = existing.response_data

                order = Order(
                    id=response_data["id"],
                    user_id=response_data["user_id"],
                    items=response_data["items"],
                    quantity=response_data["quantity"],
                    status=response_data["status"],
                    status_history=response_data["status_history"],
                    created_at=response_data["created_at"],
                    updated_at=response_data["updated_at"],
                )
                return order

        try:
            catalog_item = await self.catalog_client.check_and_get(
                str(data_order.item_id), data_order.quantity
            )
        except (CatalogTemporaryError, NotItemException, QuantityException):
            raise

        items = [catalog_item]
        order = Order(
            id=uuid4(),
            user_id=str(data_order.user_id),
            items=items,
            quantity=data_order.quantity,
            status=OrderStatusEnum.NEW,
            status_history=[OrderStatusEnum.NEW],
        )

        try:
            payment_dto = CreatePaymentRequestDTO(
                order_id=str(order.id),
                amount=str(order.calculate_total()),
                callback_url=self.payment_callback_url,
                idempotency_key=idempotency_key,
            )
            logger.info(f"Sending payment callback URL: {self.payment_callback_url}")
            await self.payment_client.create_payment(payment_dto)

        except (PaymentTemporaryError, PaymentError):
            order.status = OrderStatusEnum.CANCELLED
            order.status_history.append(OrderStatusEnum.CANCELLED)

            async with self._unit_of_work() as uow:
                saved_order = await uow.orders.add(order)

                payload = {
                    "order_id": str(saved_order.id),
                    "item_id": str(saved_order.items[0].id),
                    "quantity": saved_order.quantity,
                    "idempotency_key": idempotency_key,
                }

                outbox_event = OutboxEvent(
                    event_type=EventTypeEnum.ORDER_CANCELLED,
                    payload=payload,
                    status=OrderStatusEnum.CANCELLED,
                )

                await uow.inbox.save(
                    idempotency_key, saved_order.model_dump(mode="json")
                )
                await uow.outbox.create(outbox_event)
                await uow.commit()

                asyncio.create_task(
                    send_status_notification(
                        notification_client=self.notification_client,
                        order_id=str(saved_order.id),
                        status=OrderStatusEnum.CANCELLED.value(),
                        idempotency_key=f"notification_cancelled_{saved_order.id}",
                        reason="Ошибка при попытке платежа",
                    )
                )

            raise PaymentCreationError("Ошибка при оплате")

        async with self._unit_of_work() as uow:
            saved_order = await uow.orders.add(order)
            await uow.inbox.save(
                idempotency_key=str(idempotency_key),
                response_data=saved_order.model_dump(mode="json"),
            )

            await uow.commit()
            asyncio.create_task(
                send_status_notification(
                    notification_client=self.notification_client,
                    order_id=str(saved_order.id),
                    status=OrderStatusEnum.NEW.value(),
                    idempotency_key=f"notification_new_{saved_order.id}",
                )
            )

        return saved_order
