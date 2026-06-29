"""Report generation utilities: build tabular and graph-view data structures."""

import logging
from decimal import Decimal
from typing import Any

from app.features import (
    DECIMAL_ZERO,
    apply_conditional_formatting,
    compute_outstanding,
    compute_tax,
)

logger = logging.getLogger(__name__)


def _compute_row_fields(inv: dict) -> tuple[Decimal, Decimal, str]:
    """Compute tax, outstanding, and colour label for a single invoice row.

    Args:
        inv: Invoice dict with invoice_amount and amount_paid.

    Returns:
        Tuple of (tax_amount, outstanding_amount, color_label).
    """
    tax = compute_tax(inv["invoice_amount"])
    outstanding = compute_outstanding(inv["invoice_amount"], inv["amount_paid"])
    color = apply_conditional_formatting(outstanding, inv["invoice_amount"])
    return tax, outstanding, color


def build_table_view(invoices: list[dict]) -> list[dict]:
    """Construct the tabular view rows matching the OTBI dashboard layout.

    Each row includes all base columns plus computed tax, outstanding, and
    the colour label for conditional formatting.

    Args:
        invoices: List of invoice dicts with base fields.

    Returns:
        List of enriched row dicts suitable for table rendering.
    """
    if not invoices:
        return []
    rows = []
    for inv in invoices:
        tax, outstanding, color = _compute_row_fields(inv)
        rows.append(
            {
                "business_unit": inv["business_unit"],
                "supplier": inv["supplier"],
                "invoice_number": inv["invoice_number"],
                "invoice_date": str(inv["invoice_date"]),
                "invoice_amount": inv["invoice_amount"],
                "amount_paid": inv["amount_paid"],
                "tax_amount": tax,
                "outstanding_amount": outstanding,
                "currency": inv["currency"],
                "payment_status": inv["payment_status"],
                "color_label": color,
            }
        )
    logger.debug("Built table view with %d rows", len(rows))
    return rows


def build_graph_view(invoices: list[dict]) -> dict[str, Any]:
    """Aggregate totals for the graph-view bar/pie chart.

    Args:
        invoices: List of invoice dicts.

    Returns:
        Dict with series list and total_invoices, suitable for direct JSON serialisation.
    """
    total_invoice = sum((inv["invoice_amount"] for inv in invoices), DECIMAL_ZERO)
    total_paid = sum((inv["amount_paid"] for inv in invoices), DECIMAL_ZERO)
    total_tax = sum((compute_tax(inv["invoice_amount"]) for inv in invoices), DECIMAL_ZERO)
    total_outstanding = sum(
        (compute_outstanding(inv["invoice_amount"], inv["amount_paid"]) for inv in invoices),
        DECIMAL_ZERO,
    )
    return {
        "series": [
            {"label": "Invoice Amount", "value": total_invoice},
            {"label": "Tax", "value": total_tax},
            {"label": "Amount Paid", "value": total_paid},
            {"label": "Outstanding", "value": total_outstanding},
        ],
        "total_invoices": len(invoices),
    }


def build_summary_cards(invoices: list[dict]) -> list[dict[str, Any]]:
    """Build KPI summary card data for the dashboard header row.

    Returns four cards: Total Invoices, Total Amount, Total Paid, Total Outstanding.

    Args:
        invoices: List of invoice dicts with invoice_amount and amount_paid.

    Returns:
        List of card dicts with label and value keys.
    """
    total_amount = sum((inv["invoice_amount"] for inv in invoices), DECIMAL_ZERO)
    total_paid = sum((inv["amount_paid"] for inv in invoices), DECIMAL_ZERO)
    total_outstanding = sum(
        (compute_outstanding(inv["invoice_amount"], inv["amount_paid"]) for inv in invoices),
        DECIMAL_ZERO,
    )
    return [
        {"label": "Total Invoices", "value": len(invoices)},
        {"label": "Total Amount", "value": total_amount},
        {"label": "Total Paid", "value": total_paid},
        {"label": "Total Outstanding", "value": total_outstanding},
    ]


def build_payment_summary(invoices: list[dict]) -> dict[str, Any]:
    """Summarise payment completion as a percentage and breakdown.

    Args:
        invoices: List of invoice dicts with invoice_amount and amount_paid.

    Returns:
        Dict with total_invoices, paid_count, unpaid_count, partial_count,
        and payment_completion_pct (0-100 rounded to 2dp).
    """
    total = len(invoices)
    paid_count = sum(1 for inv in invoices if inv.get("payment_status") == "PAID")
    unpaid_count = sum(1 for inv in invoices if inv.get("payment_status") == "UNPAID")
    partial_count = sum(1 for inv in invoices if inv.get("payment_status") == "PARTIAL")
    completion_pct = round((paid_count / total * 100), 2) if total else 0.0
    return {
        "total_invoices": total,
        "paid_count": paid_count,
        "unpaid_count": unpaid_count,
        "partial_count": partial_count,
        "payment_completion_pct": completion_pct,
    }


def build_overdue_report(invoices: list[dict], threshold_days: int = 30) -> dict[str, Any]:
    """Build a structured overdue-invoice report payload.

    Args:
        invoices: List of invoice dicts with all standard fields.
        threshold_days: Minimum age in days to classify as overdue.

    Returns:
        Dict with overdue_count, total_overdue_amount, and rows keys.
    """
    from app.analytics import overdue_invoices

    overdue = overdue_invoices(invoices, threshold_days=threshold_days)
    total_overdue_amount = sum(
        (compute_outstanding(inv["invoice_amount"], inv["amount_paid"]) for inv in overdue),
        DECIMAL_ZERO,
    )
    return {
        "overdue_count": len(overdue),
        "total_overdue_amount": total_overdue_amount,
        "rows": overdue,
    }


def build_view_selector_payload(invoices: list[dict]) -> dict[str, Any]:
    """Return both table and graph views in a single payload for the view-selector UI.

    Args:
        invoices: List of invoice dicts.

    Returns:
        Dict with table_view and graph_view keys.
    """
    return {
        "table_view": build_table_view(invoices),
        "graph_view": build_graph_view(invoices),
    }
