from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.orders.infrastructure.repositories.repository import OrderRepository
from app.inbox.infrastructure.repository import IdempotencyRepository


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    @asynccontextmanager
    async def __call__(self):
        async with self._session_factory() as session:
            try:
                yield _UnitOfWorkImplementation(session)
                # Если commit не вызван - откатываем
                await session.rollback()
            except Exception:
                await session.rollback()
                raise


class _UnitOfWorkImplementation:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._order_repo = OrderRepository(session)
        self._idem_repo = IdempotencyRepository(session)
        # self._outbox_repo = OutboxRepository(session)

    @property
    def orders(self) -> OrderRepository:
        return self._order_repo

    @property
    def inbox(self) -> IdempotencyRepository:
        return self._idem_repo

    async def commit(self):
        await self._session.commit()
