"""Tests for certificate listing and downloading."""

import os


def test_get_job_certificates(client, sample_job_request):
    """GET /api/jobs/{id}/certificates should list all certificates."""
    create_resp = client.post("/api/jobs/", json=sample_job_request)
    job_id = create_resp.json()["job_id"]

    response = client.get(f"/api/jobs/{job_id}/certificates")
    assert response.status_code == 200

    data = response.json()
    assert data["job_id"] == job_id
    assert len(data["certificates"]) == 2

    for cert in data["certificates"]:
        assert "id" in cert
        assert "recipient_name" in cert
        assert "recipient_email" in cert
        assert "status" in cert


def test_successful_certificates_have_download_url(client, sample_job_request):
    """Successful certificates should include a download URL."""
    create_resp = client.post("/api/jobs/", json=sample_job_request)
    job_id = create_resp.json()["job_id"]

    response = client.get(f"/api/jobs/{job_id}/certificates")
    data = response.json()

    for cert in data["certificates"]:
        if cert["status"] == "SUCCESS":
            assert cert["download_url"] is not None
            assert "/api/certificates/" in cert["download_url"]
            assert cert["error_message"] is None


def test_download_certificate_pdf(client, sample_job_request):
    """GET /api/certificates/{id}/download should return a PDF file."""
    create_resp = client.post("/api/jobs/", json=sample_job_request)
    job_id = create_resp.json()["job_id"]

    # Get certificates list
    certs_resp = client.get(f"/api/jobs/{job_id}/certificates")
    certificates = certs_resp.json()["certificates"]

    # Find a successful certificate
    success_cert = next(
        (c for c in certificates if c["status"] == "SUCCESS"), None
    )
    assert success_cert is not None, "Expected at least one successful certificate"

    # Download it
    download_resp = client.get(success_cert["download_url"])
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"

    # Verify PDF header
    assert download_resp.content[:5] == b"%PDF-"


def test_download_nonexistent_certificate(client):
    """Downloading a non-existent certificate should return 404."""
    response = client.get(
        "/api/certificates/00000000-0000-0000-0000-000000000000/download"
    )
    assert response.status_code == 404


def test_certificates_for_nonexistent_job(client):
    """Certificates for a non-existent job should return 404."""
    response = client.get(
        "/api/jobs/00000000-0000-0000-0000-000000000000/certificates"
    )
    assert response.status_code == 404
