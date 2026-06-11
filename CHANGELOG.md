# Changelog

All notable changes to this project will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-06-11

### Added
- FastAPI REST API with `/api/v1/invoices`, `/summary`, and analytics endpoints
- SQLAlchemy ORM models for supplier invoices with PostgreSQL/SQLite support
- Pydantic v2 request/response schemas with field validation
- Feature engineering: tax computation, outstanding balance, payment status derivation
- Analytics module: supplier ranking, monthly trends, overdue detection, currency breakdown
- Report builder for OTBI-style table view and graph view data
- Correlation-ID logging middleware for request tracing
- Docker + docker-compose configuration with PostgreSQL
- Sample data seeding script and CSV/JSON export utilities
- Comprehensive pytest test suite with parametrized fixtures
- GitHub Actions CI pipeline with ruff lint and pytest
- pyproject.toml, Makefile, .pre-commit-config.yaml developer tooling
