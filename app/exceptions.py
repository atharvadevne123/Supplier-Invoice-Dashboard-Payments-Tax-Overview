"""Custom exception classes and FastAPI exception handlers."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class InvoiceNotFoundError(Exception):
    """Raised when an invoice cannot be located by its number."""

    def __init__(self, invoice_number: str) -> None:
        self.invoice_number = invoice_number
        super().__init__(f"Invoice {invoice_number} not found")

    def __repr__(self) -> str:
        return f"InvoiceNotFoundError(invoice_number={self.invoice_number!r})"


class DuplicateInvoiceError(Exception):
    """Raised when attempting to create an invoice that already exists."""

    def __init__(self, invoice_number: str) -> None:
        self.invoice_number = invoice_number
        super().__init__(f"Invoice {invoice_number} already exists")

    def __repr__(self) -> str:
        return f"DuplicateInvoiceError(invoice_number={self.invoice_number!r})"


class ValidationError(Exception):
    """Raised for domain-level validation failures not caught by Pydantic."""

    def __init__(self, message: str, field: str = "") -> None:
        self.field = field
        super().__init__(message)

    def __repr__(self) -> str:
        return f"ValidationError(message={str(self)!r}, field={self.field!r})"


async def invoice_not_found_handler(request: Request, exc: InvoiceNotFoundError) -> JSONResponse:
    """Return a 404 JSON response for missing invoices.

    Args:
        request: Incoming HTTP request.
        exc: The raised InvoiceNotFoundError.

    Returns:
        JSONResponse with status 404 and error detail.
    """
    logger.warning("Invoice not found: %s path=%s", exc.invoice_number, request.url.path)
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def duplicate_invoice_handler(
    request: Request, exc: DuplicateInvoiceError
) -> JSONResponse:
    """Return a 409 JSON response for duplicate invoices.

    Args:
        request: Incoming HTTP request.
        exc: The raised DuplicateInvoiceError.

    Returns:
        JSONResponse with status 409 and error detail.
    """
    logger.warning("Duplicate invoice: %s path=%s", exc.invoice_number, request.url.path)
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Return a 422 JSON response for domain validation errors.

    Args:
        request: Incoming HTTP request.
        exc: The raised ValidationError.

    Returns:
        JSONResponse with status 422 and error detail.
    """
    logger.warning("Validation error: %s path=%s", exc, request.url.path)
    return JSONResponse(status_code=422, content={"detail": str(exc)})
