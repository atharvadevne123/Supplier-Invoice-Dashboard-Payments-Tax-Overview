"""Shared utility helpers used across the application."""

import logging
import math
from decimal import Decimal
from typing import Any, Optional, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


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
        page_size = 10
    total = len(items)
    total_pages = max(1, math.ceil(total / page_size))
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end], total_pages


def sanitize_string(value: Optional[str]) -> Optional[str]:
    """Strip leading/trailing whitespace and return None for blank strings."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """Round a Decimal to the given number of decimal places."""
    quantizer = Decimal(10) ** -places
    return value.quantize(quantizer)


def format_currency(amount: Decimal, currency: str = "USD") -> str:
    """Return a human-readable currency string."""
    return f"{currency} {amount:,.2f}"


def build_filter_clause(filters: dict[str, Any]) -> dict[str, Any]:
    """Remove None-valued entries from a filter dict for cleaner query building."""
    return {k: v for k, v in filters.items() if v is not None}


def safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    """Return numerator / denominator, or Decimal('0') when denominator is zero."""
    if denominator == Decimal("0"):
        logger.debug("safe_divide: denominator is zero, returning 0")
        return Decimal("0")
    return numerator / denominator
