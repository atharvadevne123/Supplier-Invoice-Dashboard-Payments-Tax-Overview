"""Application configuration loaded from environment variables.

Environment variables (all optional, with defaults):
  DATABASE_URL  - SQLAlchemy connection string (default: SQLite file)
  TAX_RATE      - Decimal tax rate 0.0–1.0 (default: 0.08)
  LOG_LEVEL     - Python logging level name (default: INFO)
  RATE_LIMIT    - Requests per window per IP (default: 100)
  WINDOW_SECONDS - Rate-limit window in seconds (default: 60)
  DEBUG         - Enable debug mode (default: false)
"""

import os

from pydantic import field_validator
from pydantic_settings import BaseSettings

_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class Settings(BaseSettings):
    """Runtime configuration for the Supplier Invoice Dashboard API."""

    app_name: str = "Supplier Invoice Dashboard"
    app_version: str = "1.0.0"
    debug: bool = False
    database_url: str = os.environ.get(
        "DATABASE_URL", "sqlite:///./supplier_invoices.db"
    )
    tax_rate: float = float(os.environ.get("TAX_RATE", "0.08"))
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]
    rate_limit: int = int(os.environ.get("RATE_LIMIT", "100"))
    window_seconds: int = int(os.environ.get("WINDOW_SECONDS", "60"))

    @field_validator("tax_rate")
    @classmethod
    def tax_rate_must_be_valid(cls, v: float) -> float:
        """Ensure tax_rate is between 0 and 1 inclusive."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"tax_rate must be between 0 and 1, got {v}")
        return v

    @field_validator("log_level")
    @classmethod
    def log_level_must_be_valid(cls, v: str) -> str:
        """Ensure log_level is a recognised Python logging level."""
        upper = v.upper()
        if upper not in _VALID_LOG_LEVELS:
            raise ValueError(f"log_level must be one of {_VALID_LOG_LEVELS}, got {v!r}")
        return upper

    class Config:
        """Pydantic settings config: read from .env file, case-insensitive keys."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()
