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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_SEPARATOR = "=" * 60


def _section(title: str) -> None:
    """Log a formatted section header at INFO level."""
    logger.info(_SEPARATOR)
    logger.info("  %s", title)
    logger.info(_SEPARATOR)


def run_dashboard() -> None:
    """Fetch all invoices and log analytics to the configured handler."""
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
            logger.info("  %-30s: %s", key, val)

        _section("PAYMENT STATUS DISTRIBUTION")
        dist = payment_status_distribution(inv_dicts)
        for status, count in sorted(dist.items()):
            logger.info("  %-20s: %d", status, count)

        _section("TOP 10 SUPPLIERS BY OUTSTANDING")
        ranking = supplier_outstanding_ranking(inv_dicts)[:10]
        for i, entry in enumerate(ranking, 1):
            logger.info(
                "  %2d. %-40s  %12,.2f",
                i,
                entry["supplier"][:40],
                entry["total_outstanding"],
            )

        _section("CURRENCY BREAKDOWN")
        for entry in currency_breakdown(inv_dicts):
            logger.info("  %-5s: %14,.2f", entry["currency"], entry["total_amount"])

        _section("OVERDUE INVOICES (>30 days)")
        overdue = overdue_invoices(inv_dicts)
        if overdue:
            for inv in overdue[:10]:
                logger.info(
                    "  %-15s  %-30s  %4d days  %12,.2f",
                    inv["invoice_number"],
                    inv["supplier"][:30],
                    inv["age_days"],
                    inv["invoice_amount"],
                )
        else:
            logger.info("  No overdue invoices.")

        logger.info("Dashboard complete: %d invoices processed", len(inv_dicts))
    finally:
        db.close()


if __name__ == "__main__":
    run_dashboard()
