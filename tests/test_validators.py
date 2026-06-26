"""Tests for domain input validators."""

from datetime import date
from decimal import Decimal

import pytest

from app.validators import (
    validate_amount_precision,
    validate_currency_code,
    validate_date_range,
    validate_invoice_number,
    validate_positive_amount,
)


@pytest.mark.parametrize("code", ["USD", "EUR", "GBP", "JPY"])
def test_validate_currency_code_valid(code: str) -> None:
    assert validate_currency_code(code) == code


@pytest.mark.parametrize("code", ["US", "USDD", "123"])
def test_validate_currency_code_invalid(code: str) -> None:
    with pytest.raises(ValueError):
        validate_currency_code(code)


def test_validate_currency_code_normalizes_lowercase() -> None:
    assert validate_currency_code("usd") == "USD"


@pytest.mark.parametrize("num", ["INV-001", "ABC123", "2025/001"])
def test_validate_invoice_number_valid(num: str) -> None:
    assert validate_invoice_number(num) == num


@pytest.mark.parametrize("num", ["INV 001", "INV@001", ""])
def test_validate_invoice_number_invalid(num: str) -> None:
    with pytest.raises(ValueError):
        validate_invoice_number(num)


def test_validate_date_range_valid() -> None:
    validate_date_range(date(2025, 1, 1), date(2025, 12, 31))


def test_validate_date_range_invalid() -> None:
    with pytest.raises(ValueError):
        validate_date_range(date(2025, 12, 31), date(2025, 1, 1))


def test_validate_date_range_none_ok() -> None:
    validate_date_range(None, None)


def test_validate_amount_precision_ok() -> None:
    assert validate_amount_precision(Decimal("100.00")) == Decimal("100.00")


def test_validate_amount_precision_fails() -> None:
    with pytest.raises(ValueError):
        validate_amount_precision(Decimal("100.001"))


def test_validate_positive_amount_ok() -> None:
    assert validate_positive_amount(Decimal("0.01")) == Decimal("0.01")


def test_validate_positive_amount_fails() -> None:
    with pytest.raises(ValueError):
        validate_positive_amount(Decimal("0.00"))


def test_validate_non_negative_amount_zero_ok() -> None:
    from app.validators import validate_non_negative_amount

    assert validate_non_negative_amount(Decimal("0.00")) == Decimal("0.00")


def test_validate_non_negative_amount_positive_ok() -> None:
    from app.validators import validate_non_negative_amount

    assert validate_non_negative_amount(Decimal("0.01")) == Decimal("0.01")


def test_validate_non_negative_amount_fails_negative() -> None:
    from app.validators import validate_non_negative_amount

    with pytest.raises(ValueError):
        validate_non_negative_amount(Decimal("-0.01"))


def test_validate_non_empty_string_ok() -> None:
    from app.validators import validate_non_empty_string

    assert validate_non_empty_string("  hello  ") == "hello"


def test_validate_non_empty_string_fails_blank() -> None:
    from app.validators import validate_non_empty_string

    with pytest.raises(ValueError):
        validate_non_empty_string("   ")


def test_validate_non_empty_string_fails_empty() -> None:
    from app.validators import validate_non_empty_string

    with pytest.raises(ValueError):
        validate_non_empty_string("")


def test_validate_business_unit_valid() -> None:
    from app.validators import validate_business_unit

    assert validate_business_unit("Finance BU") == "Finance BU"


def test_validate_business_unit_strips_whitespace() -> None:
    from app.validators import validate_business_unit

    assert validate_business_unit("  IT Dept  ") == "IT Dept"


def test_validate_business_unit_fails_empty() -> None:
    from app.validators import validate_business_unit

    with pytest.raises(ValueError):
        validate_business_unit("   ")


def test_validate_business_unit_fails_special_chars() -> None:
    from app.validators import validate_business_unit

    with pytest.raises(ValueError):
        validate_business_unit("Finance@BU!")


def test_validate_supplier_name_valid() -> None:
    from app.validators import validate_supplier_name

    assert validate_supplier_name("Acme Corp") == "Acme Corp"


def test_validate_supplier_name_strips_whitespace() -> None:
    from app.validators import validate_supplier_name

    assert validate_supplier_name("  Beta Ltd  ") == "Beta Ltd"


def test_validate_supplier_name_fails_empty() -> None:
    from app.validators import validate_supplier_name

    with pytest.raises(ValueError):
        validate_supplier_name("   ")


def test_validate_supplier_name_fails_too_long() -> None:
    from app.validators import validate_supplier_name

    with pytest.raises(ValueError):
        validate_supplier_name("A" * 201)
