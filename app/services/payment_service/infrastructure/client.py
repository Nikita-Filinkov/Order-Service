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
from app.services.payment_service.dto import CreatePaymentRequest, PaymentResponse
from app.services.payment_service.exceptions import PaymentTemporaryError, PaymentError


class PaymentClient:
    """Асинхронный HTTP-клиент для Payment Service"""

    MAX_RETRIES = settings.MAX_RETRIES
    BACKOFF_FACTOR = settings.BACKOFF_FACTOR
    ASYNC_RETRY_EXCEPTIONS = (
        ClientError,
        asyncio.TimeoutError,
        ConnectionError,
        PaymentTemporaryError,
    )

    RETRY_STATUSES = {408, 429, 500, 502, 503, 504}

    def __init__(self):
        self.api_key = settings.PAYMENT_API_KEY
        self.base_url = settings.PAYMENT_BASE_URL.rstrip("/")
        self.headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
        self._session: Optional[ClientSession] = None

    async def _get_session(self) -> ClientSession:
        if self._session is None:
            timeout = ClientTimeout(total=10, connect=5)
            self._session = ClientSession(headers=self.headers, timeout=timeout)
        return self._session

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=BACKOFF_FACTOR, min=1, max=5),
        retry=retry_if_exception_type(ASYNC_RETRY_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def create_payment(self, dto: CreatePaymentRequest) -> PaymentResponse:
        url = f"{self.base_url}/api/payments"
        session = await self._get_session()
        try:
            async with session.post(url, json=dto.model_dump(mode="json")) as resp:
                status = resp.status
                if status < 300:
                    data = await resp.json()
                    return PaymentResponse(**data)
                if status in self.RETRY_STATUSES:
                    raise PaymentTemporaryError(status=status)
                raise PaymentError(status=status, message=await resp.text())
        except (ClientError, asyncio.TimeoutError):
            raise PaymentTemporaryError(status=0)

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None
