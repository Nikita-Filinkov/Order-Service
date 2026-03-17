from datetime import datetime, timedelta
from typing import Sequence
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.logger import logger
from app.outbox.infrastructure.db_schem import OutboxTable, OutboxStatus
from app.services.core.models import OutboxEvent


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, outbox_event: OutboxEvent) -> OutboxTable:
        """Создает новую запись в OutboxRepository"""
        outbox = OutboxTable(
            event_type=outbox_event.event_type, payload=outbox_event.payload
        )
        self.session.add(outbox)
        await self.session.flush()
        logger.info(f"New entry outbox: {outbox.event_type}, status{outbox.status}")
        return outbox

    async def get_pending(self, limit: int = 10) -> Sequence[OutboxTable]:
        """Получает tasks, которые требуют обработки"""
        result = await self.session.execute(
            select(OutboxTable)
            .where(OutboxTable.status == OutboxStatus.PENDING)
            .order_by(OutboxTable.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return result.scalars().all()

    async def mark_sent(self, outbox_id: UUID) -> None:
        """Ставит отметку об отправке"""
        await self.session.execute(
            update(OutboxTable)
            .where(OutboxTable.id == outbox_id)
            .values(status=OutboxStatus.SENT)
        )
        await self.session.flush()

    async def increment_retry(self, outbox_id: UUID) -> None:
        """Увеличивает количество проваленных попыток"""
        await self.session.execute(
            update(OutboxTable)
            .where(OutboxTable.id == outbox_id)
            .values(
                retry_count=OutboxTable.retry_count + 1, status=OutboxStatus.PENDING
            )
        )
        await self.session.flush()

    async def mark_failed(self, outbox_id: UUID) -> None:
        """Ставит отметку о провале"""
        await self.session.execute(
            update(OutboxTable)
            .where(OutboxTable.id == outbox_id)
            .values(status=OutboxStatus.FAILED)
        )
        await self.session.flush()

    async def count_deleted_tasks(self, days_to_keep: int = 7) -> int:
        """Удаляет отправленные сообщения старше days_to_keep дней"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        count_query = (
            select(func.count())
            .select_from(OutboxTable)
            .where(
                OutboxTable.status == OutboxStatus.SENT,
                OutboxTable.created_at < cutoff_date,
            )
        )
        to_delete = await self.session.scalar(count_query) or 0

        if to_delete > 0:
            await self.session.execute(
                delete(OutboxTable)
                .where(OutboxTable.status == OutboxStatus.SENT)
                .where(OutboxTable.created_at < cutoff_date)
            )
            await self.session.flush()

        return to_delete
