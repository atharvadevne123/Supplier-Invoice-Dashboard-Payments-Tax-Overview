"""Tests for the bulk import parser module."""

from decimal import Decimal

import pytest

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


def test_parse_csv_case_insensitive_columns() -> None:
    csv_content = """Invoice_Number,Business_Unit,Supplier,Invoice_Date,Invoice_Amount,Amount_Paid,Currency,Payment_Status
INV-CI-001,BU,Acme,2025-01-01,100.00,0.00,USD,UNPAID"""
    rows = parse_csv_invoices(csv_content)
    assert rows[0]["invoice_number"] == "INV-CI-001"


def test_parse_json_null_record_skipped() -> None:
    import json

    data = [None, {"invoice_number": "INV-001", "invoice_amount": 100.0, "amount_paid": 0.0}]
    rows = parse_json_invoices(json.dumps(data))
    assert len(rows) == 2


def test_parse_json_null_amounts_preserved() -> None:
    import json

    data = [{"invoice_number": "INV-002", "invoice_amount": None, "amount_paid": None}]
    rows = parse_json_invoices(json.dumps(data))
    assert rows[0]["invoice_amount"] is None


def test_validate_csv_row_valid() -> None:
    from decimal import Decimal

    from app.bulk import validate_csv_row

    row = {"invoice_amount": Decimal("100.00"), "amount_paid": Decimal("50.00")}
    errors = validate_csv_row(row, 1)
    assert errors == []


def test_validate_csv_row_zero_amount() -> None:
    from decimal import Decimal

    from app.bulk import validate_csv_row

    row = {"invoice_amount": Decimal("0.00"), "amount_paid": Decimal("0.00")}
    errors = validate_csv_row(row, 1)
    assert any("invoice_amount" in e for e in errors)


def test_validate_csv_row_overpaid() -> None:
    from decimal import Decimal

    from app.bulk import validate_csv_row

    row = {"invoice_amount": Decimal("100.00"), "amount_paid": Decimal("200.00")}
    errors = validate_csv_row(row, 1)
    assert any("exceed" in e for e in errors)


def test_merge_invoice_dicts_applies_update() -> None:
    from app.bulk import merge_invoice_dicts

    base = {"invoice_number": "INV-001", "payment_status": "UNPAID", "amount_paid": "0.00"}
    update = {"payment_status": "PAID", "amount_paid": "1000.00"}
    merged = merge_invoice_dicts(base, update)
    assert merged["payment_status"] == "PAID"
    assert merged["amount_paid"] == "1000.00"


def test_merge_invoice_dicts_skips_none() -> None:
    from app.bulk import merge_invoice_dicts

    base = {"invoice_number": "INV-001", "supplier": "Acme"}
    update = {"supplier": None, "currency": "EUR"}
    merged = merge_invoice_dicts(base, update)
    assert merged["supplier"] == "Acme"
    assert merged["currency"] == "EUR"


def test_to_invoice_create_payload_basic() -> None:
    from decimal import Decimal

    from app.bulk import to_invoice_create_payload

    row = {
        "invoice_number": "  INV-001  ",
        "business_unit": "Finance BU",
        "supplier": "  Acme Corp  ",
        "invoice_date": "2025-01-15",
        "invoice_amount": Decimal("1000.00"),
        "amount_paid": Decimal("0.00"),
        "currency": "usd",
        "payment_status": "unpaid",
    }
    payload = to_invoice_create_payload(row)
    assert payload["invoice_number"] == "INV-001"
    assert payload["supplier"] == "Acme Corp"
    assert payload["currency"] == "USD"
    assert payload["payment_status"] == "UNPAID"


def test_to_invoice_create_payload_defaults() -> None:
    from app.bulk import to_invoice_create_payload

    row = {"invoice_amount": 500}
    payload = to_invoice_create_payload(row)
    assert payload["currency"] == "USD"
    assert payload["payment_status"] == "UNPAID"
