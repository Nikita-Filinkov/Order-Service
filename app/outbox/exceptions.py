from typing import Dict, Optional

from fastapi import HTTPException


class OutboxWorkerException(HTTPException):
    """Базовый класс для исключений агрегатора"""

    status_code = 500
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class EventsProviderError(Exception):
    """Базовое исключение для ошибок API Events Provider"""

    def __init__(self, status: int, message: str, body: Optional[Dict] = None):
        self.status = status
        self.message = message
        self.body = body or {}
        super().__init__(f"HTTP {status}: {message}")
