"""File utility functions for safe path handling."""

import re
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from a filename.

    Keeps only alphanumeric characters, hyphens, underscores, and dots.
    """
    sanitized = re.sub(r"[^\w\-.]", "_", filename)
    # Prevent path traversal
    sanitized = sanitized.replace("..", "_")
    return sanitized


def ensure_directory(directory: str) -> Path:
    """Create a directory if it doesn't exist and return the Path object."""
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    return path
