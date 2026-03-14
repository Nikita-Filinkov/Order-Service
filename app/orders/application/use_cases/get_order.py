from app.orders.core.models import Order
from app.orders.exceptions import OrderNotFoundError
from app.orders.infrastructure.unit_of_work import UnitOfWork
from uuid import UUID


class GetOrderUseCase:
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work

    async def __call__(self, order_id: UUID) -> Order:
        async with self._unit_of_work() as uow:
            order = await uow.orders.get_order(order_id)
            if not order:
                raise OrderNotFoundError
            return order
