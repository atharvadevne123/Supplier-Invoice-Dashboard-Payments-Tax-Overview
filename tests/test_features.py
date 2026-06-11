"""Tests for feature engineering and computed field calculations."""

import pytest
from decimal import Decimal

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
