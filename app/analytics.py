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


def average_invoice_amount(invoices: list[dict]) -> Decimal:
    """Return the mean invoice amount across all invoices.

    Args:
        invoices: List of invoice dicts with invoice_amount field.

    Returns:
        Mean invoice amount rounded to 2 decimal places; Decimal("0") if empty.
    """
    if not invoices:
        return Decimal("0")
    total = sum((inv["invoice_amount"] for inv in invoices), Decimal("0"))
    return (total / len(invoices)).quantize(Decimal("0.01"))


def average_days_to_pay(invoices: list[dict], as_of: Optional[date] = None) -> float:
    """Return the mean age (in days) of invoices that are fully paid.

    Only PAID invoices are included in the average; invoices without a
    payment_date field use the invoice_date as the baseline.

    Args:
        invoices: List of invoice dicts with invoice_date and payment_status.
        as_of: Reference date for age calculation (defaults to today).

    Returns:
        Average days to pay rounded to 1 decimal place; 0.0 if no paid invoices.
    """
    reference = as_of or date.today()
    paid = [inv for inv in invoices if inv.get("payment_status") == "PAID"]
    if not paid:
        return 0.0
    total_days = sum((reference - inv["invoice_date"]).days for inv in paid)
    return round(total_days / len(paid), 1)


def incomplete_invoice_count(invoices: list[dict]) -> int:
    """Count invoices that are not fully paid (UNPAID or PARTIAL).

    Args:
        invoices: List of invoice dicts with payment_status field.

    Returns:
        Count of invoices in INCOMPLETE_STATUSES.
    """
    return sum(1 for inv in invoices if inv.get("payment_status") in INCOMPLETE_STATUSES)


def top_currencies_by_invoice_count(
    invoices: list[dict], top_n: int = 5
) -> list[dict]:
    """Return currencies ranked by number of invoices, highest first.

    Args:
        invoices: List of invoice dicts with currency field.
        top_n: Maximum number of currencies to return.

    Returns:
        List of dicts with currency and count keys, sorted by count descending.
    """
    if not invoices:
        return []
    counts: dict[str, int] = defaultdict(int)
    for inv in invoices:
        counts[inv.get("currency", "USD")] += 1
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [{"currency": c, "count": n} for c, n in ranked[:top_n]]


def overdue_by_supplier(
    invoices: list[dict],
    as_of: Optional[date] = None,
    threshold_days: int = OVERDUE_DAYS_THRESHOLD,
) -> list[dict]:
    """Aggregate overdue invoice amounts grouped by supplier.

    Args:
        invoices: List of invoice dicts with supplier, payment_status, invoice_date,
                  invoice_amount, and amount_paid.
        as_of: Reference date (defaults to today).
        threshold_days: Minimum age in days to classify as overdue.

    Returns:
        List of dicts with supplier, overdue_count, and total_outstanding,
        sorted by total_outstanding descending.
    """
    if not invoices:
        return []
    reference = as_of or date.today()
    supplier_totals: dict[str, dict] = defaultdict(
        lambda: {"overdue_count": 0, "total_outstanding": Decimal("0")}
    )
    for inv in invoices:
        if inv.get("payment_status") not in INCOMPLETE_STATUSES:
            continue
        age_days = (reference - inv["invoice_date"]).days
        if age_days <= threshold_days:
            continue
        supplier = inv.get("supplier", "Unknown")
        outstanding = compute_outstanding(inv["invoice_amount"], inv["amount_paid"])
        supplier_totals[supplier]["overdue_count"] += 1
        supplier_totals[supplier]["total_outstanding"] += outstanding

    result = [
        {"supplier": supplier, **data}
        for supplier, data in supplier_totals.items()
    ]
    result.sort(key=lambda x: x["total_outstanding"], reverse=True)
    return result


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
