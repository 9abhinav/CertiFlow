"""Tests for input validation — Pydantic rules and error responses."""


def test_missing_event_name(client, sample_job_request):
    """Request without event_name should return 422."""
    del sample_job_request["event_name"]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_empty_event_name(client, sample_job_request):
    """Empty event_name should return 422."""
    sample_job_request["event_name"] = ""
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_missing_certificate_title(client, sample_job_request):
    """Request without certificate_title should return 422."""
    del sample_job_request["certificate_title"]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_missing_organization_name(client, sample_job_request):
    """Request without organization_name should return 422."""
    del sample_job_request["organization_name"]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_missing_issue_date(client, sample_job_request):
    """Request without issue_date should return 422."""
    del sample_job_request["issue_date"]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_invalid_issue_date(client, sample_job_request):
    """Non-date issue_date should return 422."""
    sample_job_request["issue_date"] = "not-a-date"
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_empty_recipients_list(client, sample_job_request):
    """Empty recipients list should return 422."""
    sample_job_request["recipients"] = []
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_missing_recipients_field(client, sample_job_request):
    """Missing recipients field entirely should return 422."""
    del sample_job_request["recipients"]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_invalid_email(client, sample_job_request):
    """Malformed email should return 422."""
    sample_job_request["recipients"] = [
        {"name": "Test User", "email": "not-an-email"}
    ]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_missing_recipient_name(client, sample_job_request):
    """Recipient without name should return 422."""
    sample_job_request["recipients"] = [
        {"email": "test@example.com"}
    ]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_empty_recipient_name(client, sample_job_request):
    """Recipient with empty name should return 422."""
    sample_job_request["recipients"] = [
        {"name": "", "email": "test@example.com"}
    ]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_recipient_name_too_long(client, sample_job_request):
    """Recipient name exceeding max length should return 422."""
    sample_job_request["recipients"] = [
        {"name": "A" * 201, "email": "test@example.com"}
    ]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_duplicate_emails(client, sample_job_request):
    """Duplicate recipient emails should return 422."""
    sample_job_request["recipients"] = [
        {"name": "User A", "email": "same@example.com"},
        {"name": "User B", "email": "same@example.com"},
    ]
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_event_name_too_long(client, sample_job_request):
    """Event name exceeding 255 chars should return 422."""
    sample_job_request["event_name"] = "X" * 256
    response = client.post("/api/jobs/", json=sample_job_request)
    assert response.status_code == 422


def test_completely_empty_body(client):
    """Sending an empty body should return 422."""
    response = client.post("/api/jobs/", json={})
    assert response.status_code == 422


def test_validation_errors_are_json(client):
    """Validation errors should return well-formed JSON."""
    response = client.post("/api/jobs/", json={})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
