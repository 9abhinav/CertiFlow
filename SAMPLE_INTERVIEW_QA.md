# Sample Interview Questions & Answers — CertiFlow

---

### 1. Walk me through what happens when a POST request hits /api/jobs/.

The request body is first validated by Pydantic — it checks that all required fields exist, emails are valid, names are within length limits, and there are no duplicate emails. If validation fails, FastAPI automatically returns a 422 with detailed error messages. If valid, the `JobService.create_job()` method creates a `GenerationJob` row and one `Recipient` row per person, commits them, and returns the job. The API handler then schedules `process_job()` as a background task and immediately returns a 201 response with the job ID and status PENDING.

---

### 2. Why did you choose FastAPI over Flask or Django?

FastAPI gives me three things out of the box that Flask doesn't: automatic request validation through Pydantic, auto-generated OpenAPI documentation, and a built-in `BackgroundTasks` mechanism. Django would work but it's a full MVC framework — overkill for a focused API service. FastAPI is the right-sized tool for this job.

---

### 3. How does your background processing work?

I use FastAPI's `BackgroundTasks`, which schedules a function to run after the response is sent. The function `process_job()` creates its own database session, loads the job and its recipients, and iterates through each one, generating a PDF and updating the database. It runs in the same process, in a thread pool managed by Starlette.

---

### 4. Why does the background task create its own database session?

The request-scoped session from `get_db()` is closed after the response is sent. The background task runs *after* the response, so that session is no longer valid. Creating a fresh session ensures the background task has a reliable, independent database connection. Sharing sessions across threads would also risk race conditions.

---

### 5. What happens if one certificate generation fails?

The loop continues. Each recipient is processed inside a `try/except`. If generation fails, the recipient is marked FAILED with an error message, the `failed_count` is incremented, and the loop moves to the next recipient. The final job status becomes `PARTIALLY_COMPLETED` if some succeeded and some failed.

---

### 6. How do you prevent one failure from crashing the entire job?

Two layers of protection: (1) The `CertificateService.generate_certificate()` method has a `try/except` around the PDF generation call — if ReportLab throws, it catches the exception and returns a FAILED certificate record. (2) The `process_job()` method has an outer `try/except` around each iteration, catching anything the certificate service didn't catch. Both layers update the recipient status and continue.

---

### 7. Explain your database schema design.

Three tables: `generation_jobs` tracks the overall job metadata and progress counters. `recipients` stores each person's name, email, and processing status. `certificates` stores the PDF file metadata with a unique foreign key to the recipient. This separation lets me track recipient-level failures independently from certificate files.

---

### 8. Why UUIDs instead of auto-increment integers?

UUIDs prevent enumeration attacks — a user can't guess other job IDs by incrementing a number. They also don't reveal how many jobs have been created. In a distributed system, UUIDs can be generated without coordinating with the database. The minor trade-off is they're larger than integers, but for this scale it's negligible.

---

### 9. Why store PDFs on the filesystem instead of in the database?

PostgreSQL isn't optimised for serving large binary files. Storing PDFs as BLOBs would bloat the database, slow backups, and increase memory usage. The filesystem is faster for serving files, and FileResponse can stream them efficiently. In production, I'd use S3 or similar object storage.

---

### 10. How do you handle input validation?

Pydantic v2 models handle all validation declaratively. The `RecipientRequest` schema enforces non-empty name (1–200 chars) and valid email format. The `JobCreateRequest` schema requires all fields, validates the date format, ensures at least one recipient, and has a custom validator that rejects duplicate emails. FastAPI converts validation errors into 422 responses automatically.

---

### 11. How are your tests structured?

I have 35 tests across 6 files, each testing a specific concern: job creation, input validation, PDF generation, progress tracking, failure handling, and certificate download. Tests use SQLite with tables created/dropped per test for isolation. The `conftest.py` patches `SessionLocal` so background tasks also use the test database. TestClient runs background tasks synchronously, so I can assert final state immediately.

---

### 12. How do you ensure the test database is isolated from production?

Three mechanisms: (1) Environment variables are overridden before any app imports. (2) FastAPI's `dependency_overrides` replaces `get_db` with a test session factory. (3) `unittest.mock.patch` replaces `SessionLocal` in the job service module so background tasks use the test DB too. Tables are created before each test and dropped after.

---

### 13. What would you change to handle 100,000 certificates?

I'd switch to Celery with Redis as the message broker. Each recipient could be a separate Celery task, allowing parallel processing across multiple workers. I'd also add S3 for certificate storage, pagination for the certificates list endpoint, and database connection pooling. The API servers would be stateless behind a load balancer.

---

### 14. Why didn't you use Celery for this project?

The assignment specifically asked for a simple, understandable architecture. Celery adds Redis, separate worker processes, and a more complex deployment model. For the scope of this assignment (up to a few hundred certificates), BackgroundTasks is sufficient and much easier to understand, deploy, and debug.

---

### 15. How does your certificate template work?

The template uses ReportLab's Canvas API to draw directly onto a landscape A4 page. It draws decorative borders, corner ornaments, the organization name, certificate title, recipient name with an underline, event description, issue date, signature lines, and the certificate ID. It's a single function that receives all data as parameters and draws everything onto the canvas.

---

### 16. What security measures did you implement?

Input validation prevents malformed data from reaching the database. Filenames are sanitised to remove unsafe characters and prevent path traversal. UUIDs prevent resource enumeration. SQLAlchemy parameterises all queries, preventing SQL injection. Internal stack traces are never exposed to clients — the global exception handler returns a generic error message. Secrets are loaded from environment variables and never committed.

---

### 17. How would you add authentication to this API?

I'd use FastAPI's built-in OAuth2 support with JWT tokens. Add a `users` table, a login endpoint that issues JWTs, and a dependency that validates the token on protected endpoints. Each job would be associated with a user, and users could only see their own jobs. For a more robust solution, I'd integrate with an identity provider like Auth0.

---

### 18. What's the difference between COMPLETED, PARTIALLY_COMPLETED, and FAILED?

- `COMPLETED`: Every recipient got a successful certificate (`successful_count == total_recipients`)
- `PARTIALLY_COMPLETED`: At least one succeeded and at least one failed (`successful_count > 0 and failed_count > 0`)
- `FAILED`: Zero certificates were generated successfully (`successful_count == 0`)

---

### 19. How does the progress percentage work?

It's `(processed_count / total_recipients) * 100`, rounded to one decimal. `processed_count` increments after each recipient regardless of success or failure. So if 65 out of 100 recipients have been processed, the progress is 65.0% — it doesn't matter how many of those 65 were successes or failures.

---

### 20. What are the biggest weaknesses of your current implementation?

1. No authentication — any client can access any job
2. No persistent task queue — server restart loses in-progress jobs
3. Sequential processing — certificates are generated one at a time
4. Local filesystem — doesn't scale to multiple servers
5. No retry mechanism — transient failures are permanent
6. No pagination — listing 10,000 certificates returns them all at once
7. Progress counters use in-memory increments rather than SQL atomic updates

---

### 21. How does Docker Compose work in your setup?

Docker Compose defines two services: `db` (PostgreSQL 16 Alpine) and `app` (the FastAPI application). PostgreSQL has a health check, and the app waits for it to be healthy before starting. On startup, the app runs `alembic upgrade head` to apply migrations, then starts uvicorn. Generated certificates are stored in a mounted volume so they persist across container restarts.

---

### 22. What happens if the server crashes during background processing?

The in-progress job would be stuck in PROCESSING status forever. Recipients that hadn't been processed yet would remain PENDING. There's no recovery mechanism — this is the main limitation of using BackgroundTasks instead of Celery. With Celery, unacknowledged tasks are automatically retried by another worker.

---

### 23. Why did you use Alembic for migrations?

Alembic is the standard migration tool for SQLAlchemy. It tracks schema versions, supports both upgrade and downgrade, and can auto-generate migrations from model changes. This ensures database schema changes are reproducible and version-controlled, which is essential for team collaboration and deployment pipelines.

---

### 24. How would you monitor this system in production?

I'd add structured JSON logging with correlation IDs (job_id in every log line), expose Prometheus metrics (job count, processing duration, failure rate), set up Grafana dashboards, and add alerting for elevated failure rates. I'd also add a `/health` endpoint that checks database connectivity, which load balancers can use for health checks.

---

### 25. Can you explain the service layer architecture?

The code is split into three layers: **API layer** (routes, request/response handling), **service layer** (business logic), and **data layer** (SQLAlchemy models). The API layer calls `JobService` which calls `CertificateService` which calls `PDFService`. Each service has a single responsibility. This separation makes the code testable — you can test PDF generation without making HTTP requests, and test failure handling without generating real PDFs (using mocks).
