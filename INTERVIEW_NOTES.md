# Interview Notes — CertiFlow

These notes explain the system in plain language so you can confidently discuss every part during an interview.

---

## 1. How the Application Works

CertiFlow is a REST API that generates PDF certificates in bulk. A client sends a POST request with event details and a list of recipients. The API immediately creates a "job" record in the database, returns the job ID, and kicks off a background task that generates one PDF per recipient. The client can poll the job status endpoint at any time to see how many certificates have been generated so far.

---

## 2. Request Lifecycle

```
1. Client sends POST /api/jobs/ with JSON body
2. FastAPI validates the body using Pydantic (names, emails, duplicates, lengths)
3. If validation fails → 422 response with clear error messages
4. If valid → Create a GenerationJob row + one Recipient row per person
5. Commit to the database
6. Return 201 with the job ID and status=PENDING
7. FastAPI schedules a background task (process_job)
8. Background task:
   a. Sets job status → PROCESSING, records started_at
   b. Loops through each recipient
   c. For each: generates PDF → creates Certificate record → updates counters
   d. If any single PDF fails: marks that recipient as FAILED, continues to the next
   e. After all recipients: sets final job status and completed_at
```

---

## 3. Database Relationships

- **GenerationJob** → has many **Recipients** (one-to-many)
- **GenerationJob** → has many **Certificates** (one-to-many)
- **Recipient** → has one **Certificate** (one-to-one, via unique foreign key)

This separation means we can track a recipient's status independently from whether their certificate file was created.

---

## 4. Why BackgroundTasks?

FastAPI's `BackgroundTasks` runs a function after the response is sent. It runs in the same process, in the same event loop's thread pool. This is perfect for our scope because:
- No extra infrastructure (no Redis, no Celery workers)
- Simple to understand and debug
- Sufficient for moderate batch sizes

The trade-off: it doesn't survive server restarts, and can't scale horizontally. For production with thousands of concurrent jobs, you'd switch to Celery.

---

## 5. How Failures Are Isolated

Every recipient is processed inside its own `try/except` block:

```python
for recipient in recipients:
    try:
        cert = certificate_service.generate_certificate(db, ...)
        job.processed_count += 1
        if cert.status == SUCCESS:
            job.successful_count += 1
        else:
            job.failed_count += 1
        db.commit()
    except Exception as e:
        # Mark recipient as failed, continue to next
        db.rollback()
        recipient.status = FAILED
        job.processed_count += 1
        job.failed_count += 1
        db.commit()
```

Key points:
- The `try/except` is around **each recipient**, not the whole loop
- After a failure, we `rollback()` to undo any partial state, then explicitly mark the failure
- The loop continues to the next recipient

---

## 6. How Progress Is Calculated

```python
progress_percentage = (processed_count / total_recipients) * 100
```

- `total_recipients` is set when the job is created
- `processed_count` increments after each recipient (success or failure)
- `successful_count` and `failed_count` are updated atomically with each commit

The client can poll `GET /api/jobs/{id}` to see real-time progress.

---

## 7. How PDF Generation Works

1. `PDFService.generate_pdf()` creates a ReportLab Canvas (landscape A4)
2. Calls `draw_certificate()` from the template module, which draws:
   - Decorative borders and corner ornaments
   - Organization name, certificate title, recipient name
   - Event name, issue date, signature area, certificate ID
3. The canvas is saved to `generated_certificates/certificate_{uuid}.pdf`
4. The file path and name are returned and stored in the Certificate DB record

---

## 8. How SQLAlchemy Sessions Are Managed

**Request-scoped sessions:** The `get_db()` dependency yields a session per request and closes it in the `finally` block. FastAPI's dependency injection handles this automatically.

**Background task sessions:** The `process_job()` method creates its own session via `SessionLocal()` because background tasks run after the request session is closed. This is critical — sharing the request session with a background task would cause threading issues and stale data.

```python
def process_job(self, job_id: str) -> None:
    db = SessionLocal()  # Fresh session for background work
    try:
        # ... process all recipients ...
    finally:
        db.close()  # Always close when done
```

---

## 9. How the API Is Tested

- Tests use **SQLite** (not PostgreSQL) for speed and isolation
- The `conftest.py` overrides `get_db` to use a test session factory
- It also patches `SessionLocal` in the job service module so background tasks use the test DB
- `TestClient` from FastAPI executes background tasks **synchronously**, so assertions can verify the final state immediately
- Tables are created before each test and dropped after, ensuring isolation

---

## 10. What Happens If 1 Certificate Fails?

Example: 100 recipients, the 5th one fails.

1. Recipients 1–4: generated successfully, `successful_count = 4`
2. Recipient 5: PDF generation raises an exception
3. The exception is caught, recipient 5 is marked FAILED with an error message
4. `failed_count = 1`, `processed_count = 5`
5. Recipients 6–100: continue processing normally
6. Final: `successful_count = 99`, `failed_count = 1`
7. Job status: `PARTIALLY_COMPLETED`

---

## 11. What Happens If 1000 Certificates Are Submitted?

The API responds immediately with the job ID (< 100ms). The background task processes all 1000 recipients sequentially. Each PDF takes a few milliseconds to generate, so the whole job might take ~5–10 seconds.

Limitations at this scale:
- Processing is sequential (could be parallelised)
- If the server restarts, the job is lost (no persistent task queue)
- Memory usage scales linearly with recipient count during processing

For 10,000+ certificates, you'd want Celery workers processing in parallel.

---

## 12. What Would You Change for Production?

1. **Celery + Redis** for reliable, distributed background processing
2. **S3/GCS** for certificate storage (not local filesystem)
3. **Authentication** (JWT/OAuth2) to secure endpoints
4. **Rate limiting** to prevent abuse
5. **Retry logic** for transient failures
6. **Pagination** for large certificate lists
7. **Structured logging** with correlation IDs
8. **Health checks** with database connectivity verification
9. **CI/CD pipeline** with automated testing
10. **Monitoring** — Prometheus metrics, Grafana dashboards

---

## 13. How You Would Scale the System

```
                    Load Balancer
                    /     |     \
                API-1  API-2  API-3    (stateless FastAPI instances)
                    \     |     /
                    PostgreSQL (RDS)
                    /     |     \
              Worker-1 Worker-2 Worker-3  (Celery workers)
                    \     |     /
                    Redis (task queue)
                         |
                    S3 (certificate storage)
```

- Multiple API instances behind a load balancer
- Celery workers pulling tasks from Redis
- S3 for certificate storage (shared across workers)
- PostgreSQL on managed service (RDS) for reliability

---

## 14. Why Celery/Redis Could Be Introduced Later

Current architecture uses in-process background tasks. This works but has limitations:
- Tasks don't survive server restarts
- No retry on failure
- No task prioritisation
- Can't distribute work across multiple machines

Celery solves all of these by moving task execution to separate worker processes that pull from a message broker (Redis/RabbitMQ). The API just enqueues a task and returns.

---

## 15. Possible Weaknesses of the Current Implementation

1. **No authentication** — anyone can create jobs and download certificates
2. **Sequential processing** — could be parallelised for speed
3. **No persistent task queue** — server restart loses in-progress jobs
4. **Local filesystem** — doesn't work in multi-server deployments
5. **No retry mechanism** — a transient failure permanently marks a certificate as failed
6. **No pagination** — listing certificates for a job with 10,000 recipients returns all at once
7. **Race conditions** — unlikely with BackgroundTasks (single-threaded), but counters aren't using SQL `UPDATE ... SET count = count + 1` which would be safer under concurrent access
8. **No request size limit** — a malicious client could send millions of recipients
