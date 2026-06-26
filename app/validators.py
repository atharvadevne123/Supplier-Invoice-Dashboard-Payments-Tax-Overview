"""Domain-level input validators supplementing Pydantic field constraints."""

import logging
import re
from datetime import date
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)

_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3}$")
_INVOICE_NUM_PATTERN = re.compile(r"^[A-Za-z0-9\-_/]{1,50}$")
_BUSINESS_UNIT_PATTERN = re.compile(r"^[A-Za-z0-9 \-_]{1,100}$")

MAX_INVOICE_NUMBER_LENGTH: int = 50
MAX_BUSINESS_UNIT_LENGTH: int = 100


def validate_currency_code(currency: str) -> str:
    """Raise ValueError if currency is not a 3-letter ISO code.

    Args:
        currency: Raw currency string (case-insensitive).

    Returns:
        Uppercased 3-letter currency code.

    Raises:
        ValueError: If the code does not match ^[A-Z]{3}$.
    """
    if not _CURRENCY_PATTERN.match(currency.upper()):
        raise ValueError(f"Invalid currency code '{currency}': must be 3 uppercase letters")
    return currency.upper()


def validate_invoice_number(invoice_number: str) -> str:
    """Raise ValueError if invoice number contains disallowed characters.

    Args:
        invoice_number: Raw invoice number string.

    Returns:
        Validated invoice number unchanged.

    Raises:
        ValueError: If the number does not match allowed alphanumeric/symbol pattern.
    """
    if not _INVOICE_NUM_PATTERN.match(invoice_number):
        raise ValueError(
            f"Invoice number '{invoice_number}' contains invalid characters"
        )
    return invoice_number


def validate_date_range(date_from: Optional[date], date_to: Optional[date]) -> None:
    """Raise ValueError if date_from is after date_to.

    Args:
        date_from: Start of the date range (may be None).
        date_to: End of the date range (may be None).

    Raises:
        ValueError: If both are set and date_from > date_to.
    """
    if date_from and date_to and date_from > date_to:
        raise ValueError(
            f"date_from ({date_from}) must not be after date_to ({date_to})"
        )


def validate_amount_precision(amount: Decimal, field_name: str = "amount") -> Decimal:
    """Raise ValueError if amount has more than 2 decimal places.

    Args:
        amount: Decimal amount to check.
        field_name: Name used in error messages.

    Returns:
        Validated amount unchanged.

    Raises:
        ValueError: If amount has more than 2 decimal places.
    """
    if amount.as_tuple().exponent < -2:
        raise ValueError(f"{field_name} must have at most 2 decimal places")
    return amount


def validate_positive_amount(amount: Decimal, field_name: str = "amount") -> Decimal:
    """Raise ValueError if amount is not strictly positive.

    Args:
        amount: Decimal amount to check.
        field_name: Name used in error messages.

    Returns:
        Validated amount unchanged.

    Raises:
        ValueError: If amount is zero or negative.
    """
    if amount <= Decimal("0"):
        raise ValueError(f"{field_name} must be greater than zero")
    return amount


def validate_non_negative_amount(amount: Decimal, field_name: str = "amount") -> Decimal:
    """Raise ValueError if amount is negative.

    Args:
        amount: Decimal amount to check.
        field_name: Name used in error messages.

    Returns:
        Validated amount unchanged.

    Raises:
        ValueError: If amount is negative.
    """
    if amount < Decimal("0"):
        raise ValueError(f"{field_name} must not be negative")
    return amount


def validate_non_empty_string(value: str, field_name: str = "field") -> str:
    """Raise ValueError if the string is empty or whitespace-only.

    Args:
        value: String to validate.
        field_name: Name used in error messages.

    Returns:
        Stripped non-empty string.

    Raises:
        ValueError: If the stripped string is empty.
    """
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty or whitespace")
    return stripped


def validate_supplier_name(supplier: str, max_length: int = 200) -> str:
    """Raise ValueError if the supplier name is empty or too long.

    Args:
        supplier: Raw supplier name string.
        max_length: Maximum allowed character length (default 200).

    Returns:
        Stripped supplier name.

    Raises:
        ValueError: If the name is blank or exceeds max_length.
    """
    stripped = supplier.strip()
    if not stripped:
        raise ValueError("supplier name must not be empty")
    if len(stripped) > max_length:
        raise ValueError(f"supplier name exceeds maximum length of {max_length}")
    return stripped


def validate_business_unit(business_unit: str) -> str:
    """Raise ValueError if business unit contains disallowed characters.

    Args:
        business_unit: Raw business unit string.

    Returns:
        Validated business unit stripped of surrounding whitespace.

    Raises:
        ValueError: If the string does not match allowed pattern or exceeds max length.
    """
    stripped = business_unit.strip()
    if not stripped:
        raise ValueError("business_unit must not be empty")
    if len(stripped) > MAX_BUSINESS_UNIT_LENGTH:
        raise ValueError(
            f"business_unit exceeds maximum length of {MAX_BUSINESS_UNIT_LENGTH}"
        )
    if not _BUSINESS_UNIT_PATTERN.match(stripped):
        raise ValueError(
            f"business_unit '{stripped}' contains invalid characters"
        )
    return stripped
