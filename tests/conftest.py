"""Shared test fixtures and configuration.

Uses an in-memory SQLite database for fast, isolated testing.
Background tasks are executed synchronously in TestClient, so
we monkey-patch SessionLocal to use the test database.
"""

import os
import shutil
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# Override settings BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["GENERATED_FILES_DIR"] = "test_generated_certificates"

from app.db.base import Base
from app.db.database import get_db
from app.main import app
import app.services.job_service as job_service_module
import app.api.certificates as cert_api_module

# ── SQLite test engine ──────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

test_engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Enable foreign keys for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def override_get_db():
    """Dependency override that yields a test-scoped session."""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_dirs():
    """Create test output directory."""
    Path("test_generated_certificates").mkdir(exist_ok=True)
    yield
    # Cleanup generated test files
    if Path("test_generated_certificates").exists():
        shutil.rmtree("test_generated_certificates", ignore_errors=True)


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def patch_session_local():
    """Ensure background tasks use the test database session factory."""
    with patch.object(job_service_module, "SessionLocal", TestSessionLocal):
        yield


@pytest.fixture
def db_session():
    """Provide a transactional test database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_job_request():
    """Return a valid job creation request body."""
    return {
        "event_name": "AI Workshop 2026",
        "certificate_title": "Certificate of Participation",
        "organization_name": "ABC Institute",
        "issue_date": "2026-10-08",
        "recipients": [
            {"name": "Abhinav Dewangan", "email": "abhinav@example.com"},
            {"name": "Rahul Sharma", "email": "rahul@example.com"},
        ],
    }
