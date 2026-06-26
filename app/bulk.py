"""Bulk invoice import utilities for batch loading from CSV/JSON."""

import csv
import io
import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_CSV_COLUMNS: frozenset[str] = frozenset({
    "invoice_number", "business_unit", "supplier",
    "invoice_date", "invoice_amount", "amount_paid",
    "currency", "payment_status",
})


class BulkImportError(Exception):
    """Raised when bulk import encounters unrecoverable data errors."""


def _normalize_csv_header(fieldnames: list[str]) -> list[str]:
    """Strip whitespace and lowercase all CSV column names for consistent matching.

    Args:
        fieldnames: Raw column names from the CSV header row.

    Returns:
        Normalised (stripped, lowercased) column names.
    """
    return [f.strip().lower() for f in fieldnames if f is not None]


def parse_csv_invoices(csv_content: str) -> list[dict[str, Any]]:
    """Parse a CSV string into a list of invoice dicts.

    Expected columns (case-insensitive): invoice_number, business_unit, supplier,
    invoice_date, invoice_amount, amount_paid, currency, payment_status.

    Args:
        csv_content: Raw CSV text including header row.

    Returns:
        List of invoice dicts with Decimal amounts.

    Raises:
        BulkImportError: On missing columns or invalid decimal amounts.
    """
    reader = csv.DictReader(io.StringIO(csv_content.strip()))
    raw_fieldnames = list(reader.fieldnames or [])
    normalized_names = _normalize_csv_header(raw_fieldnames)
    missing = REQUIRED_CSV_COLUMNS - set(normalized_names)
    if missing:
        raise BulkImportError(f"CSV missing required columns: {missing}")

    rows = []
    for i, raw_row in enumerate(reader, start=1):
        row = {k.strip().lower(): v for k, v in raw_row.items() if k is not None}
        try:
            row["invoice_amount"] = Decimal(row["invoice_amount"].strip())
            row["amount_paid"] = Decimal(row["amount_paid"].strip())
        except (InvalidOperation, AttributeError) as e:
            raise BulkImportError(f"Row {i}: invalid decimal amount — {e}") from e
        rows.append(row)
    logger.info("Parsed %d rows from CSV", len(rows))
    return rows


def validate_csv_row(row: dict[str, Any], row_index: int) -> list[str]:
    """Run basic domain validation on a parsed CSV row.

    Args:
        row: Invoice dict from parse_csv_invoices with normalized keys.
        row_index: 1-based row index used in error messages.

    Returns:
        List of error strings (empty if the row is valid).
    """
    errors: list[str] = []
    from decimal import Decimal as _D
    invoice_amount = row.get("invoice_amount")
    amount_paid = row.get("amount_paid")
    if isinstance(invoice_amount, _D) and invoice_amount <= _D("0"):
        errors.append(f"Row {row_index}: invoice_amount must be greater than zero")
    if isinstance(amount_paid, _D) and isinstance(invoice_amount, _D):
        if amount_paid < _D("0"):
            errors.append(f"Row {row_index}: amount_paid must not be negative")
        elif amount_paid > invoice_amount:
            errors.append(f"Row {row_index}: amount_paid cannot exceed invoice_amount")
    return errors


def merge_invoice_dicts(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Merge update fields into base, skipping keys with None values.

    Useful for applying partial updates from bulk imports without
    overwriting existing values with missing fields.

    Args:
        base: Existing invoice dict.
        update: Partial dict of fields to apply.

    Returns:
        New dict with update values applied over base.
    """
    return {**base, **{k: v for k, v in update.items() if v is not None}}


def parse_json_invoices(json_content: str) -> list[dict[str, Any]]:
    """Parse a JSON string (list of objects) into a list of invoice dicts.

    Args:
        json_content: Raw JSON text representing an array of invoice objects.

    Returns:
        List of invoice dicts with Decimal amounts for invoice_amount and amount_paid.

    Raises:
        BulkImportError: On invalid JSON or non-array root.
    """
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        raise BulkImportError(f"Invalid JSON: {e}") from e
    if not isinstance(data, list):
        raise BulkImportError("JSON root must be an array of invoice objects")
    for i, item in enumerate(data):
        if item is None:
            logger.warning("JSON record %d is null — skipping", i)
            continue
        if "invoice_amount" in item and item["invoice_amount"] is not None:
            item["invoice_amount"] = Decimal(str(item["invoice_amount"]))
        if "amount_paid" in item and item["amount_paid"] is not None:
            item["amount_paid"] = Decimal(str(item["amount_paid"]))
    logger.info("Parsed %d records from JSON", len(data))
    return data
