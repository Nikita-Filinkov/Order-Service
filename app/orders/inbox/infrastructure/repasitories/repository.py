from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.orders.inbox.infrastructure.db_schemes.db_schemes import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, idempotency_key: str) -> IdempotencyKey | None:
        query = select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save(
        self, idempotency_key: str, response_data: dict, ttl_days: int = 7
    ) -> IdempotencyKey:
        idem = IdempotencyKey(
            key=idempotency_key,
            response_data=response_data,
            expires_at=datetime.now() + timedelta(days=ttl_days),
        )
        self.session.add(idem)
        await self.session.flush()
        return idem

    async def delete_expired_key(self):
        now = datetime.now()
        query = delete(IdempotencyKey).where(IdempotencyKey.expires_at <= now)
        result = await self.session.execute(query)
        return result
