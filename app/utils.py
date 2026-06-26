"""Shared utility helpers used across the application."""

import logging
import math
from decimal import Decimal
from typing import Any, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 200
MAX_TRUNCATE_LENGTH: int = 255


def paginate(
    items: list[T],
    page: int,
    page_size: int,
) -> tuple[list[T], int]:
    """Return a page slice and the total number of pages.

    Args:
        items: Full list to paginate.
        page: 1-based page number.
        page_size: Number of items per page.

    Returns:
        Tuple of (page_items, total_pages).
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE
    total = len(items)
    total_pages = max(1, math.ceil(total / page_size))
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total_pages


def sanitize_string(value: Optional[str]) -> Optional[str]:
    """Strip leading/trailing whitespace and return None for blank strings.

    Args:
        value: String to sanitize, or None.

    Returns:
        Stripped string, or None if blank or None.
    """
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """Round a Decimal to the given number of decimal places.

    Args:
        value: Decimal value to round.
        places: Number of decimal places (default 2).

    Returns:
        Rounded Decimal.
    """
    quantizer = Decimal(10) ** -places
    return value.quantize(quantizer)


def format_currency(amount: Decimal, currency: str = "USD") -> str:
    """Return a human-readable currency string.

    Args:
        amount: Decimal amount to format.
        currency: ISO 4217 currency code (default "USD").

    Returns:
        Formatted string, e.g. "USD 1,234.56".
    """
    return f"{currency} {amount:,.2f}"


def build_filter_clause(filters: dict[str, Any]) -> dict[str, Any]:
    """Remove None-valued entries from a filter dict for cleaner query building.

    Args:
        filters: Dict of field -> value pairs, possibly containing None values.

    Returns:
        Copy of filters with all None values removed.
    """
    return {k: v for k, v in filters.items() if v is not None}


def safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Return numerator / denominator, or Decimal('0') when denominator is zero.

    Args:
        numerator: Dividend.
        denominator: Divisor.

    Returns:
        Quotient, or Decimal("0") if denominator is zero.
    """
    if denominator == Decimal("0"):
        logger.debug("safe_divide: denominator is zero, returning 0")
        return Decimal("0")
    return numerator / denominator


def clamp(value: int, minimum: int, maximum: int) -> int:
    """Return value clamped to the inclusive [minimum, maximum] range.

    Args:
        value: Integer to clamp.
        minimum: Lower bound (inclusive).
        maximum: Upper bound (inclusive).

    Returns:
        Value clamped to [minimum, maximum].
    """
    return max(minimum, min(value, maximum))


def chunk_list(items: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split a list into fixed-size chunks (last chunk may be smaller).

    Args:
        items: List to split.
        chunk_size: Maximum number of items per chunk.

    Returns:
        List of sub-lists, each of at most chunk_size elements.
    """
    if chunk_size < 1:
        chunk_size = 1
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def truncate_string(value: str, max_length: int = MAX_TRUNCATE_LENGTH) -> str:
    """Truncate a string to max_length characters, appending '...' when cut.

    Args:
        value: String to truncate.
        max_length: Maximum allowed length (must be >= 3).

    Returns:
        Original string if within limit; otherwise truncated with '...' suffix.
    """
    if len(value) <= max_length:
        return value
    return value[: max(0, max_length - 3)] + "..."
