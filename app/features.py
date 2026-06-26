"""Feature engineering and computed field calculations for invoice analytics."""

import logging
from decimal import Decimal
from functools import lru_cache
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

DECIMAL_ZERO: Decimal = Decimal("0")
DECIMAL_CENT: Decimal = Decimal("0.01")
DECIMAL_EPSILON: Decimal = Decimal("0.00")


@lru_cache(maxsize=256)
def compute_tax(invoice_amount: Decimal, tax_rate: Optional[float] = None) -> Decimal:
    """Return the tax amount for a given invoice amount.

    Uses the configured global tax rate unless overridden.

    Args:
        invoice_amount: Gross invoice amount.
        tax_rate: Override tax rate (0.0–1.0). Uses settings.tax_rate if None.

    Returns:
        Tax amount rounded to 2 decimal places.
    """
    rate = Decimal(str(tax_rate)) if tax_rate is not None else Decimal(str(settings.tax_rate))
    return (invoice_amount * rate).quantize(DECIMAL_CENT)


def compute_outstanding(
    invoice_amount: Decimal,
    amount_paid: Decimal,
    tax_rate: Optional[float] = None,
) -> Decimal:
    """Calculate outstanding balance after tax and payments.

    outstanding = invoice_amount + tax - amount_paid

    Args:
        invoice_amount: Gross invoice amount.
        amount_paid: Amount already paid.
        tax_rate: Override tax rate (0.0–1.0).

    Returns:
        Outstanding balance (minimum 0), rounded to 2 decimal places.
    """
    tax = compute_tax(invoice_amount, tax_rate)
    outstanding = invoice_amount + tax - amount_paid
    return max(outstanding, DECIMAL_ZERO).quantize(DECIMAL_CENT)


def derive_payment_status(
    invoice_amount: Decimal,
    amount_paid: Decimal,
) -> str:
    """Infer payment status from amounts when the stored status is unreliable.

    Args:
        invoice_amount: Gross invoice amount.
        amount_paid: Amount already paid.

    Returns:
        One of "UNPAID", "PARTIAL", or "PAID".
    """
    if amount_paid <= DECIMAL_ZERO:
        return "UNPAID"
    if amount_paid >= invoice_amount:
        return "PAID"
    return "PARTIAL"


def apply_conditional_formatting(outstanding: Decimal, invoice_amount: Decimal) -> str:
    """Return a colour label matching the dashboard's conditional formatting rules.

    - green  → fully paid (outstanding == 0)
    - amber  → partially paid (0 < outstanding < invoice_amount)
    - red    → fully unpaid or large outstanding

    Args:
        outstanding: Current outstanding balance.
        invoice_amount: Original invoice amount.

    Returns:
        Colour label string: "green", "amber", or "red".
    """
    if outstanding <= DECIMAL_ZERO:
        return "green"
    if outstanding < invoice_amount:
        return "amber"
    return "red"


def compute_payment_ratio(invoice_amount: Decimal, amount_paid: Decimal) -> Decimal:
    """Return the fraction of the invoice that has been paid (0.0 – 1.0).

    Args:
        invoice_amount: Gross invoice amount.
        amount_paid: Amount already paid.

    Returns:
        Payment ratio rounded to 4 decimal places; 0 when invoice_amount is zero.
    """
    if invoice_amount <= DECIMAL_ZERO:
        return DECIMAL_ZERO
    ratio = (amount_paid / invoice_amount).quantize(Decimal("0.0001"))
    return min(ratio, Decimal("1.0000"))


def invoice_age_days(invoice_date: object, as_of: object = None) -> int:
    """Return the number of days since the invoice date.

    Args:
        invoice_date: datetime.date of the invoice.
        as_of: Reference date (defaults to today).

    Returns:
        Age in days (non-negative integer).
    """
    from datetime import date

    ref: date = as_of or date.today()
    delta = ref - invoice_date  # type: ignore[operator]
    return max(0, delta.days)


def aggregate_invoices(invoices: list[dict]) -> dict[str, object]:
    """Compute summary statistics across a list of invoice dicts.

    Args:
        invoices: List of invoice dicts with invoice_amount, amount_paid,
                  and payment_status fields.

    Returns:
        Dict with total_invoices, total_invoice_amount, total_paid, total_tax,
        total_outstanding, paid_count, unpaid_count, partial_count.
    """
    total_invoices = len(invoices)
    total_invoice_amount = sum((inv["invoice_amount"] for inv in invoices), DECIMAL_ZERO)
    total_paid = sum((inv["amount_paid"] for inv in invoices), DECIMAL_ZERO)
    total_tax = sum((compute_tax(inv["invoice_amount"]) for inv in invoices), DECIMAL_ZERO)
    total_outstanding = sum(
        (compute_outstanding(inv["invoice_amount"], inv["amount_paid"]) for inv in invoices),
        DECIMAL_ZERO,
    )
    paid_count = sum(1 for inv in invoices if inv.get("payment_status") == "PAID")
    unpaid_count = sum(1 for inv in invoices if inv.get("payment_status") == "UNPAID")
    partial_count = sum(1 for inv in invoices if inv.get("payment_status") == "PARTIAL")
    cancelled_count = sum(1 for inv in invoices if inv.get("payment_status") == "CANCELLED")

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
        "cancelled_count": cancelled_count,
    }
