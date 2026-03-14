from fastapi import HTTPException, status


class OrderException(HTTPException):
    """Базовый класс для исключений агрегатора"""

    status_code = 500
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class OrderNotFoundError(OrderException):
    status_code = 404
    detail = "Такого заказа нет"
