from fastapi import HTTPException, status


class IdempotencyError(HTTPException):
    """Базовый класс ошибок идемпотентности"""

    status_code = status.HTTP_409_CONFLICT
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class DontConsistentData(IdempotencyError):
    detail = (
        "Ключ идемпотентности совпадает, но входные и сохранённые данные отличаются"
    )


class IdemDontHaveTicket(IdempotencyError):
    detail = "Нет билета в таблице идемпотентности"
