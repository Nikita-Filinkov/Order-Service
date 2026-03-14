class CatalogError(Exception):
    """Базовое исключение для ошибок Catalog Service"""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}")


class ProviderTemporaryError(CatalogError):
    """Исключение для временных ошибок"""

    def __init__(self, status: int, message: str = "Временная ошибка"):
        self.status = status
        self.message = message
        super().__init__(self.status, self.message)
