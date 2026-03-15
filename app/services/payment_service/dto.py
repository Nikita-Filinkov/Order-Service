from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime


class CreatePaymentRequest(BaseModel):
    order_id: str
    amount: Decimal
    callback_url: str
    idempotency_key: str


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    order_id: str
    amount: Decimal
    status: str
    idempotency_key: str
    created_at: datetime
