"""Tests for the currency conversion module."""

from decimal import Decimal

import pytest

from app.currency import convert_amount, get_exchange_rate, normalize_to_usd


def test_same_currency_returns_original() -> None:
    result = convert_amount(Decimal("1000.00"), "USD", "USD")
    assert result == Decimal("1000.00")


def test_usd_to_eur_converts() -> None:
    result = convert_amount(Decimal("1000.00"), "USD", "EUR")
    assert result is not None
    assert result < Decimal("1000.00")


def test_unknown_currency_returns_none() -> None:
    result = convert_amount(Decimal("100.00"), "XYZ", "USD")
    assert result is None


def test_get_exchange_rate_usd_to_usd() -> None:
    rate = get_exchange_rate("USD", "USD")
    assert rate == Decimal("1.000000")


def test_get_exchange_rate_unknown() -> None:
    rate = get_exchange_rate("ABC", "USD")
    assert rate is None


@pytest.mark.parametrize("currency", ["USD", "EUR", "GBP", "CAD"])
def test_normalize_known_currencies(currency: str) -> None:
    invoices = [{"invoice_amount": Decimal("1000.00"), "currency": currency}]
    result = normalize_to_usd(invoices)
    assert "invoice_amount_usd" in result[0]
    assert result[0]["invoice_amount_usd"] is not None


def test_normalize_unknown_currency_passthrough() -> None:
    invoices = [{"invoice_amount": Decimal("500.00"), "currency": "XYZ"}]
    result = normalize_to_usd(invoices)
    assert result[0]["invoice_amount_usd"] == Decimal("500.00")
