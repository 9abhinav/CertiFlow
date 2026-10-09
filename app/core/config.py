"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central configuration for the application."""

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/certificates",
    )
    APP_ENV: str = os.getenv("APP_ENV", "development")
    GENERATED_FILES_DIR: str = os.getenv("GENERATED_FILES_DIR", "generated_certificates")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Ensure the generated certificates directory exists
    @staticmethod
    def ensure_directories() -> None:
        """Create required directories if they don't exist."""
        Path(settings.GENERATED_FILES_DIR).mkdir(parents=True, exist_ok=True)


settings = Settings()
