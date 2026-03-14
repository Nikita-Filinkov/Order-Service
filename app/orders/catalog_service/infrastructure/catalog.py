import asyncio
import logging
from pprint import pprint
from typing import Optional

from aiohttp import ClientConnectorError, ClientError, ClientSession, ClientTimeout
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.orders.catalog_service.catalog_dto import ItemDTO
from app.orders.catalog_service.exceptions import ProviderTemporaryError, CatalogError
from app.config import settings
from app.logger import logger
from app.orders.core.models import Item


class CatalogClient:
    """Асинхронный HTTP-клиент для Catalog Service"""

    MAX_RETRIES = settings.MAX_RETRIES
    BACKOFF_FACTOR = settings.BACKOFF_FACTOR
    ASYNC_RETRY_EXCEPTIONS = (
        ClientError,
        asyncio.TimeoutError,
        ConnectionError,
        ProviderTemporaryError,
    )

    RETRY_STATUSES = {408, 429, 500, 502, 503, 504}

    def __init__(self):

        self.api_key = settings.LMS_API_KEY
        self.base_url = settings.CAPASHINO_BASE_URL.rstrip("/") + "/api/catalog/items"
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
    async def get_item_by_id(self, item_id) -> Item:
        """Получение информации по товару по его id"""
        url = f"{self.base_url}/{item_id}"
        session = await self._get_session()
        try:
            async with session.get(url=url) as resp:
                status = resp.status
                if status < 300:
                    item_data: dict = await resp.json()
                    item = Item(
                        id=item_data["id"],
                        name=item_data["name"],
                        price=item_data["price"]
                    )
                    return item

                if status in self.RETRY_STATUSES:
                    logger.warning(
                        f"Временная ошибка при получении товара {item_id}, статус {status}"
                    )
                    raise ProviderTemporaryError(status=status)

                error_message = f"Ошибка каталога: статус {status}, причина {resp.reason}"
                logger.error(error_message)
                raise CatalogError(status=status, message=error_message)

        except (ClientError, asyncio.TimeoutError, ConnectionError) as e:
            message = "Ошибка при получить информацию по товару из Catalog Service"
            logger.warning(
                message, extra={"tries": self.MAX_RETRIES, "error": str(e)}
            )
            raise ProviderTemporaryError(status=0, message=message)

    async def check_availability(self):
        """Проверка доступности API"""
        session = await self._get_session()
        try:
            async with session.get(self.base_url) as response:
                pprint(await response.json())
                status = response.status
                if status == 200:
                    logger.info("Catalog Service доступен")
                    return {"status": "ok"}
                return {"status": "fault"}
        except (ClientConnectorError, asyncio.TimeoutError):
            logger.error("Catalog Service не доступен")
            raise

    async def check_available_qty(self, item_id, quantity) -> bool:
        """Проверка, что такое количество есть на складе"""
        item = await self.get_item_by_id(item_id=item_id)
        return quantity <= item.available_qty

    async def close(self):
        """Закрытие сессии"""
        if self._session:
            await self._session.close()
            self._session = None
