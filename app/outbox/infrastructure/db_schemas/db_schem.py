import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OutboxStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus), default=OutboxStatus.PENDING, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )
    retry_count: Mapped[int] = mapped_column(default=0)

    __table_args__ = (Index("ix_outbox_status_created", "status", "created_at"),)
