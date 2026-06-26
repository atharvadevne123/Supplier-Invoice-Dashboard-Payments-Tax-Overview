"""Currency conversion utilities for multi-currency invoice analytics."""

import logging
from decimal import Decimal
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

_STATIC_RATES: dict[str, Decimal] = {
    "USD": Decimal("1.0000"),
    "EUR": Decimal("0.9200"),
    "GBP": Decimal("0.7800"),
    "CAD": Decimal("1.3600"),
    "AUD": Decimal("1.5200"),
    "JPY": Decimal("149.50"),
    "CHF": Decimal("0.8900"),
    "INR": Decimal("83.20"),
    "CNY": Decimal("7.2400"),
    "SGD": Decimal("1.3500"),
    "MXN": Decimal("17.15"),
}


def list_supported_currencies() -> list[str]:
    """Return a sorted list of currency codes with known exchange rates.

    Returns:
        Sorted list of 3-letter ISO currency codes.
    """
    return sorted(_STATIC_RATES.keys())


@lru_cache(maxsize=512)
def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> Optional[Decimal]:
    """Return the exchange rate from from_currency to to_currency.

    Uses a static rate table. Returns None if either currency is unknown.

    Args:
        from_currency: Source ISO currency code.
        to_currency: Target ISO currency code (default "USD").

    Returns:
        Exchange rate as Decimal rounded to 6 places, or None if unknown currency.
    """
    from_rate = _STATIC_RATES.get(from_currency.upper())
    to_rate = _STATIC_RATES.get(to_currency.upper())
    if from_rate is None or to_rate is None:
        logger.warning("Unknown currency in rate lookup: %s -> %s", from_currency, to_currency)
        return None
    return (to_rate / from_rate).quantize(Decimal("0.000001"))


def convert_amount(
    amount: Decimal,
    from_currency: str,
    to_currency: str = "USD",
) -> Optional[Decimal]:
    """Convert amount from from_currency to to_currency.

    Args:
        amount: Decimal amount to convert.
        from_currency: Source ISO currency code.
        to_currency: Target ISO currency code (default "USD").

    Returns:
        Converted amount rounded to 2 decimal places, or None if rate unavailable.
    """
    if from_currency.upper() == to_currency.upper():
        return amount
    rate = get_exchange_rate(from_currency, to_currency)
    if rate is None:
        return None
    return (amount * rate).quantize(Decimal("0.01"))


def normalize_to_usd(invoices: list[dict]) -> list[dict]:
    """Return a copy of each invoice dict with invoice_amount converted to USD.

    Invoices with unknown currencies are passed through unchanged with the
    original invoice_amount used as the fallback USD amount.

    Args:
        invoices: List of invoice dicts with invoice_amount and currency fields.

    Returns:
        List of dicts with an added invoice_amount_usd field.
    """
    normalized = []
    for inv in invoices:
        currency = inv.get("currency", "USD")
        usd_amount = convert_amount(inv["invoice_amount"], currency, "USD")
        if usd_amount is not None:
            normalized.append({**inv, "invoice_amount_usd": usd_amount})
        else:
            logger.warning("Cannot normalize %s to USD — unknown currency", currency)
            normalized.append({**inv, "invoice_amount_usd": inv["invoice_amount"]})
    return normalized


def normalize_amount_list(
    amounts: list[tuple[Decimal, str]],
    to_currency: str = "USD",
) -> list[Optional[Decimal]]:
    """Batch-convert a list of (amount, currency) pairs to a target currency.

    Args:
        amounts: List of (amount, from_currency) tuples.
        to_currency: Target ISO currency code (default "USD").

    Returns:
        List of converted Decimal amounts (None where conversion unavailable).
    """
    return [convert_amount(amount, currency, to_currency) for amount, currency in amounts]
