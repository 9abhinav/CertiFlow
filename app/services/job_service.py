"""Job orchestration service.

Responsible for creating jobs, persisting recipients,
and running the background certificate generation loop.
"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.logging import logger
from app.db.database import SessionLocal
from app.models.job import GenerationJob, JobStatus
from app.models.recipient import Recipient, RecipientStatus
from app.models.certificate import CertificateStatus
from app.schemas.job import JobCreateRequest
from app.services.certificate_service import CertificateService


class JobService:
    """Orchestrates certificate generation jobs."""

    def __init__(self) -> None:
        self.certificate_service = CertificateService()

    @staticmethod
    def _parse_uuid(value: str | uuid.UUID) -> uuid.UUID:
        """Convert a string to UUID if needed."""
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

    def create_job(self, db: Session, request: JobCreateRequest) -> GenerationJob:
        """Create a new generation job and its recipient records.

        Does NOT start processing — that happens in the background task.

        Args:
            db: Active SQLAlchemy session.
            request: Validated job creation request.

        Returns:
            The persisted GenerationJob object.
        """
        job = GenerationJob(
            event_name=request.event_name,
            certificate_title=request.certificate_title,
            organization_name=request.organization_name,
            issue_date=request.issue_date,
            status=JobStatus.PENDING,
            total_recipients=len(request.recipients),
        )
        db.add(job)
        db.flush()  # Assign job.id before creating recipients

        for r in request.recipients:
            recipient = Recipient(
                job_id=job.id,
                name=r.name,
                email=r.email,
                status=RecipientStatus.PENDING,
            )
            db.add(recipient)

        db.commit()
        db.refresh(job)

        logger.info(
            "Job created: %s with %d recipients", job.id, job.total_recipients
        )
        return job

    def get_job(self, db: Session, job_id: str | uuid.UUID) -> GenerationJob | None:
        """Retrieve a job by its UUID."""
        return db.get(GenerationJob, self._parse_uuid(job_id))

    def process_job(self, job_id: str, session_factory=None) -> None:
        """Background task: generate certificates for every recipient.

        This method creates its own database session so it is safe to
        run outside the request lifecycle. Each recipient is processed
        individually — a failure in one does NOT stop the others.

        Args:
            job_id: UUID of the job to process.
            session_factory: Optional session factory (for testing).
                             Defaults to SessionLocal.
        """
        # Background tasks must create their own session
        factory = session_factory or SessionLocal
        db = factory()
        try:
            parsed_id = self._parse_uuid(job_id)
            job = db.get(GenerationJob, parsed_id)
            if job is None:
                logger.error("Background task: job %s not found", job_id)
                return

            job.status = JobStatus.PROCESSING
            job.started_at = datetime.utcnow()
            db.commit()

            logger.info("Processing job %s — %d recipients", job_id, job.total_recipients)

            recipients = (
                db.query(Recipient)
                .filter(Recipient.job_id == job.id)
                .all()
            )

            for recipient in recipients:
                try:
                    cert = self.certificate_service.generate_certificate(
                        db,
                        recipient=recipient,
                        organization_name=job.organization_name,
                        certificate_title=job.certificate_title,
                        event_name=job.event_name,
                        issue_date=job.issue_date,
                    )

                    # Update job counters
                    job.processed_count += 1
                    if cert.status == CertificateStatus.SUCCESS:
                        job.successful_count += 1
                    else:
                        job.failed_count += 1

                    db.commit()

                except Exception as e:
                    # Catch-all: even if the certificate service itself raises,
                    # we don't want the whole job to abort.
                    logger.error(
                        "Unexpected error processing recipient %s: %s",
                        recipient.id,
                        str(e),
                    )
                    db.rollback()

                    # Refresh the job object after rollback
                    db.refresh(job)

                    recipient.status = RecipientStatus.FAILED
                    recipient.error_message = f"Unexpected error: {str(e)}"
                    recipient.processed_at = datetime.utcnow()
                    job.processed_count += 1
                    job.failed_count += 1
                    db.commit()

            # ── Finalize job status ─────────────────────────────
            if job.successful_count == job.total_recipients:
                job.status = JobStatus.COMPLETED
            elif job.successful_count > 0:
                job.status = JobStatus.PARTIALLY_COMPLETED
            else:
                job.status = JobStatus.FAILED

            job.completed_at = datetime.utcnow()
            db.commit()

            logger.info(
                "Job %s finished — status=%s, success=%d, failed=%d",
                job_id,
                job.status.value,
                job.successful_count,
                job.failed_count,
            )

        except Exception as e:
            logger.error("Fatal error processing job %s: %s", job_id, str(e))
            db.rollback()
            try:
                parsed_id = self._parse_uuid(job_id)
                job = db.get(GenerationJob, parsed_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.utcnow()
                    db.commit()
            except Exception:
                logger.error("Could not mark job %s as FAILED", job_id)
        finally:
            db.close()
