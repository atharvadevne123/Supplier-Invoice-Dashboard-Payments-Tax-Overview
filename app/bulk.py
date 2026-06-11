"""Bulk invoice import utilities for batch loading from CSV/JSON."""

import csv
import io
import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

logger = logging.getLogger(__name__)


class BulkImportError(Exception):
    """Raised when bulk import encounters unrecoverable data errors."""


def parse_csv_invoices(csv_content: str) -> list[dict[str, Any]]:
    """Parse a CSV string into a list of invoice dicts.

    Expected columns: invoice_number, business_unit, supplier, invoice_date,
    invoice_amount, amount_paid, currency, payment_status
    """
    reader = csv.DictReader(io.StringIO(csv_content.strip()))
    required = {
        "invoice_number", "business_unit", "supplier",
        "invoice_date", "invoice_amount", "amount_paid",
        "currency", "payment_status",
    }
    rows = []
    for i, row in enumerate(reader, start=1):
        missing = required - set(row.keys())
        if missing:
            raise BulkImportError(f"Row {i}: missing columns {missing}")
        try:
            row["invoice_amount"] = Decimal(row["invoice_amount"])
            row["amount_paid"] = Decimal(row["amount_paid"])
        except InvalidOperation as e:
            raise BulkImportError(f"Row {i}: invalid decimal amount — {e}") from e
        rows.append(dict(row))
    logger.info("Parsed %d rows from CSV", len(rows))
    return rows


def parse_json_invoices(json_content: str) -> list[dict[str, Any]]:
    """Parse a JSON string (list of objects) into a list of invoice dicts."""
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        raise BulkImportError(f"Invalid JSON: {e}") from e
    if not isinstance(data, list):
        raise BulkImportError("JSON root must be an array of invoice objects")
    for i, item in enumerate(data):
        if "invoice_amount" in item:
            item["invoice_amount"] = Decimal(str(item["invoice_amount"]))
        if "amount_paid" in item:
            item["amount_paid"] = Decimal(str(item["amount_paid"]))
    logger.info("Parsed %d records from JSON", len(data))
    return data
