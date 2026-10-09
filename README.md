# CertiFlow — Bulk Certificate Generator API

A production-quality REST API for generating PDF certificates in bulk. Submit a list of recipients, track generation progress in real time, and download certificates individually.

Built as an SDE Intern assignment demonstrating backend engineering fundamentals: REST API design, database modeling, background processing, PDF generation, error handling, and testing.

---

## Features

- **Bulk certificate generation** — submit hundreds of recipients in a single API call
- **Asynchronous processing** — the API responds immediately; certificates are generated in the background
- **Real-time progress tracking** — poll job status to see processed/successful/failed counts
- **Fault-tolerant processing** — one failed certificate does not stop the rest
- **Professional PDF output** — clean, centered certificates with borders, signature areas, and unique IDs
- **Input validation** — Pydantic v2 validates names, emails, lengths, duplicates, and required fields
- **PDF download** — download each generated certificate via a direct URL
- **OpenAPI documentation** — Swagger UI and ReDoc auto-generated from code

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Web Framework | FastAPI | 0.115.x |
| Language | Python | 3.11+ |
| Database | PostgreSQL | 16 |
| ORM | SQLAlchemy | 2.0.x |
| Migrations | Alembic | 1.14.x |
| Validation | Pydantic | 2.10.x |
| PDF Generation | ReportLab | 4.2.x |
| Testing | Pytest | 8.3.x |
| Containerisation | Docker + Docker Compose | — |

---

## Architecture

```
Client
  │
  ▼
POST /api/jobs/  ──►  Validate Request
                          │
                          ▼
                     Create Job + Recipients in DB
                          │
                          ▼
                     Return Job ID (201)
                          │
                          ▼
                  Background Task (FastAPI)
                          │
                   ┌──────┴──────┐
                   │  For each   │
                   │  recipient  │
                   └──────┬──────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
         Generate PDF  Generate PDF  Generate PDF
              │           │           │
              ▼           ▼           ▼
         Save to DB   Save to DB   Save to DB
              │           │           │
              └───────────┼───────────┘
                          ▼
                   Finalize Job Status
                   (COMPLETED / PARTIALLY_COMPLETED / FAILED)
```

---

## Project Structure

```
CertiFlow/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── jobs.py                # Job endpoints (create, status, certificates list)
│   │   └── certificates.py       # Certificate download endpoint
│   ├── core/
│   │   ├── config.py              # Environment-based configuration
│   │   └── logging.py             # Structured logging setup
│   ├── db/
│   │   ├── database.py            # SQLAlchemy engine and session factory
│   │   └── base.py                # Declarative base class
│   ├── models/
│   │   ├── job.py                 # GenerationJob model
│   │   ├── recipient.py           # Recipient model
│   │   └── certificate.py         # Certificate model
│   ├── schemas/
│   │   ├── job.py                 # Job request/response schemas
│   │   ├── recipient.py           # Recipient request schema
│   │   └── certificate.py         # Certificate response schemas
│   ├── services/
│   │   ├── job_service.py         # Job orchestration and background processing
│   │   ├── certificate_service.py # Per-recipient certificate generation
│   │   └── pdf_service.py         # ReportLab PDF file generation
│   └── utils/
│       └── file_utils.py          # Filename sanitisation and directory helpers
├── tests/
│   ├── conftest.py                # Test fixtures and database setup
│   ├── test_jobs.py               # Job creation tests
│   ├── test_validation.py         # Input validation tests
│   ├── test_certificate_generation.py  # PDF generation tests
│   ├── test_job_progress.py       # Progress tracking tests
│   ├── test_failure_handling.py   # Failure isolation tests
│   └── test_certificate_download.py   # Download and listing tests
├── templates/
│   └── certificate_template.py    # ReportLab certificate layout
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 2026_10_08_001_initial_migration.py
├── generated_certificates/        # PDF output directory (git-ignored)
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
├── README.md
├── INTERVIEW_NOTES.md
└── SAMPLE_INTERVIEW_QA.md
```

---

## Database Schema

### `generation_jobs`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique job identifier |
| event_name | VARCHAR(255) | Name of the event or course |
| certificate_title | VARCHAR(255) | Title printed on the certificate |
| organization_name | VARCHAR(255) | Issuing organization |
| issue_date | DATE | Certificate issue date |
| status | ENUM | PENDING / PROCESSING / COMPLETED / PARTIALLY_COMPLETED / FAILED |
| total_recipients | INT | Total recipients submitted |
| processed_count | INT | Recipients processed so far |
| successful_count | INT | Certificates generated successfully |
| failed_count | INT | Certificates that failed |
| created_at | DATETIME | Job creation timestamp |
| started_at | DATETIME | When background processing started |
| completed_at | DATETIME | When the job finished |

### `recipients`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique recipient identifier |
| job_id | UUID (FK) | References generation_jobs.id |
| name | VARCHAR(255) | Recipient full name |
| email | VARCHAR(255) | Recipient email address |
| status | ENUM | PENDING / SUCCESS / FAILED |
| error_message | TEXT | Error details if failed |
| created_at | DATETIME | Record creation timestamp |
| processed_at | DATETIME | When this recipient was processed |

### `certificates`

| Column | Type | Description |
|---|---|---|
| id | UUID (PK) | Unique certificate identifier |
| job_id | UUID (FK) | References generation_jobs.id |
| recipient_id | UUID (FK, UNIQUE) | References recipients.id |
| file_path | VARCHAR(500) | Absolute path to generated PDF |
| file_name | VARCHAR(255) | Safe filename of the PDF |
| status | ENUM | SUCCESS / FAILED |
| created_at | DATETIME | When the certificate was created |

**Relationships:**
- A Job has many Recipients (one-to-many)
- A Job has many Certificates (one-to-many)
- A Recipient has one Certificate (one-to-one)

---

## API Endpoints

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| POST | `/api/jobs/` | Create a certificate generation job | 201 |
| GET | `/api/jobs/{job_id}` | Get job status and progress | 200 |
| GET | `/api/jobs/{job_id}/certificates` | List certificates for a job | 200 |
| GET | `/api/certificates/{certificate_id}/download` | Download a certificate PDF | 200 |
| GET | `/health` | Health check | 200 |
| GET | `/docs` | Swagger UI documentation | — |
| GET | `/redoc` | ReDoc documentation | — |

### Request / Response Examples

**Create a job:**

```bash
curl -X POST http://localhost:8000/api/jobs/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "AI Workshop 2026",
    "certificate_title": "Certificate of Participation",
    "organization_name": "ABC Institute",
    "issue_date": "2026-10-08",
    "recipients": [
      {"name": "Abhinav Dewangan", "email": "abhinav@example.com"},
      {"name": "Rahul Sharma", "email": "rahul@example.com"}
    ]
  }'
```

Response (201):

```json
{
  "job_id": "a1b2c3d4-...",
  "status": "PENDING",
  "total_recipients": 2,
  "processed_count": 0,
  "successful_count": 0,
  "failed_count": 0,
  "created_at": "2026-10-08T18:15:00.000000"
}
```

**Check job status:**

```bash
curl http://localhost:8000/api/jobs/a1b2c3d4-.../
```

Response (200):

```json
{
  "job_id": "a1b2c3d4-...",
  "status": "COMPLETED",
  "total_recipients": 2,
  "processed_count": 2,
  "successful_count": 2,
  "failed_count": 0,
  "progress_percentage": 100.0,
  "created_at": "2026-10-08T18:15:00.000000",
  "started_at": "2026-10-08T18:15:00.100000",
  "completed_at": "2026-10-08T18:15:01.500000"
}
```

**List certificates:**

```bash
curl http://localhost:8000/api/jobs/a1b2c3d4-.../certificates
```

**Download a certificate:**

```bash
curl -O http://localhost:8000/api/certificates/e5f6g7h8-.../download
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 16 (or Docker)

### Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/CertiFlow.git
cd CertiFlow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your PostgreSQL connection string

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/certificates` | PostgreSQL connection string |
| `APP_ENV` | `development` | Application environment |
| `GENERATED_FILES_DIR` | `generated_certificates` | Directory for generated PDFs |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Docker Setup

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

Docker Compose starts:
- **PostgreSQL 16** on port 5432
- **FastAPI application** on port 8000

Alembic migrations run automatically on container startup.

---

## Database Migrations

```bash
# Run all pending migrations
alembic upgrade head

# Create a new migration (after model changes)
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test file
pytest tests/test_validation.py

# Run a specific test
pytest tests/test_failure_handling.py::test_partial_failure_continues_processing
```

Tests use an in-memory SQLite database — no PostgreSQL required for testing.

**Test coverage:**
- Job creation (4 tests)
- Input validation (16 tests)
- PDF generation (3 tests)
- Job progress tracking (4 tests)
- Failure handling (3 tests)
- Certificate download (5 tests)
- **Total: 35 tests**

---

## Design Decisions

### Why FastAPI?

FastAPI provides automatic request validation through Pydantic, built-in OpenAPI documentation, native `BackgroundTasks` support, and high performance via async capabilities. It's the most pragmatic choice for a modern Python REST API.

**Alternatives considered:** Flask (lacks built-in validation, async, and docs generation), Django REST Framework (too heavy for a focused API service).

### Why PostgreSQL?

PostgreSQL is the industry-standard relational database for production applications. It supports UUIDs natively, has robust ACID compliance, and handles concurrent writes safely — all critical for tracking job progress from background tasks.

**Alternatives considered:** SQLite (no concurrency support for production), MySQL (less UUID support, weaker feature set).

### Why SQLAlchemy 2.x?

SQLAlchemy 2.x with mapped columns provides type-safe ORM models, strong relationship support, and clean integration with Alembic for migrations. The declarative style is readable and maintainable.

### Why ReportLab?

ReportLab is the most mature Python library for programmatic PDF generation. It provides pixel-level control over layout, which is essential for certificate aesthetics. The canvas API is straightforward to understand and extend.

**Alternatives considered:** FPDF2 (less mature), WeasyPrint (requires HTML-to-PDF, adding unnecessary complexity).

### Why BackgroundTasks instead of Celery?

For this assignment scope, FastAPI `BackgroundTasks` provides simple, in-process background execution without additional infrastructure (Redis, RabbitMQ, separate worker processes). It keeps the architecture understandable and deployable as a single service.

**When to switch to Celery:** When processing thousands of certificates, needing horizontal scaling, requiring retry mechanisms, or running across multiple worker nodes.

### Why Filesystem Storage instead of Database BLOBs?

Storing PDFs on the filesystem is simpler, more performant, and avoids bloating the database. PostgreSQL isn't optimised for serving large binary files. The database stores only the file path and metadata.

**For production:** Object storage (S3, GCS) would replace the local filesystem.

### Why UUIDs?

UUIDs prevent enumeration attacks (users can't guess other job/certificate IDs), don't leak creation order, and work well in distributed systems. They're the standard for public-facing resource identifiers.

### Why Job-Based API?

A job-based (asynchronous) API lets the client submit a request and poll for results. This avoids HTTP timeouts for large batches and provides real-time progress visibility. The alternative — synchronous generation — would block the client for the entire duration.

---

## Failure Handling

The system is designed so that **one failed certificate never stops the rest**:

1. Each recipient is processed individually inside a `try/except` block
2. On failure: the recipient is marked `FAILED`, an error message is stored, and counters are updated
3. Processing continues to the next recipient
4. Final job status reflects the outcome:
   - All succeed → `COMPLETED`
   - Some succeed, some fail → `PARTIALLY_COMPLETED`
   - All fail → `FAILED`

---

## Limitations

- **No authentication** — any client can create jobs and download certificates
- **No rate limiting** — no protection against abuse
- **Single-process background tasks** — not suitable for horizontal scaling
- **Local filesystem storage** — not suitable for multi-server deployments
- **No email delivery** — certificates must be downloaded manually
- **Single certificate template** — no template customisation
- **No job cancellation** — once started, a job runs to completion
- **No retry mechanism** — failed certificates are not automatically retried

---

## Future Scope

- **Celery + Redis** for distributed, scalable background processing
- **S3/object storage** for certificate files
- **Email delivery** of generated certificates
- **Multiple certificate templates** with customizable designs
- **Authentication & authorization** (OAuth2 / JWT)
- **Rate limiting** to prevent abuse
- **Job cancellation** endpoint
- **Automatic retry** for transient failures
- **Admin dashboard** for monitoring jobs
- **Horizontal scaling** with multiple worker processes
- **Observability** — structured logging, metrics (Prometheus), tracing
- **Pagination** for certificate listings

---

## License

This project was built as an SDE Intern assignment submission.
