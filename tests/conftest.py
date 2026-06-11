"""Pytest fixtures for the Supplier Invoice Dashboard test suite."""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, SupplierInvoice, get_db
from app.main import app


TEST_DB_URL = "sqlite:///./test_invoices.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Provide a test database session."""
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create fresh tables and yield a session; tear down after each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Return a TestClient with the test database wired in."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_invoice_data() -> dict:
    """Return a valid invoice payload dict."""
    return {
        "invoice_number": "INV-001",
        "business_unit": "Finance BU",
        "supplier": "Acme Corp",
        "invoice_date": "2025-01-15",
        "invoice_amount": "1000.00",
        "amount_paid": "0.00",
        "currency": "USD",
        "payment_status": "UNPAID",
    }


@pytest.fixture
def seed_invoices(db_session):
    """Insert a small set of invoices for aggregate-query tests."""
    today = date.today()
    invoices = [
        SupplierInvoice(
            invoice_number=f"INV-{i:03d}",
            business_unit="BU-A",
            supplier="Supplier X" if i % 2 == 0 else "Supplier Y",
            invoice_date=today - timedelta(days=i * 10),
            invoice_amount=Decimal(f"{1000 + i * 100}.00"),
            amount_paid=Decimal("0.00") if i % 3 != 0 else Decimal(f"{1000 + i * 100}.00"),
            currency="USD",
            payment_status="UNPAID" if i % 3 != 0 else "PAID",
        )
        for i in range(1, 6)
    ]
    db_session.add_all(invoices)
    db_session.commit()
    return invoices
