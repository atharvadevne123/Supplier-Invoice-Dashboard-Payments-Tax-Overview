"""Feature engineering and computed field calculations for invoice analytics."""

import logging
from decimal import Decimal
from functools import lru_cache
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=256)
def compute_tax(invoice_amount: Decimal, tax_rate: Optional[float] = None) -> Decimal:
    """Return the tax amount for a given invoice amount.

    Uses the configured global tax rate unless overridden.
    """
    rate = Decimal(str(tax_rate)) if tax_rate is not None else Decimal(str(settings.tax_rate))
    return (invoice_amount * rate).quantize(Decimal("0.01"))


def compute_outstanding(
    invoice_amount: Decimal,
    amount_paid: Decimal,
    tax_rate: Optional[float] = None,
) -> Decimal:
    """Calculate outstanding balance after tax and payments.

    outstanding = invoice_amount + tax - amount_paid
    """
    tax = compute_tax(invoice_amount, tax_rate)
    outstanding = invoice_amount + tax - amount_paid
    return max(outstanding, Decimal("0.00")).quantize(Decimal("0.01"))


def derive_payment_status(
    invoice_amount: Decimal,
    amount_paid: Decimal,
) -> str:
    """Infer payment status from amounts when the stored status is unreliable."""
    if amount_paid <= Decimal("0"):
        return "UNPAID"
    if amount_paid >= invoice_amount:
        return "PAID"
    return "PARTIAL"


def apply_conditional_formatting(outstanding: Decimal, invoice_amount: Decimal) -> str:
    """Return a colour label matching the dashboard's conditional formatting rules.

    - green  → fully paid (outstanding == 0)
    - amber  → partially paid (0 < outstanding < invoice_amount)
    - red    → fully unpaid or large outstanding
    """
    if outstanding <= Decimal("0"):
        return "green"
    if outstanding < invoice_amount:
        return "amber"
    return "red"


def aggregate_invoices(invoices: list[dict]) -> dict:
    """Compute summary statistics across a list of invoice dicts."""
    total_invoices = len(invoices)
    total_invoice_amount = sum((inv["invoice_amount"] for inv in invoices), Decimal("0"))
    total_paid = sum((inv["amount_paid"] for inv in invoices), Decimal("0"))
    total_tax = sum((compute_tax(inv["invoice_amount"]) for inv in invoices), Decimal("0"))
    total_outstanding = sum(
        (compute_outstanding(inv["invoice_amount"], inv["amount_paid"]) for inv in invoices),
        Decimal("0"),
    )
    paid_count = sum(1 for inv in invoices if inv.get("payment_status") == "PAID")
    unpaid_count = sum(1 for inv in invoices if inv.get("payment_status") == "UNPAID")
    partial_count = sum(1 for inv in invoices if inv.get("payment_status") == "PARTIAL")

    logger.debug("Aggregated %d invoices; total_outstanding=%s", total_invoices, total_outstanding)
    return {
        "total_invoices": total_invoices,
        "total_invoice_amount": total_invoice_amount,
        "total_paid": total_paid,
        "total_tax": total_tax,
        "total_outstanding": total_outstanding,
        "paid_count": paid_count,
        "unpaid_count": unpaid_count,
        "partial_count": partial_count,
    }
