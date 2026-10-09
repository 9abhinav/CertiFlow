"""Jobs API endpoints."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.models.job import GenerationJob
from app.models.recipient import Recipient
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.job import JobCreateRequest, JobCreateResponse, JobStatusResponse
from app.schemas.certificate import CertificateResponse, JobCertificatesResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

job_service = JobService()


def _parse_uuid(value: str) -> uuid.UUID:
    """Safely parse a UUID string, raising 404 on invalid format."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found",
        )


@router.post(
    "/",
    response_model=JobCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a certificate generation job",
    description=(
        "Accepts a list of recipients and immediately returns a job ID. "
        "Certificate generation happens asynchronously in the background."
    ),
)
def create_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> JobCreateResponse:
    """Create a new certificate generation job and start background processing."""
    job = job_service.create_job(db, request)

    # Schedule background processing
    background_tasks.add_task(job_service.process_job, str(job.id))

    return JobCreateResponse(
        job_id=job.id,
        status=job.status.value,
        total_recipients=job.total_recipients,
        processed_count=job.processed_count,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        created_at=job.created_at,
    )


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status and progress",
    description="Returns the current processing status and progress counters for a job.",
)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    """Retrieve the current status of a generation job."""
    parsed_id = _parse_uuid(job_id)
    job = db.get(GenerationJob, parsed_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found",
        )

    progress = (
        round((job.processed_count / job.total_recipients) * 100, 1)
        if job.total_recipients > 0
        else 0.0
    )

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        total_recipients=job.total_recipients,
        processed_count=job.processed_count,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        progress_percentage=progress,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get(
    "/{job_id}/certificates",
    response_model=JobCertificatesResponse,
    summary="List certificates for a job",
    description="Returns certificate results for every recipient in the job.",
)
def get_job_certificates(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobCertificatesResponse:
    """List all certificate results for a given job."""
    parsed_id = _parse_uuid(job_id)
    job = db.get(GenerationJob, parsed_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found",
        )

    # Query recipients and left-join their certificates
    recipients = (
        db.query(Recipient)
        .filter(Recipient.job_id == job.id)
        .all()
    )

    certificates_out: list[CertificateResponse] = []

    for recipient in recipients:
        cert = (
            db.query(Certificate)
            .filter(Certificate.recipient_id == recipient.id)
            .first()
        )

        if cert and cert.status == CertificateStatus.SUCCESS:
            download_url = f"/api/certificates/{cert.id}/download"
            cert_status = "SUCCESS"
            error_message = None
        elif cert:
            download_url = None
            cert_status = "FAILED"
            error_message = recipient.error_message or "Certificate generation failed"
        else:
            # Certificate not yet generated (still processing)
            download_url = None
            cert_status = recipient.status.value
            error_message = recipient.error_message

        certificates_out.append(
            CertificateResponse(
                id=cert.id if cert else recipient.id,
                recipient_name=recipient.name,
                recipient_email=recipient.email,
                status=cert_status,
                download_url=download_url,
                error_message=error_message,
            )
        )

    return JobCertificatesResponse(job_id=job.id, certificates=certificates_out)
