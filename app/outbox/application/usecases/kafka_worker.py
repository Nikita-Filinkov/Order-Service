import asyncio

from app.config import settings
from app.database import get_async_db
from app.kafka.dto import ProducePaidEventDTO
from app.kafka.infrastructure.kafka_producer import KafkaProducer
from app.logger import logger
from app.outbox.infrastructure.db_schem import OutboxTable
from app.outbox.infrastructure.repository import OutboxRepository


class KafkaOutboxWorker:
    def __init__(
        self,
        kafka_producer: KafkaProducer,
        batch_size: int = settings.OUTBOX_BATCH_SIZE,
        poll_interval: int = settings.OUTBOX_POLL_INTERVAL,
        max_retries: int = settings.OUTBOX_MAX_RETRIES,
        days_to_keep: int = settings.OUTBOX_DAYS_TO_KEEP,
    ):
        self.kafka_producer = kafka_producer
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.days_to_keep = days_to_keep
        self._running = False

    async def start(self):
        """Запускает worker"""
        self._running = True
        logger.info("KafkaOutboxWorker worker start")
        while self._running:
            try:
                await self._process_pending()
            except Exception:
                logger.exception("Outbox worker error")
            await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """Останавливает worker"""
        self._running = False

    async def _process_pending(self):
        """Процесс обработки и отправки tasks в kafka"""
        async for session in get_async_db():
            repo = OutboxRepository(session)
            pending = await repo.get_pending(limit=self.batch_size)
            if not pending:
                return
            for outbox in pending:
                await self._process_outbox_record(repo, outbox)

            count_deleted_tasks = await repo.count_deleted_tasks(
                days_to_keep=self.days_to_keep
            )
            if count_deleted_tasks > 0:
                logger.info(
                    f"Cleaned {count_deleted_tasks} older {self.days_to_keep} days"
                )

            await session.commit()
            break

    async def _process_outbox_record(self, repo: OutboxRepository, outbox: OutboxTable):
        if outbox.retry_count >= self.max_retries:
            logger.error(
                f"Outbox record {outbox.id} reached max retries, marking as failed"
            )
            await repo.mark_failed(outbox.id)
            return

        event = ProducePaidEventDTO(
            event_type=outbox.payload["event_type"],
            order_id=outbox.payload["order_id"],
            item_id=outbox.payload["item_id"],
            quantity=outbox.payload["quantity"],
            idempotency_key=outbox.payload["idempotency_key"],
        )

        event_payload = event.model_dump(mode="json")

        try:
            logger.info(f"Sending to Kafka: {event_payload}")
            await self.kafka_producer.send(settings.KAFKA_ORDER_TOPIC, event_payload)
            await repo.mark_sent(outbox.id)
            logger.info(f"Outbox record {outbox.id} sent to Kafka")
        except Exception as e:
            logger.warning(f"Failed to send outbox record {outbox.id}: {e}")
            await repo.increment_retry(outbox.id)
