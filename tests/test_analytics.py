"""Tests for the analytics module."""

from datetime import date, timedelta
from decimal import Decimal

from app.analytics import (
    currency_breakdown,
    monthly_invoice_trend,
    overdue_invoices,
    payment_status_distribution,
    supplier_outstanding_ranking,
)

SAMPLE_INVOICES = [
    {
        "invoice_number": "INV-001",
        "supplier": "Acme",
        "invoice_date": date(2025, 1, 10),
        "invoice_amount": Decimal("1000.00"),
        "amount_paid": Decimal("0.00"),
        "currency": "USD",
        "payment_status": "UNPAID",
    },
    {
        "invoice_number": "INV-002",
        "supplier": "Beta",
        "invoice_date": date(2025, 2, 5),
        "invoice_amount": Decimal("2000.00"),
        "amount_paid": Decimal("2000.00"),
        "currency": "EUR",
        "payment_status": "PAID",
    },
    {
        "invoice_number": "INV-003",
        "supplier": "Acme",
        "invoice_date": date(2025, 1, 20),
        "invoice_amount": Decimal("500.00"),
        "amount_paid": Decimal("250.00"),
        "currency": "USD",
        "payment_status": "PARTIAL",
    },
]


def test_supplier_ranking_order() -> None:
    ranking = supplier_outstanding_ranking(SAMPLE_INVOICES)
    assert ranking[0]["supplier"] == "Acme"
    assert ranking[0]["total_outstanding"] > ranking[1]["total_outstanding"]


def test_supplier_ranking_empty() -> None:
    assert supplier_outstanding_ranking([]) == []


def test_monthly_trend_groups_by_month() -> None:
    trend = monthly_invoice_trend(SAMPLE_INVOICES)
    months = [t["month"] for t in trend]
    assert "2025-01" in months
    assert "2025-02" in months


def test_monthly_trend_sorted() -> None:
    trend = monthly_invoice_trend(SAMPLE_INVOICES)
    assert trend[0]["month"] < trend[-1]["month"]


def test_payment_status_distribution() -> None:
    dist = payment_status_distribution(SAMPLE_INVOICES)
    assert dist["UNPAID"] == 1
    assert dist["PAID"] == 1
    assert dist["PARTIAL"] == 1


def test_currency_breakdown_order() -> None:
    breakdown = currency_breakdown(SAMPLE_INVOICES)
    assert breakdown[0]["currency"] == "EUR"


def test_overdue_invoices_detected() -> None:
    old_invoices = [
        {
            "invoice_number": "OLD-001",
            "supplier": "X",
            "invoice_date": date.today() - timedelta(days=60),
            "invoice_amount": Decimal("500.00"),
            "amount_paid": Decimal("0.00"),
            "payment_status": "UNPAID",
        }
    ]
    overdue = overdue_invoices(old_invoices)
    assert len(overdue) == 1
    assert overdue[0]["age_days"] >= 60


def test_overdue_invoices_excludes_recent() -> None:
    recent = [
        {
            "invoice_number": "NEW-001",
            "supplier": "X",
            "invoice_date": date.today() - timedelta(days=5),
            "invoice_amount": Decimal("500.00"),
            "amount_paid": Decimal("0.00"),
            "payment_status": "UNPAID",
        }
    ]
    assert overdue_invoices(recent) == []


def test_overdue_excludes_paid() -> None:
    paid = [
        {
            "invoice_number": "PAID-001",
            "supplier": "X",
            "invoice_date": date.today() - timedelta(days=90),
            "invoice_amount": Decimal("500.00"),
            "amount_paid": Decimal("500.00"),
            "payment_status": "PAID",
        }
    ]
    assert overdue_invoices(paid) == []


def test_monthly_trend_empty_invoices() -> None:
    assert monthly_invoice_trend([]) == []


def test_payment_status_distribution_empty() -> None:
    assert payment_status_distribution([]) == {}


def test_currency_breakdown_empty() -> None:
    assert currency_breakdown([]) == []


def test_overdue_invoices_partial_included() -> None:
    from datetime import timedelta
    from decimal import Decimal

    partial = [
        {
            "invoice_number": "PART-001",
            "supplier": "X",
            "invoice_date": date.today() - timedelta(days=45),
            "invoice_amount": Decimal("1000.00"),
            "amount_paid": Decimal("500.00"),
            "payment_status": "PARTIAL",
        }
    ]
    result = overdue_invoices(partial)
    assert len(result) == 1
    assert result[0]["payment_status"] == "PARTIAL"


def test_supplier_ranking_aggregates_across_invoices() -> None:
    invoices = [
        {
            "supplier": "Acme",
            "invoice_amount": Decimal("1000"),
            "amount_paid": Decimal("0"),
        },
        {
            "supplier": "Acme",
            "invoice_amount": Decimal("2000"),
            "amount_paid": Decimal("0"),
        },
    ]
    ranking = supplier_outstanding_ranking(invoices)
    assert len(ranking) == 1
    assert ranking[0]["supplier"] == "Acme"
