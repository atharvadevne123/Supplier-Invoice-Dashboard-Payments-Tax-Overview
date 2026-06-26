"""Tests for shared utility helpers."""

from decimal import Decimal

import pytest

from app.utils import (
    build_filter_clause,
    format_currency,
    paginate,
    round_decimal,
    safe_divide,
    sanitize_string,
)


@pytest.mark.parametrize(
    "page,page_size,total,expected_pages",
    [
        (1, 10, 25, 3),
        (1, 10, 10, 1),
        (1, 10, 0, 1),
        (2, 5, 12, 3),
        (1, 100, 5, 1),
    ],
)
def test_paginate_page_count(
    page: int, page_size: int, total: int, expected_pages: int
) -> None:
    items = list(range(total))
    _, pages = paginate(items, page, page_size)
    assert pages == expected_pages


def test_paginate_returns_correct_slice() -> None:
    items = list(range(10))
    sliced, _ = paginate(items, 2, 3)
    assert sliced == [3, 4, 5]


def test_paginate_last_page_partial() -> None:
    items = list(range(7))
    sliced, _ = paginate(items, 3, 3)
    assert sliced == [6]


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("  hello  ", "hello"),
        ("", None),
        ("   ", None),
        (None, None),
        ("abc", "abc"),
    ],
)
def test_sanitize_string(input_str, expected) -> None:
    assert sanitize_string(input_str) == expected


def test_round_decimal() -> None:
    assert round_decimal(Decimal("1.2345"), 2) == Decimal("1.23")


def test_format_currency() -> None:
    assert format_currency(Decimal("1234.56"), "USD") == "USD 1,234.56"


def test_build_filter_clause_removes_none() -> None:
    result = build_filter_clause({"a": 1, "b": None, "c": "x"})
    assert result == {"a": 1, "c": "x"}


def test_safe_divide_normal() -> None:
    result = safe_divide(Decimal("10"), Decimal("4"))
    assert result == Decimal("2.5")


def test_safe_divide_by_zero() -> None:
    result = safe_divide(Decimal("10"), Decimal("0"))
    assert result == Decimal("0")


def test_default_page_size_constant() -> None:
    from app.utils import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

    assert DEFAULT_PAGE_SIZE == 20
    assert MAX_PAGE_SIZE == 200


def test_clamp_within_range() -> None:
    from app.utils import clamp

    assert clamp(5, 1, 10) == 5


def test_clamp_below_minimum() -> None:
    from app.utils import clamp

    assert clamp(-1, 0, 10) == 0


def test_clamp_above_maximum() -> None:
    from app.utils import clamp

    assert clamp(100, 0, 10) == 10


def test_clamp_at_boundary() -> None:
    from app.utils import clamp

    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10


def test_truncate_string_short() -> None:
    from app.utils import truncate_string

    assert truncate_string("hello", 20) == "hello"


def test_truncate_string_exact_length() -> None:
    from app.utils import truncate_string

    assert truncate_string("hello", 5) == "hello"


def test_truncate_string_truncated() -> None:
    from app.utils import truncate_string

    result = truncate_string("hello world", 8)
    assert result.endswith("...")
    assert len(result) == 8


def test_paginate_invalid_page_clamped_to_one() -> None:
    items = list(range(5))
    sliced, _ = paginate(items, -5, 10)
    assert sliced == items
