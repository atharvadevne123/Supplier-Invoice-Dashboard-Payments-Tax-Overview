"""Tests for the bulk import parser module."""

import pytest
from decimal import Decimal

from app.bulk import BulkImportError, parse_csv_invoices, parse_json_invoices


CSV_VALID = """invoice_number,business_unit,supplier,invoice_date,invoice_amount,amount_paid,currency,payment_status
INV-001,Finance BU,Acme,2025-01-15,1000.00,0.00,USD,UNPAID
INV-002,IT BU,Beta,2025-02-20,2500.50,2500.50,EUR,PAID"""


def test_parse_csv_valid() -> None:
    rows = parse_csv_invoices(CSV_VALID)
    assert len(rows) == 2
    assert rows[0]["invoice_number"] == "INV-001"
    assert rows[0]["invoice_amount"] == Decimal("1000.00")


def test_parse_csv_missing_column() -> None:
    bad_csv = "invoice_number,supplier\nINV-001,Acme"
    with pytest.raises(BulkImportError, match="missing columns"):
        parse_csv_invoices(bad_csv)


def test_parse_csv_invalid_amount() -> None:
    bad_csv = CSV_VALID.replace("1000.00", "not-a-number")
    with pytest.raises(BulkImportError, match="invalid decimal"):
        parse_csv_invoices(bad_csv)


def test_parse_json_valid() -> None:
    import json
    data = [
        {
            "invoice_number": "INV-001",
            "business_unit": "BU",
            "supplier": "X",
            "invoice_amount": 500.0,
            "amount_paid": 0.0,
        }
    ]
    rows = parse_json_invoices(json.dumps(data))
    assert len(rows) == 1
    assert rows[0]["invoice_amount"] == Decimal("500.0")


def test_parse_json_invalid_json() -> None:
    with pytest.raises(BulkImportError, match="Invalid JSON"):
        parse_json_invoices("not json {")


def test_parse_json_not_list() -> None:
    import json
    with pytest.raises(BulkImportError, match="array"):
        parse_json_invoices(json.dumps({"key": "value"}))
