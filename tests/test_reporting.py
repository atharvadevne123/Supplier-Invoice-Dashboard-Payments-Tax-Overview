"""Tests for the report builder module."""

from datetime import date
from decimal import Decimal

from app.reporting import build_graph_view, build_table_view, build_view_selector_payload


INVOICES = [
    {
        "invoice_number": "INV-001",
        "business_unit": "Finance BU",
        "supplier": "Acme",
        "invoice_date": date(2025, 3, 1),
        "invoice_amount": Decimal("1000.00"),
        "amount_paid": Decimal("1080.00"),
        "currency": "USD",
        "payment_status": "PAID",
    },
    {
        "invoice_number": "INV-002",
        "business_unit": "IT BU",
        "supplier": "Beta",
        "invoice_date": date(2025, 3, 15),
        "invoice_amount": Decimal("500.00"),
        "amount_paid": Decimal("0.00"),
        "currency": "USD",
        "payment_status": "UNPAID",
    },
]


def test_table_view_row_count() -> None:
    rows = build_table_view(INVOICES)
    assert len(rows) == 2


def test_table_view_has_computed_fields() -> None:
    rows = build_table_view(INVOICES)
    for row in rows:
        assert "tax_amount" in row
        assert "outstanding_amount" in row
        assert "color_label" in row


def test_table_view_color_labels() -> None:
    rows = build_table_view(INVOICES)
    paid_row = next(r for r in rows if r["payment_status"] == "PAID")
    unpaid_row = next(r for r in rows if r["payment_status"] == "UNPAID")
    assert paid_row["color_label"] == "green"
    assert unpaid_row["color_label"] == "red"


def test_graph_view_series_labels() -> None:
    graph = build_graph_view(INVOICES)
    labels = [s["label"] for s in graph["series"]]
    assert "Invoice Amount" in labels
    assert "Tax" in labels
    assert "Amount Paid" in labels
    assert "Outstanding" in labels


def test_graph_view_total_count() -> None:
    graph = build_graph_view(INVOICES)
    assert graph["total_invoices"] == 2


def test_view_selector_contains_both_views() -> None:
    payload = build_view_selector_payload(INVOICES)
    assert "table_view" in payload
    assert "graph_view" in payload


def test_build_table_view_empty() -> None:
    assert build_table_view([]) == []


def test_build_graph_view_empty() -> None:
    graph = build_graph_view([])
    assert graph["total_invoices"] == 0
    assert all(s["value"] == Decimal("0") for s in graph["series"])
