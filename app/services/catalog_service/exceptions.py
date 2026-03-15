class CatalogError(Exception):
    """Базовое исключение для ошибок обращения к Catalog Service"""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}")


class CatalogTemporaryError(CatalogError):
    """Исключение для временных ошибок"""

    def __init__(
        self, status: int, message: str = "Временная ошибка у Catalog Service"
    ):
        self.status = status
        self.message = message
        super().__init__(self.status, self.message)


class QuantityException(CatalogError):
    """Исключение отрицательного количества товара"""

    status = 400

    def __init__(self, message):
        super().__init__(status=self.status, message=message)


class NotItemException(CatalogError):
    """Исключение в случае отсутствия товара"""

    status = 400
    message = "Такого товара нет в наличии"

    def __init__(self):
        super().__init__(status=self.status, message=self.message)
