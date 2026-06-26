"""Pytest fixtures for the Supplier Invoice Dashboard test suite."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
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
def paid_invoice_data() -> dict:
    """Return a valid invoice payload dict for a fully paid invoice."""
    return {
        "invoice_number": "INV-PAID-001",
        "business_unit": "Operations BU",
        "supplier": "Beta Corp",
        "invoice_date": "2025-03-10",
        "invoice_amount": "2000.00",
        "amount_paid": "2000.00",
        "currency": "EUR",
        "payment_status": "PAID",
    }


@pytest.fixture
def overdue_invoice_data() -> dict:
    """Return an invoice payload dict that is overdue (60 days old, unpaid)."""
    from datetime import date, timedelta

    old_date = (date.today() - timedelta(days=60)).isoformat()
    return {
        "invoice_number": "INV-OVERDUE-001",
        "business_unit": "Finance BU",
        "supplier": "Old Creditor Ltd",
        "invoice_date": old_date,
        "invoice_amount": "5000.00",
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
