"""Pydantic request/response schemas for the Supplier Invoice API."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PaymentStatus(str, Enum):
    """Allowed payment status values matching Oracle Payables nomenclature."""

    PAID = "PAID"
    UNPAID = "UNPAID"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"


class InvoiceCreate(BaseModel):
    """Schema for creating a new supplier invoice."""

    invoice_number: str = Field(..., min_length=1, max_length=50, description="Unique invoice ID")
    business_unit: str = Field(..., min_length=1, max_length=100)
    supplier: str = Field(..., min_length=1, max_length=200)
    invoice_date: date
    invoice_amount: Decimal = Field(..., gt=Decimal("0"), decimal_places=2)
    amount_paid: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"), decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=10)
    payment_status: PaymentStatus = PaymentStatus.UNPAID

    @field_validator("amount_paid")
    @classmethod
    def paid_must_not_exceed_invoice(cls, v: Decimal, info: object) -> Decimal:
        """Ensure paid amount does not exceed invoice amount."""
        amount = getattr(info, "data", {}).get("invoice_amount")
        if amount is not None and v > amount:
            raise ValueError("amount_paid cannot exceed invoice_amount")
        return v


class InvoiceResponse(BaseModel):
    """Schema for a full invoice record including computed fields."""

    invoice_number: str
    business_unit: str
    supplier: str
    invoice_date: date
    invoice_amount: Decimal
    amount_paid: Decimal
    currency: str
    payment_status: str
    tax_amount: Decimal
    outstanding_amount: Decimal

    model_config = {"from_attributes": True}


class InvoiceSummary(BaseModel):
    """Aggregated invoice analytics for a supplier or business unit."""

    total_invoices: int
    total_invoice_amount: Decimal
    total_paid: Decimal
    total_tax: Decimal
    total_outstanding: Decimal
    paid_count: int
    unpaid_count: int
    partial_count: int


class HealthResponse(BaseModel):
    """API health check response."""

    status: str
    version: str
    database: str


class PaginatedInvoices(BaseModel):
    """Paginated list of invoice records."""

    items: list[InvoiceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class FilterParams(BaseModel):
    """Query filter parameters for invoice listing."""

    supplier: Optional[str] = None
    business_unit: Optional[str] = None
    payment_status: Optional[PaymentStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    currency: Optional[str] = None
