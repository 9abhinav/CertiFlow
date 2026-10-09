"""Tests for the POST /api/jobs/ endpoint — job creation."""

import time


def test_create_job_success(client, sample_job_request):
    """A valid request should return 201 with job details."""
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 201

    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"
    assert data["total_recipients"] == 2
    assert data["processed_count"] == 0
    assert data["successful_count"] == 0
    assert data["failed_count"] == 0


def test_create_job_single_recipient(client):
    """A job with one recipient should work."""
    payload = {
        "event_name": "Workshop",
        "certificate_title": "Certificate",
        "organization_name": "Org",
        "issue_date": "2026-10-08",
        "recipients": [{"name": "Test User", "email": "test@example.com"}],
    }
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 201
    assert response.json()["total_recipients"] == 1


def test_create_job_many_recipients(client):
    """A job with multiple recipients should be accepted."""
    recipients = [
        {"name": f"User {i}", "email": f"user{i}@example.com"}
        for i in range(10)
    ]
    payload = {
        "event_name": "Big Event",
        "certificate_title": "Certificate",
        "organization_name": "Org",
        "issue_date": "2026-10-08",
        "recipients": recipients,
    }
    response = client.post("/api/jobs/", json=payload)
    assert response.status_code == 201
    assert response.json()["total_recipients"] == 10


def test_create_job_returns_created_at(client, sample_job_request):
    """Response should include a created_at timestamp."""
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 201
    assert response.json()["created_at"] is not None
