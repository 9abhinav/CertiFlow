"""Models package — import all models so SQLAlchemy registers them."""

from app.models.job import GenerationJob, JobStatus
from app.models.recipient import Recipient, RecipientStatus
from app.models.certificate import Certificate, CertificateStatus

__all__ = [
    "GenerationJob",
    "JobStatus",
    "Recipient",
    "RecipientStatus",
    "Certificate",
    "CertificateStatus",
]
