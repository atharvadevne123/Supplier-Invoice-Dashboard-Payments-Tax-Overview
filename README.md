# Supplier Invoice Dashboard — Payments & Tax Overview

![CI](https://github.com/atharvadevne123/Supplier-Invoice-Dashboard-Payments-Tax-Overview/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

REST API that replicates Oracle OTBI Payables reporting — providing table-view and graph-view analytics for supplier invoices, including tax computation, outstanding balance tracking, and payment-status dashboards.

## Features

- **Invoice CRUD** — create, retrieve, and paginate supplier invoices
- **Computed fields** — tax (configurable rate), outstanding balance, colour labels
- **Analytics** — supplier outstanding ranking, monthly trends, overdue detection, currency breakdown
- **View Selector** — table-view and graph-view payloads matching the OTBI dashboard design
- **Filtering** — by supplier, business unit, payment status, currency
- **PostgreSQL + SQLite** — swap via `DATABASE_URL` env var
- **Docker** — single-command `docker-compose up` startup

## Quick Start

```bash
git clone https://github.com/atharvadevne123/Supplier-Invoice-Dashboard-Payments-Tax-Overview.git
cd Supplier-Invoice-Dashboard-Payments-Tax-Overview
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

## Docker

```bash
docker-compose up --build -d
```

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Liveness + DB status |
| GET | `/api/v1/version` | API version |
| GET | `/api/v1/invoices` | List invoices (paginated, filterable) |
| POST | `/api/v1/invoices` | Create invoice |
| GET | `/api/v1/invoices/{id}` | Get single invoice |
| GET | `/api/v1/summary` | Aggregated statistics |
| GET | `/api/v1/analytics/supplier-ranking` | Suppliers by outstanding balance |
| GET | `/api/v1/analytics/monthly-trend` | Monthly invoice/payment totals |
| GET | `/api/v1/analytics/overdue` | Overdue unpaid/partial invoices |
| GET | `/api/v1/analytics/currency-breakdown` | Totals by currency |
| GET | `/api/v1/analytics/status-distribution` | Count by payment status |
| GET | `/api/v1/analytics/currency-normalized` | Invoices normalized to USD |
| PATCH | `/api/v1/invoices/{id}` | Update payment amount/status |
| DELETE | `/api/v1/invoices/{id}` | Delete invoice |
| GET | `/api/v1/report/view-selector` | OTBI dual table+graph payload |
| GET | `/api/v1/metrics` | Operational monitoring metrics |

Interactive docs: `http://localhost:8000/docs`

## Testing

```bash
make test
```

## Environment Variables

See `.env.example` for all supported variables. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./supplier_invoices.db` | Database connection string |
| `TAX_RATE` | `0.08` | Invoice tax rate (decimal) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Architecture

```
app/
├── main.py          FastAPI routes
├── database.py      SQLAlchemy models + session
├── schemas.py       Pydantic request/response models
├── features.py      Tax, outstanding, status logic
├── analytics.py     Trends, ranking, overdue detection
├── reporting.py     Table/graph view builders
├── middleware.py    Correlation-ID logging
├── utils.py         Pagination, formatting helpers
├── cache.py         TTL in-memory caching
├── currency.py      Exchange-rate conversion
├── validators.py    Domain input validators
├── bulk.py          CSV/JSON bulk import parser
├── exceptions.py    Custom exceptions and handlers
├── rate_limit.py    Per-IP rate limiting
└── config.py        Settings from env vars
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
