"""CertiFlow — Bulk Certificate Generator API.

FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.jobs import router as jobs_router
from app.api.certificates import router as certificates_router
from app.core.config import settings
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings.ensure_directories()
    logger.info("CertiFlow started (env=%s)", settings.APP_ENV)
    yield
    logger.info("CertiFlow shutting down")


app = FastAPI(
    title="CertiFlow — Bulk Certificate Generator",
    description=(
        "A production-quality REST API for generating certificates in bulk. "
        "Submit a list of recipients and track certificate generation progress "
        "in real time."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Register routers ────────────────────────────────────────────
app.include_router(jobs_router)
app.include_router(certificates_router)


# ── Global exception handler ───────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return a safe JSON response."""
    logger.error("Unhandled exception: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )


# ── Health check ────────────────────────────────────────────────
@app.get("/health", tags=["Health"], summary="Health check")
def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "healthy", "service": "CertiFlow"}
