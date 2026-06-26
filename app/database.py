"""SQLAlchemy database models and session management."""

import logging
from datetime import date
from decimal import Decimal
from typing import Generator

from sqlalchemy import (
    Column,
    Date,
    Index,
    Numeric,
    String,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class SupplierInvoice(Base):
    """ORM model representing a single supplier invoice record."""

    __tablename__ = "supplier_invoices"

    invoice_number: str = Column(String(50), primary_key=True, index=True)  # type: ignore[assignment]
    business_unit: str = Column(String(100), nullable=False, index=True)  # type: ignore[assignment]
    supplier: str = Column(String(200), nullable=False, index=True)  # type: ignore[assignment]
    invoice_date: date = Column(Date, nullable=False, index=True)  # type: ignore[assignment]
    invoice_amount: Decimal = Column(Numeric(18, 2), nullable=False)  # type: ignore[assignment]
    amount_paid: Decimal = Column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))  # type: ignore[assignment]
    currency: str = Column(String(10), nullable=False, default="USD")  # type: ignore[assignment]
    payment_status: str = Column(String(50), nullable=False, default="UNPAID")  # type: ignore[assignment]

    __table_args__ = (
        Index("ix_invoice_supplier_date", "supplier", "invoice_date"),
        Index("ix_invoice_status", "payment_status"),
        Index("ix_invoice_bu_status", "business_unit", "payment_status"),
    )


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Yield a database session and close it after use.

    Yields:
        Active SQLAlchemy Session.

    Raises:
        Exception: Rolls back the session before re-raising any database error.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        logger.exception("Database session error")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> None:
    """Create all database tables if they do not exist.

    Raises:
        Exception: If the underlying CREATE TABLE statements fail.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created or verified")
    except Exception:
        logger.exception("Failed to create database tables")
        raise


def check_db_connection() -> bool:
    """Verify database connectivity by executing a trivial query.

    Returns:
        True if the database is reachable, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("Database connectivity check failed")
        return False
