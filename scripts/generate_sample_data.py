"""Seed the database with realistic supplier invoice sample data."""

import logging
import os
import random
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session

from app.database import SessionLocal, SupplierInvoice, create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPLIERS = [
    "Acme Industrial Supplies",
    "Beta Tech Solutions",
    "Gamma Logistics Ltd",
    "Delta Manufacturing Co",
    "Epsilon Software Inc",
    "Zeta Consulting Group",
    "Eta Procurement Services",
    "Theta Global Trading",
    "Iota Infrastructure LLC",
    "Kappa Engineering Works",
]

BUSINESS_UNITS = [
    "Finance BU",
    "Operations BU",
    "IT Department",
    "Procurement",
    "Legal & Compliance",
    "Human Resources",
]
CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "CHF"]
STATUSES = ["PAID", "UNPAID", "PARTIAL", "CANCELLED"]
STATUS_WEIGHTS = [0.45, 0.30, 0.20, 0.05]


def _random_invoice(index: int) -> SupplierInvoice:
    """Generate a single randomised SupplierInvoice record.

    Args:
        index: Sequential invoice index used to build the invoice number.

    Returns:
        Unsaved SupplierInvoice ORM instance.
    """
    invoice_amount = Decimal(str(round(random.uniform(500, 50000), 2)))
    status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
    amount_paid: Decimal
    if status == "PAID":
        amount_paid = invoice_amount
    elif status == "PARTIAL":
        amount_paid = (invoice_amount * Decimal(str(round(random.uniform(0.1, 0.9), 2)))).quantize(
            Decimal("0.01")
        )
    else:
        amount_paid = Decimal("0.00")
    return SupplierInvoice(
        invoice_number=f"INV-{2025000 + index}",
        business_unit=random.choice(BUSINESS_UNITS),
        supplier=random.choice(SUPPLIERS),
        invoice_date=date.today() - timedelta(days=random.randint(0, 365)),
        invoice_amount=invoice_amount,
        amount_paid=amount_paid,
        currency=random.choice(CURRENCIES),
        payment_status=status,
    )


def seed(count: int = 100) -> None:
    """Insert ``count`` sample invoices into the database.

    Skips seeding if the database already contains any records.

    Args:
        count: Number of sample invoices to insert (default 100).
    """
    create_tables()
    db: Session = SessionLocal()
    try:
        existing = db.query(SupplierInvoice).count()
        if existing > 0:
            logger.info("Database already contains %d invoices — skipping seed", existing)
            return
        invoices = [_random_invoice(i) for i in range(1, count + 1)]
        db.add_all(invoices)
        db.commit()
        logger.info("Inserted %d sample invoices", count)
    except Exception:
        db.rollback()
        logger.exception("Failed to seed database")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed(count)
