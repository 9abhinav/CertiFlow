"""Tests for PDF certificate generation using the PDFService directly."""

import os
from datetime import date
from pathlib import Path

from app.services.pdf_service import PDFService


def test_generate_pdf_creates_file():
    """PDFService should create a valid PDF file on disk."""
    service = PDFService()
    file_path, file_name = service.generate_pdf(
        certificate_id="test-cert-001",
        organization_name="Test University",
        certificate_title="Certificate of Achievement",
        recipient_name="Jane Doe",
        event_name="Python Masterclass",
        issue_date=date(2026, 10, 8),
    )

    assert os.path.exists(file_path)
    assert file_name == "certificate_test-cert-001.pdf"
    assert file_path.endswith(".pdf")

    # Verify it's actually a PDF (starts with %PDF)
    with open(file_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"

    # Cleanup
    os.remove(file_path)


def test_generate_pdf_file_has_content():
    """Generated PDF should have non-trivial file size."""
    service = PDFService()
    file_path, _ = service.generate_pdf(
        certificate_id="test-cert-002",
        organization_name="Org",
        certificate_title="Certificate",
        recipient_name="John Smith",
        event_name="Event",
        issue_date=date(2026, 1, 1),
    )

    file_size = os.path.getsize(file_path)
    assert file_size > 1000  # A proper certificate PDF is well over 1KB

    os.remove(file_path)


def test_generate_pdf_safe_filename():
    """File name should not contain unsafe characters."""
    service = PDFService()
    _, file_name = service.generate_pdf(
        certificate_id="abc-123-def",
        organization_name="Org",
        certificate_title="Cert",
        recipient_name="User",
        event_name="Event",
        issue_date=date(2026, 6, 15),
    )

    # Should only contain safe characters
    assert ".." not in file_name
    assert "/" not in file_name
    assert "\\" not in file_name

    # Cleanup
    path = Path(os.environ.get("GENERATED_FILES_DIR", "test_generated_certificates")) / file_name
    if path.exists():
        path.unlink()
