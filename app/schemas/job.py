"""Pydantic schemas for job requests and responses."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.recipient import RecipientRequest


class JobCreateRequest(BaseModel):
    """Schema for creating a new certificate generation job."""

    event_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the event or course",
        examples=["AI Workshop 2026"],
    )
    certificate_title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Title displayed on the certificate",
        examples=["Certificate of Participation"],
    )
    organization_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the issuing organization",
        examples=["ABC Institute"],
    )
    issue_date: date = Field(
        ...,
        description="Date of certificate issuance",
        examples=["2026-10-08"],
    )
    recipients: list[RecipientRequest] = Field(
        ...,
        min_length=1,
        description="List of certificate recipients (at least one required)",
    )

    @field_validator("recipients")
    @classmethod
    def check_duplicate_emails(cls, recipients: list[RecipientRequest]) -> list[RecipientRequest]:
        """Reject requests with duplicate recipient emails."""
        emails = [r.email.lower() for r in recipients]
        duplicates = {e for e in emails if emails.count(e) > 1}
        if duplicates:
            raise ValueError(
                f"Duplicate recipient emails found: {', '.join(sorted(duplicates))}"
            )
        return recipients


class JobCreateResponse(BaseModel):
    """Schema returned after successfully creating a job."""

    job_id: uuid.UUID
    status: str
    total_recipients: int
    processed_count: int
    successful_count: int
    failed_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class JobStatusResponse(BaseModel):
    """Schema for job status and progress."""

    job_id: uuid.UUID
    status: str
    total_recipients: int
    processed_count: int
    successful_count: int
    failed_count: int
    progress_percentage: float
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = {"from_attributes": True}
