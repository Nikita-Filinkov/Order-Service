from datetime import datetime, timedelta
from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.outbox.infrastructure.db_schemas.db_schem import Outbox, OutboxStatus


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event_type: str, payload: dict) -> Outbox:
        """Создает новую запись в OutboxRepository"""
        outbox = Outbox(event_type=event_type, payload=payload)
        self.session.add(outbox)
        await self.session.flush()
        return outbox

    async def get_pending(self, limit: int = 10) -> Sequence[Outbox]:
        """Получает tasks, которые требуют обработки"""
        result = await self.session.execute(
            select(Outbox)
            .where(Outbox.status == OutboxStatus.PENDING)
            .order_by(Outbox.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return result.scalars().all()

    async def mark_sent(self, outbox_id: UUID) -> None:
        """Ставит отметку об отправке"""
        await self.session.execute(
            update(Outbox)
            .where(Outbox.id == outbox_id)
            .values(status=OutboxStatus.SENT)
        )
        await self.session.flush()

    async def increment_retry(self, outbox_id: UUID) -> None:
        """Увеличивает количество проваленных попыток"""
        await self.session.execute(
            update(Outbox)
            .where(Outbox.id == outbox_id)
            .values(retry_count=Outbox.retry_count + 1, status=OutboxStatus.PENDING)
        )
        await self.session.flush()

    async def mark_failed(self, outbox_id: UUID) -> None:
        """Ставит отметку о провале"""
        await self.session.execute(
            update(Outbox)
            .where(Outbox.id == outbox_id)
            .values(status=OutboxStatus.FAILED)
        )
        await self.session.flush()

    async def count_deleted_tasks(self, days_to_keep: int = 7) -> int:
        """Удаляет отправленные сообщения старше days_to_keep дней"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        count_query = (
            select(func.count())
            .select_from(Outbox)
            .where(Outbox.status == OutboxStatus.SENT, Outbox.created_at < cutoff_date)
        )
        to_delete = await self.session.scalar(count_query) or 0

        if to_delete > 0:
            await self.session.execute(
                delete(Outbox)
                .where(Outbox.status == OutboxStatus.SENT)
                .where(Outbox.created_at < cutoff_date)
            )
            await self.session.flush()

        return to_delete
