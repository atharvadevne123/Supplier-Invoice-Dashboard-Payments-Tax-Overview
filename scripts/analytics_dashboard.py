"""Command-line analytics dashboard: print a summary report to stdout."""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.analytics import (
    currency_breakdown,
    overdue_invoices,
    payment_status_distribution,
    supplier_outstanding_ranking,
)
from app.database import SessionLocal, SupplierInvoice, create_tables
from app.features import aggregate_invoices

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def _section(title: str) -> None:
    """Print a formatted section header."""
    width = 60
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}")


def run_dashboard() -> None:
    """Fetch all invoices and print analytics to stdout."""
    create_tables()
    db = SessionLocal()
    try:
        records = db.query(SupplierInvoice).all()
        inv_dicts = [
            {
                "invoice_number": r.invoice_number,
                "supplier": r.supplier,
                "invoice_date": r.invoice_date,
                "invoice_amount": r.invoice_amount,
                "amount_paid": r.amount_paid,
                "currency": r.currency,
                "payment_status": r.payment_status,
            }
            for r in records
        ]

        _section("INVOICE SUMMARY")
        agg = aggregate_invoices(inv_dicts)
        for key, val in agg.items():
            print(f"  {key:30s}: {val}")

        _section("PAYMENT STATUS DISTRIBUTION")
        dist = payment_status_distribution(inv_dicts)
        for status, count in sorted(dist.items()):
            print(f"  {status:20s}: {count}")

        _section("TOP 10 SUPPLIERS BY OUTSTANDING")
        ranking = supplier_outstanding_ranking(inv_dicts)[:10]
        for i, entry in enumerate(ranking, 1):
            print(f"  {i:2d}. {entry['supplier'][:40]:40s}  {entry['total_outstanding']:>12,.2f}")

        _section("CURRENCY BREAKDOWN")
        for entry in currency_breakdown(inv_dicts):
            print(f"  {entry['currency']:5s}: {entry['total_amount']:>14,.2f}")

        _section("OVERDUE INVOICES (>30 days)")
        overdue = overdue_invoices(inv_dicts)
        if overdue:
            for inv in overdue[:10]:
                print(
                    f"  {inv['invoice_number']:15s}  {inv['supplier'][:30]:30s}"
                    f"  {inv['age_days']:4d} days  {inv['invoice_amount']:>12,.2f}"
                )
        else:
            print("  No overdue invoices.")

    finally:
        db.close()


if __name__ == "__main__":
    run_dashboard()
