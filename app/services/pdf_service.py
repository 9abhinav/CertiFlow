"""PDF generation service using ReportLab.

Responsible for creating certificate PDF files on the filesystem.
"""

from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen.canvas import Canvas

from app.core.config import settings
from app.core.logging import logger
from app.utils.file_utils import ensure_directory, sanitize_filename
from templates.certificate_template import draw_certificate


class PDFService:
    """Generates certificate PDF files and stores them on the filesystem."""

    def __init__(self) -> None:
        self.output_dir = ensure_directory(settings.GENERATED_FILES_DIR)

    def generate_pdf(
        self,
        *,
        certificate_id: str,
        organization_name: str,
        certificate_title: str,
        recipient_name: str,
        event_name: str,
        issue_date: date,
    ) -> tuple[str, str]:
        """Generate a certificate PDF and return (file_path, file_name).

        Args:
            certificate_id: Unique certificate identifier.
            organization_name: Issuing organization.
            certificate_title: Title printed on the certificate.
            recipient_name: Name of the recipient.
            event_name: Event or course name.
            issue_date: Date of issuance.

        Returns:
            Tuple of (absolute file path, safe file name).

        Raises:
            Exception: If PDF generation fails for any reason.
        """
        file_name = sanitize_filename(f"certificate_{certificate_id}.pdf")
        file_path = str(self.output_dir / file_name)

        logger.info("Generating PDF: %s for %s", file_name, recipient_name)

        canvas = Canvas(file_path, pagesize=landscape(A4))

        draw_certificate(
            canvas,
            organization_name=organization_name,
            certificate_title=certificate_title,
            recipient_name=recipient_name,
            event_name=event_name,
            issue_date=issue_date,
            certificate_id=certificate_id,
        )

        canvas.showPage()
        canvas.save()

        logger.info("PDF saved: %s", file_path)
        return file_path, file_name
