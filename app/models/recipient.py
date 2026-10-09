"""SQLAlchemy model for certificate recipients."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecipientStatus(str, enum.Enum):
    """Possible statuses for a recipient."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Recipient(Base):
    """Represents an individual certificate recipient within a job."""

    __tablename__ = "recipients"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[RecipientStatus] = mapped_column(
        Enum(RecipientStatus), default=RecipientStatus.PENDING, nullable=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    job: Mapped["GenerationJob"] = relationship(
        "GenerationJob", back_populates="recipients"
    )
    certificate: Mapped["Certificate | None"] = relationship(
        "Certificate", back_populates="recipient", uselist=False
    )


from app.models.job import GenerationJob  # noqa: E402, F401
from app.models.certificate import Certificate  # noqa: E402, F401
