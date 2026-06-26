"""Advanced analytics: trends, supplier scoring, and outstanding risk ranking."""

import logging
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Optional

from app.features import compute_outstanding, compute_tax

logger = logging.getLogger(__name__)

OVERDUE_DAYS_THRESHOLD: int = 30
INCOMPLETE_STATUSES: frozenset[str] = frozenset({"UNPAID", "PARTIAL"})


def supplier_outstanding_ranking(invoices: list[dict]) -> list[dict]:
    """Rank suppliers by total outstanding balance, highest first.

    Args:
        invoices: List of invoice dicts with supplier, invoice_amount, amount_paid.

    Returns:
        List of dicts with supplier and total_outstanding, sorted descending.
    """
    if not invoices:
        return []
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for inv in invoices:
        outstanding = compute_outstanding(inv["invoice_amount"], inv["amount_paid"])
        totals[inv["supplier"]] += outstanding

    ranking = [
        {"supplier": supplier, "total_outstanding": amount}
        for supplier, amount in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]
    logger.debug("Ranked %d suppliers by outstanding", len(ranking))
    return ranking


def monthly_invoice_trend(invoices: list[dict]) -> list[dict]:
    """Aggregate invoice amounts by calendar month (YYYY-MM).

    Args:
        invoices: List of invoice dicts with invoice_date, invoice_amount, amount_paid.

    Returns:
        List of monthly summary dicts sorted chronologically.
    """
    if not invoices:
        return []
    monthly: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"invoice_amount": Decimal("0"), "amount_paid": Decimal("0"), "tax": Decimal("0")}
    )
    for inv in invoices:
        inv_date: date = inv["invoice_date"]
        month_key = f"{inv_date.year}-{inv_date.month:02d}"
        monthly[month_key]["invoice_amount"] += inv["invoice_amount"]
        monthly[month_key]["amount_paid"] += inv["amount_paid"]
        monthly[month_key]["tax"] += compute_tax(inv["invoice_amount"])

    trend = [
        {
            "month": month,
            "invoice_amount": data["invoice_amount"],
            "amount_paid": data["amount_paid"],
            "tax": data["tax"],
            "outstanding": data["invoice_amount"] + data["tax"] - data["amount_paid"],
        }
        for month, data in sorted(monthly.items())
    ]
    return trend


def payment_status_distribution(invoices: list[dict]) -> dict[str, int]:
    """Count invoices grouped by payment status.

    Args:
        invoices: List of invoice dicts with payment_status field.

    Returns:
        Dict mapping payment status to count.
    """
    if not invoices:
        return {}
    distribution: dict[str, int] = defaultdict(int)
    for inv in invoices:
        distribution[inv.get("payment_status", "UNKNOWN")] += 1
    return dict(distribution)


def currency_breakdown(invoices: list[dict]) -> list[dict]:
    """Summarise total invoice amounts grouped by currency.

    Args:
        invoices: List of invoice dicts with currency and invoice_amount.

    Returns:
        List of dicts with currency and total_amount, sorted by total descending.
    """
    if not invoices:
        return []
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for inv in invoices:
        totals[inv.get("currency", "USD")] += inv["invoice_amount"]
    return [
        {"currency": currency, "total_amount": amount}
        for currency, amount in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]


def overdue_invoices(
    invoices: list[dict],
    as_of: Optional[date] = None,
    threshold_days: int = OVERDUE_DAYS_THRESHOLD,
) -> list[dict]:
    """Return unpaid or partial invoices older than threshold_days from as_of date.

    Args:
        invoices: List of invoice dicts with payment_status and invoice_date.
        as_of: Reference date (defaults to today).
        threshold_days: Minimum age in days to classify as overdue.

    Returns:
        List of overdue invoice dicts with age_days field, sorted by age descending.
    """
    if not invoices:
        return []
    reference = as_of or date.today()
    overdue = []
    for inv in invoices:
        if inv.get("payment_status") in INCOMPLETE_STATUSES:
            age_days = (reference - inv["invoice_date"]).days
            if age_days > threshold_days:
                overdue.append({**inv, "age_days": age_days})
    overdue.sort(key=lambda x: x["age_days"], reverse=True)
    return overdue
