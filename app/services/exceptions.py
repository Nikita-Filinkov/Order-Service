from fastapi import HTTPException, status


class OrderException(HTTPException):
    """Базовый класс для исключений агрегатора"""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class OrderNotFoundError(OrderException):
    """Исключение если такого заказа нет"""

    status_code = status.HTTP_404_NOT_FOUND
    detail = "Такого заказа нет"


class QuantityCatalogException(OrderException):
    """Исключение если количество товара в заказе больше, чем есть на складе"""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Не достаточно товара"


class NotItemCatalogException(OrderException):
    """Исключение если такого товара нет"""

    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Такого товара нет в наличии"


class OrderNotRequestException(OrderException):
    """Исключение если сервис каталога товаров не отвечает"""

    detail = "Сервис товаров не отвечает"
