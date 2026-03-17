import asyncio
import logging
from typing import Optional
from aiohttp import ClientSession, ClientTimeout, ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import settings
from app.logger import logger
from app.services.notifications_service.dto import (
    SendNotificationRequestDTO,
    NotificationResponseDTO,
)
from app.services.notifications_service.exceptions import (
    BadRequestNotificationException,
    WrongApiKeyNotificationException,
    ExistsNotificationException,
    NotificationServiceErrorException,
    UnexpectedNotificationError,
    NotificationTemporaryError,
)


class NotificationClient:
    """Асинхронный HTTP-клиент для Notifications Service"""

    MAX_RETRIES = settings.MAX_RETRIES
    BACKOFF_FACTOR = settings.BACKOFF_FACTOR
    ASYNC_RETRY_EXCEPTIONS = (
        ClientError,
        asyncio.TimeoutError,
        ConnectionError,
        NotificationTemporaryError,
    )

    RETRY_STATUSES = {408, 429, 500, 502, 503, 504}

    def __init__(self):
        self.api_key = settings.LMS_API_KEY
        self.base_url = settings.CAPASHINO_BASE_URL.rstrip("/") + "/api/notifications"
        self.headers = {"x-api-key": self.api_key}
        self._session: Optional[ClientSession] = None

    async def _get_session(self) -> ClientSession:
        """Создаёт или возвращает существующую сессию"""
        if self._session is None:
            timeout = ClientTimeout(total=10, connect=5)
            self._session = ClientSession(
                headers=self.headers, raise_for_status=False, timeout=timeout
            )
        return self._session

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=BACKOFF_FACTOR, min=1, max=5),
        retry=retry_if_exception_type(ASYNC_RETRY_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def send_notification(
        self, dto: SendNotificationRequestDTO
    ) -> NotificationResponseDTO:
        session = await self._get_session()
        try:
            async with session.post(
                self.base_url, json=dto.model_dump(mode="json")
            ) as resp:
                status = resp.status
                response_text = await resp.text()

                if status < 300:
                    data = await resp.json()
                    return NotificationResponseDTO(**data)
                elif status == 400:
                    logger.error(f"Dont valid body: {status} - {response_text}")
                    raise BadRequestNotificationException
                elif status == 401:
                    logger.error(f"invalid X-API-Key: {status} - {await resp.text()}")
                    raise WrongApiKeyNotificationException

                elif status == 409:
                    logger.error(
                        f"There is already a notification with this idempotency_key: {status} - {await resp.text()}"
                    )
                    raise ExistsNotificationException

                elif status >= 500:
                    logger.error(
                        f"Error on the notification service side: {status} - {await resp.text()}"
                    )
                    raise NotificationServiceErrorException

                else:
                    logger.error(f"Capashino error: {status} - {await resp.text()}")
                    message = "An unexpected error occurred while sending a message to the notification service"
                    raise UnexpectedNotificationError(status, message)

            if status in self.RETRY_STATUSES:
                raise NotificationTemporaryError(status=status, message=response_text)

        except (ClientError, asyncio.TimeoutError) as e:
            raise NotificationTemporaryError(status=0, message=str(e))

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
