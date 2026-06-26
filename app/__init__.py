"""Supplier Invoice Dashboard — FastAPI application package.

Modules:
  main        - FastAPI app factory, route handlers
  config      - Pydantic settings loaded from environment
  database    - SQLAlchemy ORM models and session management
  schemas     - Pydantic request/response models
  features    - Tax, outstanding, and payment-status computations
  analytics   - Supplier ranking, trends, overdue detection
  reporting   - OTBI-style table-view and graph-view builders
  middleware  - Correlation-ID and access-log middleware
  rate_limit  - In-memory IP-based rate limiting
  cache       - TTL decorator for expensive aggregations
  bulk        - CSV/JSON batch import parsers
  currency    - Exchange-rate normalization utilities
  validators  - Domain-level input validation helpers
  utils       - Pagination, formatting, and misc helpers
  exceptions  - Custom exception classes and FastAPI handlers
"""

__version__ = "1.0.0"
