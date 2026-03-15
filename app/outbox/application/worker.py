import asyncio

from app.aggregator.tickets.outbox.models import Outbox
from app.aggregator.tickets.outbox.repository import OutboxRepository
from app.database import get_async_db
from app.logger import logger
from app.notifications.capashino_client import CapashinoClient
from app.notifications.exceptions import (
    BadRequestNotificationException,
    ExistsNotificationException,
    NotificationServiceErrorException,
    UnexpectedNotificationError,
    WrongApiKeyNotificationException,
)


class OutboxWorker:
    def __init__(
        self,
        capashino_client: CapashinoClient,
        batch_size: int = 10,
        poll_interval: int = 5,
        max_retries: int = 5,
        days_to_keep: int = 7,
    ):

        self.capashino_client = capashino_client
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.days_to_keep = days_to_keep
        self._running = False

    async def start(self):
        """Запускает worker"""
        self._running = True
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
        """Процесс обработки и отправки tasks в сервис уведомлений"""
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
                    f"Отчищено {count_deleted_tasks} сообщений старше {self.days_to_keep} дней"
                )

            await session.commit()
            break

    async def _process_outbox_record(self, repo: OutboxRepository, outbox: Outbox):
        """Обрабатывает одну запись outbox и отправляет в сервис уведомлений"""
        ticket = str(outbox.payload.get("ticket_id", "unknown"))

        if outbox.retry_count >= self.max_retries:
            extra = {
                "ticket": ticket,
                "status": outbox.status,
                "max_retry": outbox.retry_count,
            }
            logger.error(
                f"У записи {outbox.id} было достигнуто максимальное количество попыток",
                extra=extra,
            )
            await repo.mark_failed(outbox.id)
            return

        message = f"Вы успешно зарегистрированы на мероприятие (билет {ticket})"

        try:
            success = await self.capashino_client.send_notification(
                message=message,
                reference_id=ticket,
                idempotency_key=f"outbox_{outbox.id}",
            )

            if success:
                await repo.mark_sent(outbox.id)
                logger.info(f"Outbox record {outbox.id} sent")

        except (NotificationServiceErrorException, UnexpectedNotificationError):
            await repo.increment_retry(outbox.id)
            logger.warning(
                f"Outbox record {outbox.id} send failed, retry {outbox.retry_count + 1}"
            )

        except (
            ExistsNotificationException,
            WrongApiKeyNotificationException,
            BadRequestNotificationException,
        ):
            logger.warning(f"Ошибка при отправке уведомления для записи {outbox.id}")
            await repo.mark_failed(outbox.id)
