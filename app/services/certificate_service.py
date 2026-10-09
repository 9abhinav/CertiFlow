"""Certificate generation service.

Handles the logic of generating a single certificate:
creating the PDF, persisting the Certificate record,
and updating the Recipient status.
"""

import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.certificate import Certificate, CertificateStatus
from app.models.recipient import Recipient, RecipientStatus
from app.services.pdf_service import PDFService


class CertificateService:
    """Generates a single certificate for one recipient."""

    def __init__(self) -> None:
        self.pdf_service = PDFService()

    def generate_certificate(
        self,
        db: Session,
        *,
        recipient: Recipient,
        organization_name: str,
        certificate_title: str,
        event_name: str,
        issue_date: date,
    ) -> Certificate:
        """Generate a certificate for a single recipient.

        Creates the PDF file, saves a Certificate record, and
        updates the Recipient status. On failure, marks both
        records as FAILED and stores the error message.

        Args:
            db: Active SQLAlchemy session.
            recipient: The Recipient ORM object.
            organization_name: Issuing organization.
            certificate_title: Title on the certificate.
            event_name: Event or course name.
            issue_date: Certificate issue date.

        Returns:
            The Certificate ORM object (SUCCESS or FAILED).
        """
        cert_id = uuid.uuid4()

        try:
            file_path, file_name = self.pdf_service.generate_pdf(
                certificate_id=str(cert_id),
                organization_name=organization_name,
                certificate_title=certificate_title,
                recipient_name=recipient.name,
                event_name=event_name,
                issue_date=issue_date,
            )

            certificate = Certificate(
                id=cert_id,
                job_id=recipient.job_id,
                recipient_id=recipient.id,
                file_path=file_path,
                file_name=file_name,
                status=CertificateStatus.SUCCESS,
            )
            recipient.status = RecipientStatus.SUCCESS
            recipient.processed_at = datetime.utcnow()

            db.add(certificate)
            db.flush()

            logger.info(
                "Certificate generated for %s (%s)", recipient.name, recipient.email
            )
            return certificate

        except Exception as e:
            logger.error(
                "Certificate generation failed for %s: %s", recipient.name, str(e)
            )
            certificate = Certificate(
                id=cert_id,
                job_id=recipient.job_id,
                recipient_id=recipient.id,
                file_path=None,
                file_name=None,
                status=CertificateStatus.FAILED,
            )
            recipient.status = RecipientStatus.FAILED
            recipient.error_message = f"Certificate generation failed: {str(e)}"
            recipient.processed_at = datetime.utcnow()

            db.add(certificate)
            db.flush()

            return certificate
