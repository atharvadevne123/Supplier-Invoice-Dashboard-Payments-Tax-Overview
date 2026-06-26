"""FastAPI application entry point for the Supplier Invoice Dashboard API."""

import logging
from decimal import Decimal
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.analytics import (
    currency_breakdown,
    monthly_invoice_trend,
    overdue_invoices,
    payment_status_distribution,
    supplier_outstanding_ranking,
)
from app.config import settings
from app.database import SupplierInvoice, create_tables, get_db
from app.features import aggregate_invoices, compute_outstanding, compute_tax
from app.middleware import CorrelationIDMiddleware
from app.schemas import (
    HealthResponse,
    InvoiceCreate,
    InvoiceResponse,
    InvoiceSummary,
    PaginatedInvoices,
    PaymentStatus,
)
from app.utils import paginate

logger = logging.getLogger(__name__)

logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="REST API for supplier invoice analytics replicating Oracle OTBI payables reporting.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    """Initialise database tables on application start."""
    create_tables()
    logger.info("Supplier Invoice Dashboard API started")


def _to_response(inv: SupplierInvoice) -> InvoiceResponse:
    """Convert an ORM instance to a response schema with computed fields."""
    tax = compute_tax(inv.invoice_amount)
    outstanding = compute_outstanding(inv.invoice_amount, inv.amount_paid)
    return InvoiceResponse(
        invoice_number=inv.invoice_number,
        business_unit=inv.business_unit,
        supplier=inv.supplier,
        invoice_date=inv.invoice_date,
        invoice_amount=inv.invoice_amount,
        amount_paid=inv.amount_paid,
        currency=inv.currency,
        payment_status=inv.payment_status,
        tax_amount=tax,
        outstanding_amount=outstanding,
    )


@app.get(f"{settings.api_prefix}/health", response_model=HealthResponse, tags=["Operations"])
def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    """Return API liveness and database connectivity status."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        logger.exception("Database health check failed")
        db_status = "disconnected"
    return HealthResponse(status="ok", version=settings.app_version, database=db_status)


@app.get(f"{settings.api_prefix}/version", tags=["Operations"])
def get_version() -> dict:
    """Return the current API version."""
    return {"version": settings.app_version, "app": settings.app_name}


@app.get(f"{settings.api_prefix}/invoices", response_model=PaginatedInvoices, tags=["Invoices"])
def list_invoices(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=200, description="Items per page"),
    supplier: Optional[str] = Query(None),
    business_unit: Optional[str] = Query(None),
    payment_status: Optional[PaymentStatus] = Query(None),
    currency: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> PaginatedInvoices:
    """List supplier invoices with optional filtering and pagination."""
    query = db.query(SupplierInvoice)
    if supplier:
        query = query.filter(SupplierInvoice.supplier.ilike(f"%{supplier}%"))
    if business_unit:
        query = query.filter(SupplierInvoice.business_unit.ilike(f"%{business_unit}%"))
    if payment_status:
        query = query.filter(SupplierInvoice.payment_status == payment_status.value)
    if currency:
        query = query.filter(SupplierInvoice.currency == currency.upper())

    all_records = query.all()
    total = len(all_records)
    page_records, total_pages = paginate(all_records, page, page_size)
    return PaginatedInvoices(
        items=[_to_response(inv) for inv in page_records],
        total=total,
        page=page,
        page_size=page_size,
        pages=total_pages,
    )


@app.post(
    f"{settings.api_prefix}/invoices",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Invoices"],
)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)) -> InvoiceResponse:
    """Create a new supplier invoice record."""
    existing = db.query(SupplierInvoice).filter(
        SupplierInvoice.invoice_number == payload.invoice_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invoice {payload.invoice_number} already exists",
        )
    try:
        inv = SupplierInvoice(**payload.model_dump())
        db.add(inv)
        db.commit()
        db.refresh(inv)
    except Exception:
        db.rollback()
        logger.exception("Failed to create invoice %s", payload.invoice_number)
        raise HTTPException(status_code=500, detail="Failed to save invoice")
    return _to_response(inv)


@app.get(
    f"{settings.api_prefix}/invoices/{{invoice_number}}",
    response_model=InvoiceResponse,
    tags=["Invoices"],
)
def get_invoice(invoice_number: str, db: Session = Depends(get_db)) -> InvoiceResponse:
    """Retrieve a single invoice by invoice number."""
    inv = db.query(SupplierInvoice).filter(
        SupplierInvoice.invoice_number == invoice_number
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found")
    return _to_response(inv)


@app.get(f"{settings.api_prefix}/summary", response_model=InvoiceSummary, tags=["Analytics"])
def get_summary(
    supplier: Optional[str] = Query(None),
    business_unit: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> InvoiceSummary:
    """Return aggregated invoice statistics, optionally filtered by supplier or BU."""
    query = db.query(SupplierInvoice)
    if supplier:
        query = query.filter(SupplierInvoice.supplier.ilike(f"%{supplier}%"))
    if business_unit:
        query = query.filter(SupplierInvoice.business_unit.ilike(f"%{business_unit}%"))
    records = query.all()
    inv_dicts = [
        {
            "invoice_amount": r.invoice_amount,
            "amount_paid": r.amount_paid,
            "payment_status": r.payment_status,
        }
        for r in records
    ]
    agg = aggregate_invoices(inv_dicts)
    return InvoiceSummary(**agg)


@app.get(f"{settings.api_prefix}/analytics/supplier-ranking", tags=["Analytics"])
def get_supplier_ranking(db: Session = Depends(get_db)) -> list[dict]:
    """Rank all suppliers by total outstanding balance (highest first)."""
    records = db.query(SupplierInvoice).all()
    inv_dicts = [
        {
            "supplier": r.supplier,
            "invoice_amount": r.invoice_amount,
            "amount_paid": r.amount_paid,
        }
        for r in records
    ]
    return supplier_outstanding_ranking(inv_dicts)


@app.get(f"{settings.api_prefix}/analytics/monthly-trend", tags=["Analytics"])
def get_monthly_trend(db: Session = Depends(get_db)) -> list[dict]:
    """Return monthly aggregated invoice and payment totals."""
    records = db.query(SupplierInvoice).all()
    inv_dicts = [
        {
            "invoice_date": r.invoice_date,
            "invoice_amount": r.invoice_amount,
            "amount_paid": r.amount_paid,
        }
        for r in records
    ]
    return monthly_invoice_trend(inv_dicts)


@app.get(f"{settings.api_prefix}/analytics/currency-breakdown", tags=["Analytics"])
def get_currency_breakdown(db: Session = Depends(get_db)) -> list[dict]:
    """Summarise invoice totals grouped by currency."""
    records = db.query(SupplierInvoice).all()
    inv_dicts = [
        {"currency": r.currency, "invoice_amount": r.invoice_amount}
        for r in records
    ]
    return currency_breakdown(inv_dicts)


@app.get(f"{settings.api_prefix}/analytics/overdue", tags=["Analytics"])
def get_overdue_invoices(db: Session = Depends(get_db)) -> list[dict]:
    """Return unpaid/partial invoices that are more than 30 days old."""
    records = db.query(SupplierInvoice).filter(
        SupplierInvoice.payment_status.in_(["UNPAID", "PARTIAL"])
    ).all()
    inv_dicts = [
        {
            "invoice_number": r.invoice_number,
            "supplier": r.supplier,
            "invoice_date": r.invoice_date,
            "invoice_amount": r.invoice_amount,
            "amount_paid": r.amount_paid,
            "payment_status": r.payment_status,
        }
        for r in records
    ]
    return overdue_invoices(inv_dicts)


@app.get(f"{settings.api_prefix}/analytics/status-distribution", tags=["Analytics"])
def get_status_distribution(db: Session = Depends(get_db)) -> dict:
    """Return counts of invoices grouped by payment status."""
    records = db.query(SupplierInvoice).all()
    inv_dicts = [{"payment_status": r.payment_status} for r in records]
    return payment_status_distribution(inv_dicts)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)


@app.get(f"{settings.api_prefix}/report/view-selector", tags=["Reports"])
def get_view_selector(
    supplier: Optional[str] = Query(None),
    business_unit: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    """Return table-view and graph-view payloads for the OTBI view-selector UI."""
    from app.reporting import build_view_selector_payload

    query = db.query(SupplierInvoice)
    if supplier:
        query = query.filter(SupplierInvoice.supplier.ilike(f"%{supplier}%"))
    if business_unit:
        query = query.filter(SupplierInvoice.business_unit.ilike(f"%{business_unit}%"))
    records = query.all()
    inv_dicts = [
        {
            "invoice_number": r.invoice_number,
            "business_unit": r.business_unit,
            "supplier": r.supplier,
            "invoice_date": r.invoice_date,
            "invoice_amount": r.invoice_amount,
            "amount_paid": r.amount_paid,
            "currency": r.currency,
            "payment_status": r.payment_status,
        }
        for r in records
    ]
    return build_view_selector_payload(inv_dicts)


@app.get(f"{settings.api_prefix}/metrics", tags=["Operations"])
def get_metrics(db: Session = Depends(get_db)) -> dict:
    """Return basic operational metrics for monitoring dashboards."""
    try:
        total = db.query(SupplierInvoice).count()
        unpaid = db.query(SupplierInvoice).filter(
            SupplierInvoice.payment_status == "UNPAID"
        ).count()
        paid = db.query(SupplierInvoice).filter(
            SupplierInvoice.payment_status == "PAID"
        ).count()
    except Exception:
        logger.exception("Metrics query failed")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")
    return {
        "total_invoices": total,
        "unpaid_invoices": unpaid,
        "paid_invoices": paid,
        "unpaid_ratio": round(unpaid / total, 4) if total else 0,
    }


@app.get(f"{settings.api_prefix}/analytics/currency-normalized", tags=["Analytics"])
def get_currency_normalized(db: Session = Depends(get_db)) -> list[dict]:
    """Return all invoices with invoice amounts normalized to USD."""
    from app.currency import normalize_to_usd

    records = db.query(SupplierInvoice).all()
    inv_dicts = [
        {
            "invoice_number": r.invoice_number,
            "supplier": r.supplier,
            "invoice_amount": r.invoice_amount,
            "currency": r.currency,
        }
        for r in records
    ]
    return normalize_to_usd(inv_dicts)


@app.patch(
    f"{settings.api_prefix}/invoices/{{invoice_number}}",
    response_model=InvoiceResponse,
    tags=["Invoices"],
)
def update_invoice_payment(
    invoice_number: str,
    amount_paid: Decimal = Query(..., gt=Decimal("0"), description="New total amount paid"),
    payment_status: Optional[PaymentStatus] = Query(None),
    db: Session = Depends(get_db),
) -> InvoiceResponse:
    """Update the paid amount and optionally the payment status of an invoice."""
    inv = db.query(SupplierInvoice).filter(
        SupplierInvoice.invoice_number == invoice_number
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found")
    if amount_paid > inv.invoice_amount:
        raise HTTPException(
            status_code=422, detail="amount_paid cannot exceed invoice_amount"
        )
    try:
        inv.amount_paid = amount_paid
        if payment_status:
            inv.payment_status = payment_status.value
        db.commit()
        db.refresh(inv)
    except Exception:
        db.rollback()
        logger.exception("Failed to update invoice %s", invoice_number)
        raise HTTPException(status_code=500, detail="Failed to update invoice")
    return _to_response(inv)


@app.delete(
    f"{settings.api_prefix}/invoices/{{invoice_number}}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Invoices"],
)
def delete_invoice(invoice_number: str, db: Session = Depends(get_db)) -> None:
    """Delete a supplier invoice by invoice number."""
    inv = db.query(SupplierInvoice).filter(
        SupplierInvoice.invoice_number == invoice_number
    ).first()
    if not inv:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found")
    try:
        db.delete(inv)
        db.commit()
        logger.info("Deleted invoice %s", invoice_number)
    except Exception:
        db.rollback()
        logger.exception("Failed to delete invoice %s", invoice_number)
        raise HTTPException(status_code=500, detail="Failed to delete invoice")
