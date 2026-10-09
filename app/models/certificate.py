"""SQLAlchemy model for generated certificates."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CertificateStatus(str, enum.Enum):
    """Possible statuses for a certificate."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class Certificate(Base):
    """Represents a generated certificate PDF."""

    __tablename__ = "certificates"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipients.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[CertificateStatus] = mapped_column(
        Enum(CertificateStatus), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    job: Mapped["GenerationJob"] = relationship(
        "GenerationJob", back_populates="certificates"
    )
    recipient: Mapped["Recipient"] = relationship(
        "Recipient", back_populates="certificate"
    )


from app.models.job import GenerationJob  # noqa: E402, F401
from app.models.recipient import Recipient  # noqa: E402, F401
