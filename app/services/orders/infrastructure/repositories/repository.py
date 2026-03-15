import uuid

from sqlalchemy import insert, select, update

from app.services.core.models import Order, Item, OrderStatusEnum
from app.services.orders.infrastructure.db_schemes.db_schemes import (
    OrderTable,
    OrderStatusHistoryTable,
)
from sqlalchemy.ext.asyncio import AsyncSession


class OrderRepository:
    """Репозиторий для работы с таблицей Order"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, order: Order) -> Order:
        """Добавление заказа в таблицу OrderTable и статуса в таблицу OrderStatusHistoryTable"""
        items_for_db = []
        for item in order.items:
            item_dict = item.model_dump()
            item_dict["price"] = str(item_dict["price"])
            items_for_db.append(item_dict)

        stmt = (
            insert(OrderTable)
            .values(
                id=order.id,
                user_id=str(order.user_id),
                items=items_for_db,
                quantity=order.quantity,
                status=order.status.value,
            )
            .returning(OrderTable)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()

        stmt_history = insert(OrderStatusHistoryTable).values(
            id=uuid.uuid4(),
            order_id=order.id,
            status=order.status,
        )
        await self.session.execute(stmt_history)

        await self.session.flush()

        order_table = result.scalar_one()
        order.created_at = order_table.created_at
        order.updated_at = order_table.updated_at
        return order

    async def get_order(self, order_id: uuid.UUID) -> Order | None:
        """Получение заказа по его UUID"""
        stmt = select(OrderTable).where(OrderTable.id == order_id)
        result = await self.session.execute(stmt)
        order_row = result.scalar_one_or_none()

        if not order_row:
            return None

        stmt_history = (
            select(OrderStatusHistoryTable)
            .where(OrderStatusHistoryTable.order_id == order_id)
            .order_by(OrderStatusHistoryTable.created_at)
        )
        result_history = await self.session.execute(stmt_history)
        history_rows = result_history.scalars().all()

        items = [Item(**item) for item in order_row.items]
        status_history = [row.status for row in history_rows]

        order = Order(
            id=order_row.id,
            user_id=order_row.user_id,
            items=items,
            quantity=order_row.quantity,
            status=order_row.status,
            status_history=status_history,
            created_at=order_row.created_at,
            updated_at=order_row.updated_at,
        )
        return order

    async def update_status(
        self, order_id: uuid.UUID, new_status: OrderStatusEnum
    ) -> None:
        """Обновление статуса заказа"""
        stmt = (
            update(OrderTable)
            .where(OrderTable.id == order_id)
            .values(status=new_status.value)
        )
        await self.session.execute(stmt)

        stmt_history = insert(OrderStatusHistoryTable).values(
            id=uuid.uuid4(),
            order_id=order_id,
            status=new_status.value,
        )
        await self.session.execute(stmt_history)
        await self.session.flush()
        # await self.session.commit()
