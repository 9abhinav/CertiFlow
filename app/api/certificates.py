"""Certificates API endpoints."""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.certificate import Certificate, CertificateStatus

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


def _parse_uuid(value: str) -> uuid.UUID:
    """Safely parse a UUID string, raising 404 on invalid format."""
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )


@router.get(
    "/{certificate_id}/download",
    summary="Download a generated certificate",
    description="Returns the PDF file for a successfully generated certificate.",
    responses={
        200: {"content": {"application/pdf": {}}, "description": "Certificate PDF file"},
        404: {"description": "Certificate not found or not yet generated"},
    },
)
def download_certificate(
    certificate_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """Download a certificate PDF by its ID."""
    parsed_id = _parse_uuid(certificate_id)
    certificate = db.get(Certificate, parsed_id)

    if certificate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )

    if certificate.status != CertificateStatus.SUCCESS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate generation failed — no file available",
        )

    if not certificate.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file path is missing",
        )

    file_path = Path(certificate.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file not found on disk",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=certificate.file_name or f"certificate_{certificate_id}.pdf",
    )
