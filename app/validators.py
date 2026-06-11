"""Domain-level input validators supplementing Pydantic field constraints."""

import logging
import re
from datetime import date
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)

_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
_INVOICE_NUM_PATTERN = re.compile(r"^[A-Za-z0-9\-_/]{1,50}$")


def validate_currency_code(currency: str) -> str:
    """Raise ValueError if currency is not a 3-letter ISO code."""
    if not _CURRENCY_PATTERN.match(currency.upper()):
        raise ValueError(f"Invalid currency code '{currency}': must be 3 uppercase letters")
    return currency.upper()


def validate_invoice_number(invoice_number: str) -> str:
    """Raise ValueError if invoice number contains disallowed characters."""
    if not _INVOICE_NUM_PATTERN.match(invoice_number):
        raise ValueError(
            f"Invoice number '{invoice_number}' contains invalid characters"
        )
    return invoice_number


def validate_date_range(date_from: Optional[date], date_to: Optional[date]) -> None:
    """Raise ValueError if date_from is after date_to."""
    if date_from and date_to and date_from > date_to:
        raise ValueError(
            f"date_from ({date_from}) must not be after date_to ({date_to})"
        )


def validate_amount_precision(amount: Decimal, field_name: str = "amount") -> Decimal:
    """Raise ValueError if amount has more than 2 decimal places."""
    if amount.as_tuple().exponent < -2:
        raise ValueError(f"{field_name} must have at most 2 decimal places")
    return amount


def validate_positive_amount(amount: Decimal, field_name: str = "amount") -> Decimal:
    """Raise ValueError if amount is not strictly positive."""
    if amount <= Decimal("0"):
        raise ValueError(f"{field_name} must be greater than zero")
    return amount
