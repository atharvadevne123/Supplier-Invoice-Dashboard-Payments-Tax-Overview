"""Tests for feature engineering and computed field calculations."""

from decimal import Decimal

import pytest

from app.features import (
    aggregate_invoices,
    apply_conditional_formatting,
    compute_outstanding,
    compute_tax,
    derive_payment_status,
)


@pytest.mark.parametrize(
    "amount,rate,expected",
    [
        (Decimal("1000.00"), 0.08, Decimal("80.00")),
        (Decimal("500.00"), 0.10, Decimal("50.00")),
        (Decimal("0.00"), 0.08, Decimal("0.00")),
        (Decimal("999.99"), 0.08, Decimal("80.00")),
        (Decimal("1.00"), 0.08, Decimal("0.08")),
    ],
)
def test_compute_tax(amount: Decimal, rate: float, expected: Decimal) -> None:
    assert compute_tax(amount, rate) == expected


def test_compute_tax_default_rate() -> None:
    tax = compute_tax(Decimal("1000.00"))
    assert tax > Decimal("0")


def test_compute_outstanding_unpaid() -> None:
    outstanding = compute_outstanding(Decimal("1000.00"), Decimal("0.00"), 0.08)
    assert outstanding == Decimal("1080.00")


def test_compute_outstanding_paid() -> None:
    outstanding = compute_outstanding(Decimal("1000.00"), Decimal("1080.00"), 0.08)
    assert outstanding == Decimal("0.00")


def test_compute_outstanding_partial() -> None:
    outstanding = compute_outstanding(Decimal("1000.00"), Decimal("500.00"), 0.08)
    assert outstanding == Decimal("580.00")


def test_compute_outstanding_never_negative() -> None:
    outstanding = compute_outstanding(Decimal("1000.00"), Decimal("9999.00"), 0.08)
    assert outstanding == Decimal("0.00")


@pytest.mark.parametrize(
    "paid,amount,expected_status",
    [
        (Decimal("0"), Decimal("1000"), "UNPAID"),
        (Decimal("1000"), Decimal("1000"), "PAID"),
        (Decimal("500"), Decimal("1000"), "PARTIAL"),
        (Decimal("1001"), Decimal("1000"), "PAID"),
    ],
)
def test_derive_payment_status(paid: Decimal, amount: Decimal, expected_status: str) -> None:
    assert derive_payment_status(amount, paid) == expected_status


@pytest.mark.parametrize(
    "outstanding,amount,color",
    [
        (Decimal("0"), Decimal("1000"), "green"),
        (Decimal("500"), Decimal("1000"), "amber"),
        (Decimal("1000"), Decimal("1000"), "red"),
        (Decimal("1500"), Decimal("1000"), "red"),
    ],
)
def test_apply_conditional_formatting(outstanding: Decimal, amount: Decimal, color: str) -> None:
    assert apply_conditional_formatting(outstanding, amount) == color


def test_aggregate_invoices_empty() -> None:
    result = aggregate_invoices([])
    assert result["total_invoices"] == 0
    assert result["total_outstanding"] == Decimal("0")


def test_aggregate_invoices_counts() -> None:
    invoices = [
        {"invoice_amount": Decimal("1000"), "amount_paid": Decimal("1000"), "payment_status": "PAID"},
        {"invoice_amount": Decimal("500"), "amount_paid": Decimal("0"), "payment_status": "UNPAID"},
        {"invoice_amount": Decimal("800"), "amount_paid": Decimal("400"), "payment_status": "PARTIAL"},
    ]
    result = aggregate_invoices(invoices)
    assert result["total_invoices"] == 3
    assert result["paid_count"] == 1
    assert result["unpaid_count"] == 1
    assert result["partial_count"] == 1


def test_aggregate_invoices_cancelled_count() -> None:
    from app.features import aggregate_invoices

    invoices = [
        {"invoice_amount": Decimal("200"), "amount_paid": Decimal("0"), "payment_status": "CANCELLED"},
        {"invoice_amount": Decimal("300"), "amount_paid": Decimal("0"), "payment_status": "UNPAID"},
    ]
    result = aggregate_invoices(invoices)
    assert result["cancelled_count"] == 1


def test_compute_payment_ratio_full() -> None:
    from app.features import compute_payment_ratio

    ratio = compute_payment_ratio(Decimal("1000"), Decimal("1000"))
    assert ratio == Decimal("1.0000")


def test_compute_payment_ratio_partial() -> None:
    from app.features import compute_payment_ratio

    ratio = compute_payment_ratio(Decimal("1000"), Decimal("250"))
    assert ratio == Decimal("0.2500")


def test_compute_payment_ratio_zero_invoice() -> None:
    from app.features import compute_payment_ratio

    ratio = compute_payment_ratio(Decimal("0"), Decimal("0"))
    assert ratio == Decimal("0")


def test_compute_payment_ratio_capped_at_one() -> None:
    from app.features import compute_payment_ratio

    ratio = compute_payment_ratio(Decimal("100"), Decimal("200"))
    assert ratio == Decimal("1.0000")


def test_invoice_age_days_today() -> None:
    from datetime import date

    from app.features import invoice_age_days

    assert invoice_age_days(date.today()) == 0


def test_invoice_age_days_past() -> None:
    from datetime import date, timedelta

    from app.features import invoice_age_days

    old = date.today() - timedelta(days=30)
    assert invoice_age_days(old) == 30


def test_invoice_age_days_with_reference() -> None:
    from datetime import date

    from app.features import invoice_age_days

    inv_date = date(2025, 1, 1)
    ref = date(2025, 3, 2)
    assert invoice_age_days(inv_date, as_of=ref) == 60


def test_classify_invoice_size_small() -> None:
    from app.features import classify_invoice_size

    assert classify_invoice_size(Decimal("500.00")) == "small"


def test_classify_invoice_size_medium() -> None:
    from app.features import classify_invoice_size

    assert classify_invoice_size(Decimal("5000.00")) == "medium"


def test_classify_invoice_size_large() -> None:
    from app.features import classify_invoice_size

    assert classify_invoice_size(Decimal("15000.00")) == "large"


def test_classify_invoice_size_at_threshold() -> None:
    from app.features import classify_invoice_size

    assert classify_invoice_size(Decimal("1000.00")) == "medium"
    assert classify_invoice_size(Decimal("10000.00")) == "large"
