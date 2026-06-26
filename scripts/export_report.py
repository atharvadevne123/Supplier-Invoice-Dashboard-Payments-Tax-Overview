"""Export supplier invoice summary to CSV and JSON for offline analysis."""

import csv
import json
import logging
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import SessionLocal, SupplierInvoice, create_tables
from app.features import compute_outstanding, compute_tax

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _invoice_to_dict(inv: SupplierInvoice) -> dict:
    """Convert an ORM invoice to a serialisable dict with computed fields."""
    tax = compute_tax(inv.invoice_amount)
    outstanding = compute_outstanding(inv.invoice_amount, inv.amount_paid)
    return {
        "invoice_number": inv.invoice_number,
        "business_unit": inv.business_unit,
        "supplier": inv.supplier,
        "invoice_date": str(inv.invoice_date),
        "invoice_amount": str(inv.invoice_amount),
        "amount_paid": str(inv.amount_paid),
        "tax_amount": str(tax),
        "outstanding_amount": str(outstanding),
        "currency": inv.currency,
        "payment_status": inv.payment_status,
    }


def get_report_path(base_name: str, output_dir: str = ".") -> str:
    """Build a full output file path under output_dir.

    Args:
        base_name: File name (e.g. "invoice_report.csv").
        output_dir: Directory to write to (default current directory).

    Returns:
        Absolute path string combining output_dir and base_name.
    """
    import os

    return os.path.join(os.path.abspath(output_dir), base_name)


def export_csv(output_path: str = "invoice_report.csv") -> None:
    """Write all invoices to a CSV file at output_path."""
    create_tables()
    db = SessionLocal()
    try:
        invoices = db.query(SupplierInvoice).all()
        if not invoices:
            logger.warning("No invoices found in database")
            return
        rows = [_invoice_to_dict(inv) for inv in invoices]
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        logger.info("Exported %d invoices to %s", len(rows), output_path)
    except Exception:
        logger.exception("CSV export failed")
        raise
    finally:
        db.close()


def export_json(output_path: str = "invoice_report.json") -> None:
    """Write all invoices to a JSON file at output_path."""
    create_tables()
    db = SessionLocal()
    try:
        invoices = db.query(SupplierInvoice).all()
        rows = [_invoice_to_dict(inv) for inv in invoices]
        with open(output_path, "w") as f:
            json.dump({"generated_at": str(date.today()), "invoices": rows}, f, indent=2)
        logger.info("Exported %d invoices to %s", len(rows), output_path)
    except Exception:
        logger.exception("JSON export failed")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fmt = sys.argv[1] if len(sys.argv) > 1 else "csv"
    if fmt == "json":
        export_json()
    else:
        export_csv()
