"""Tests for job status and progress tracking."""

import time


def test_get_job_status(client, sample_job_request):
    """GET /api/jobs/{id} should return job status."""
    create_resp = client.post("/api/jobs/", json=sample_job_request)
    job_id = create_resp.json()["job_id"]

    # Background task runs synchronously in TestClient
    response = client.get(f"/api/jobs/{job_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["job_id"] == job_id
    assert data["total_recipients"] == 2
    assert "progress_percentage" in data
    assert "status" in data


def test_job_not_found(client):
    """GET for a non-existent job should return 404."""
    response = client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Generation job not found"


def test_completed_job_has_correct_counts(client, sample_job_request):
    """After processing, counts should match recipients."""
    create_resp = client.post("/api/jobs/", json=sample_job_request)
    job_id = create_resp.json()["job_id"]

    # TestClient executes background tasks synchronously
    response = client.get(f"/api/jobs/{job_id}")
    data = response.json()

    assert data["total_recipients"] == 2
    assert data["processed_count"] == 2
    assert data["successful_count"] == 2
    assert data["failed_count"] == 0
    assert data["status"] == "COMPLETED"
    assert data["progress_percentage"] == 100.0


def test_completed_job_has_timestamps(client, sample_job_request):
    """Completed jobs should have started_at and completed_at."""
    create_resp = client.post("/api/jobs/", json=sample_job_request)
    job_id = create_resp.json()["job_id"]

    response = client.get(f"/api/jobs/{job_id}")
    data = response.json()

    assert data["started_at"] is not None
    assert data["completed_at"] is not None
