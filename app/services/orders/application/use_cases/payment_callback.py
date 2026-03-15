from uuid import UUID
from app.services.core.models import Order, OrderStatusEnum
from app.services.exceptions import OrderNotFoundError, WrongCallbackOrderId
from app.services.orders.infrastructure.unit_of_work import UnitOfWork
from app.services.orders.presentation.schemas import PaymentCallbackSchem


class PaymentCallbackUseCase:
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work

    async def __call__(self, callback: PaymentCallbackSchem) -> dict:
        async with self._unit_of_work() as uow:
            existing = await uow.inbox.get(callback.payment_id)
            if existing:
                return {"status": "already_processed"}

            order = await uow.orders.get_order(callback.order_id)
            if not order:
                raise WrongCallbackOrderId

            new_status = OrderStatusEnum.PAID if callback.status == "succeeded" else OrderStatusEnum.CANCELLED

            await uow.orders.update_status(order.id, new_status)

            await uow.inbox.save(callback.payment_id, callback.model_dump(mode='json'))
            await uow.commit()

        return {"status": "ok"}
