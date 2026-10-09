"""Tests for failure handling — ensuring one failure doesn't stop the job."""

import uuid
from datetime import date, datetime
from unittest.mock import patch, MagicMock

from app.models.job import GenerationJob, JobStatus
from app.models.recipient import Recipient, RecipientStatus
from app.services.job_service import JobService


def test_partial_failure_continues_processing(client, db_session):
    """If one certificate fails, the rest should still be generated."""
    # Create a job directly in the DB
    job = GenerationJob(
        event_name="Test Event",
        certificate_title="Certificate",
        organization_name="Org",
        issue_date=date(2026, 10, 8),
        status=JobStatus.PENDING,
        total_recipients=3,
    )
    db_session.add(job)
    db_session.flush()

    # Add 3 recipients
    for i in range(3):
        recipient = Recipient(
            job_id=job.id,
            name=f"User {i}",
            email=f"user{i}@example.com",
            status=RecipientStatus.PENDING,
        )
        db_session.add(recipient)
    db_session.commit()

    # Mock PDF generation to fail for the second recipient
    call_count = 0
    original_generate = PDFService_generate_pdf = None

    from app.services.pdf_service import PDFService
    original_generate = PDFService.generate_pdf

    def mock_generate_pdf(self, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise Exception("Simulated PDF failure")
        return original_generate(self, **kwargs)

    with patch.object(PDFService, "generate_pdf", mock_generate_pdf):
        service = JobService()
        service.process_job(str(job.id))

    # Refresh job
    db_session.expire_all()
    job = db_session.get(GenerationJob, job.id)

    assert job.status == JobStatus.PARTIALLY_COMPLETED
    assert job.processed_count == 3
    assert job.successful_count == 2
    assert job.failed_count == 1


def test_all_failures_marks_job_failed(client, db_session):
    """If every certificate fails, job status should be FAILED."""
    job = GenerationJob(
        event_name="Test Event",
        certificate_title="Certificate",
        organization_name="Org",
        issue_date=date(2026, 10, 8),
        status=JobStatus.PENDING,
        total_recipients=2,
    )
    db_session.add(job)
    db_session.flush()

    for i in range(2):
        db_session.add(Recipient(
            job_id=job.id,
            name=f"User {i}",
            email=f"fail{i}@example.com",
            status=RecipientStatus.PENDING,
        ))
    db_session.commit()

    from app.services.pdf_service import PDFService

    with patch.object(PDFService, "generate_pdf", side_effect=Exception("Always fail")):
        service = JobService()
        service.process_job(str(job.id))

    db_session.expire_all()
    job = db_session.get(GenerationJob, job.id)

    assert job.status == JobStatus.FAILED
    assert job.successful_count == 0
    assert job.failed_count == 2


def test_failed_recipient_has_error_message(client, db_session):
    """Failed recipients should have an error_message set."""
    job = GenerationJob(
        event_name="Event",
        certificate_title="Cert",
        organization_name="Org",
        issue_date=date(2026, 10, 8),
        status=JobStatus.PENDING,
        total_recipients=1,
    )
    db_session.add(job)
    db_session.flush()

    recipient = Recipient(
        job_id=job.id,
        name="Fail User",
        email="fail@example.com",
        status=RecipientStatus.PENDING,
    )
    db_session.add(recipient)
    db_session.commit()

    from app.services.pdf_service import PDFService

    with patch.object(PDFService, "generate_pdf", side_effect=Exception("PDF error")):
        service = JobService()
        service.process_job(str(job.id))

    db_session.expire_all()
    recipient = db_session.get(Recipient, recipient.id)

    assert recipient.status == RecipientStatus.FAILED
    assert recipient.error_message is not None
    assert "PDF error" in recipient.error_message
