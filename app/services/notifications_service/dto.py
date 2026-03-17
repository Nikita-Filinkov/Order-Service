from pydantic import BaseModel
from datetime import datetime


class SendNotificationRequestDTO(BaseModel):
    message: str
    reference_id: str
    idempotency_key: str


class NotificationResponseDTO(BaseModel):
    id: str
    user_id: str
    message: str
    reference_id: str
    created_at: datetime
