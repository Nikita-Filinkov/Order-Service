class PaymentError(Exception):
    def __init__(
        self, status: int, message: str = "Временная ошибка у Payment Service"
    ):
        self.status = status
        self.message = message
        super().__init__(f"Payment error {status}: {message}")


class PaymentTemporaryError(PaymentError):
    """Временная ошибка (повторные попытки)"""

    def __init__(self, status: int):
        self.status = status
        super().__init__(self.status)
