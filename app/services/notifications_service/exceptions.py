class NotificationServiceError(Exception):
    """Базовое исключение для ошибок API Events Provider"""

    status: int = 400
    message: str = ""

    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f"HTTP {status}: {message}")


class NotificationTemporaryError(NotificationServiceError):
    """Исключение для временных ошибок"""

    pass


class BadRequestNotificationException(NotificationServiceError):
    """Не верные переданные данные"""

    status: int = 400
    message: str = "Невалидное тело"


class WrongApiKeyNotificationException(NotificationServiceError):
    """Исключения выбрасывается в случае неавторизованного запроса"""

    status: int = 401
    message: str = "Нет/неверный X-API-Key"


class ExistsNotificationException(NotificationServiceError):
    """Исключения выбрасывается если уведомление уже существует"""

    status: int = 409
    message: str = "Уведомление уже существует"


class NotificationServiceErrorException(NotificationServiceError):
    """Исключения выбрасывается, когда ошибка на сервере уведомлений"""

    status: int = 500
    message: str = "Ошибка на стороне сервиса уведомлений"


class UnexpectedNotificationError(NotificationServiceError):
    message = "Неожиданная ошибка при отправке сообщения в сервис нотификации"
