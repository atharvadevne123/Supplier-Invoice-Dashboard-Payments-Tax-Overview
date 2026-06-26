"""Tests for database models and session utilities."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.database import Base, SupplierInvoice


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db, engine
    db.close()
    Base.metadata.drop_all(bind=engine)


def test_table_created(in_memory_db) -> None:
    _, engine = in_memory_db
    inspector = inspect(engine)
    assert "supplier_invoices" in inspector.get_table_names()


def test_insert_and_retrieve(in_memory_db) -> None:
    db, _ = in_memory_db
    inv = SupplierInvoice(
        invoice_number="INV-TEST-001",
        business_unit="Finance BU",
        supplier="Test Supplier",
        invoice_date=date(2025, 1, 15),
        invoice_amount=Decimal("1000.00"),
        amount_paid=Decimal("0.00"),
        currency="USD",
        payment_status="UNPAID",
    )
    db.add(inv)
    db.commit()

    fetched = db.query(SupplierInvoice).filter_by(invoice_number="INV-TEST-001").first()
    assert fetched is not None
    assert fetched.supplier == "Test Supplier"
    assert fetched.invoice_amount == Decimal("1000.00")


def test_default_amount_paid(in_memory_db) -> None:
    db, _ = in_memory_db
    inv = SupplierInvoice(
        invoice_number="INV-DEF-001",
        business_unit="IT",
        supplier="Acme",
        invoice_date=date(2025, 3, 1),
        invoice_amount=Decimal("500.00"),
        currency="USD",
        payment_status="UNPAID",
    )
    db.add(inv)
    db.commit()
    fetched = db.query(SupplierInvoice).filter_by(invoice_number="INV-DEF-001").first()
    assert fetched.amount_paid == Decimal("0.00")


def test_indexes_created(in_memory_db) -> None:
    _, engine = in_memory_db
    inspector = inspect(engine)
    index_names = {idx["name"] for idx in inspector.get_indexes("supplier_invoices")}
    assert "ix_invoice_supplier_date" in index_names
    assert "ix_invoice_status" in index_names
    assert "ix_invoice_bu_status" in index_names


def test_invoice_number_is_primary_key(in_memory_db) -> None:
    db, _ = in_memory_db
    inv1 = SupplierInvoice(
        invoice_number="INV-DUP",
        business_unit="X",
        supplier="S",
        invoice_date=date(2025, 1, 1),
        invoice_amount=Decimal("100.00"),
        currency="USD",
        payment_status="UNPAID",
    )
    inv2 = SupplierInvoice(
        invoice_number="INV-DUP",
        business_unit="Y",
        supplier="T",
        invoice_date=date(2025, 2, 1),
        invoice_amount=Decimal("200.00"),
        currency="USD",
        payment_status="UNPAID",
    )
    db.add(inv1)
    db.commit()
    db.add(inv2)
    with pytest.raises(Exception):
        db.commit()
