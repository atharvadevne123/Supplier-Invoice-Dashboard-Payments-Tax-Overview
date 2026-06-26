"""Tests for custom exception classes and FastAPI exception handlers."""

import pytest


def test_invoice_not_found_message() -> None:
    from app.exceptions import InvoiceNotFoundError

    exc = InvoiceNotFoundError("INV-001")
    assert "INV-001" in str(exc)
    assert exc.invoice_number == "INV-001"


def test_invoice_not_found_repr() -> None:
    from app.exceptions import InvoiceNotFoundError

    exc = InvoiceNotFoundError("INV-001")
    assert "InvoiceNotFoundError" in repr(exc)
    assert "INV-001" in repr(exc)


def test_duplicate_invoice_message() -> None:
    from app.exceptions import DuplicateInvoiceError

    exc = DuplicateInvoiceError("INV-002")
    assert "INV-002" in str(exc)
    assert exc.invoice_number == "INV-002"


def test_duplicate_invoice_repr() -> None:
    from app.exceptions import DuplicateInvoiceError

    exc = DuplicateInvoiceError("INV-002")
    assert "DuplicateInvoiceError" in repr(exc)


def test_validation_error_message() -> None:
    from app.exceptions import ValidationError

    exc = ValidationError("bad input", field="amount")
    assert "bad input" in str(exc)
    assert exc.field == "amount"


def test_validation_error_repr() -> None:
    from app.exceptions import ValidationError

    exc = ValidationError("bad input", field="currency")
    assert "ValidationError" in repr(exc)
    assert "currency" in repr(exc)


def test_validation_error_default_field() -> None:
    from app.exceptions import ValidationError

    exc = ValidationError("something wrong")
    assert exc.field == ""


@pytest.mark.anyio
async def test_invoice_not_found_handler_returns_404() -> None:
    from unittest.mock import MagicMock

    from app.exceptions import InvoiceNotFoundError, invoice_not_found_handler

    request = MagicMock()
    request.url.path = "/api/v1/invoices/INV-999"
    exc = InvoiceNotFoundError("INV-999")
    response = await invoice_not_found_handler(request, exc)
    assert response.status_code == 404


@pytest.mark.anyio
async def test_duplicate_invoice_handler_returns_409() -> None:
    from unittest.mock import MagicMock

    from app.exceptions import DuplicateInvoiceError, duplicate_invoice_handler

    request = MagicMock()
    request.url.path = "/api/v1/invoices"
    exc = DuplicateInvoiceError("INV-001")
    response = await duplicate_invoice_handler(request, exc)
    assert response.status_code == 409


@pytest.mark.anyio
async def test_validation_error_handler_returns_422() -> None:
    from unittest.mock import MagicMock

    from app.exceptions import ValidationError, validation_error_handler

    request = MagicMock()
    request.url.path = "/api/v1/invoices"
    exc = ValidationError("invalid amount")
    response = await validation_error_handler(request, exc)
    assert response.status_code == 422
