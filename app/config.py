"""Application configuration loaded from environment variables."""

import os

from pydantic_settings import BaseSettings


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

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
