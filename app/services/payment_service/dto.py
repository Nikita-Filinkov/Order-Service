from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class CreatePaymentRequestDTO(BaseModel):
    order_id: str
    amount: str
    callback_url: str
    idempotency_key: str


class PaymentResponseDTO(BaseModel):
    id: str
    user_id: str
    order_id: str
    amount: Decimal
    status: str
    idempotency_key: str
    created_at: datetime
