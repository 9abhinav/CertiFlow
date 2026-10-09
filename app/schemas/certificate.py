"""Pydantic schemas for certificate responses."""

import uuid

from pydantic import BaseModel


class CertificateResponse(BaseModel):
    """Schema for a single certificate in the results list."""

    id: uuid.UUID
    recipient_name: str
    recipient_email: str
    status: str
    download_url: str | None
    error_message: str | None

    model_config = {"from_attributes": True}


class JobCertificatesResponse(BaseModel):
    """Schema for the full list of certificates for a job."""

    job_id: uuid.UUID
    certificates: list[CertificateResponse]
