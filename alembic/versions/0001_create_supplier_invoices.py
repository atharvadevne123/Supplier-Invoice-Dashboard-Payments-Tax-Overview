"""Create supplier_invoices table.

Revision ID: 0001
Revises:
Create Date: 2026-06-11
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the supplier_invoices table with all indexes."""
    op.create_table(
        "supplier_invoices",
        sa.Column("invoice_number", sa.String(50), primary_key=True),
        sa.Column("business_unit", sa.String(100), nullable=False),
        sa.Column("supplier", sa.String(200), nullable=False),
        sa.Column("invoice_date", sa.Date, nullable=False),
        sa.Column("invoice_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("amount_paid", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column("payment_status", sa.String(50), nullable=False, server_default="UNPAID"),
    )
    op.create_index("ix_supplier_invoices_invoice_number", "supplier_invoices", ["invoice_number"])
    op.create_index("ix_supplier_invoices_business_unit", "supplier_invoices", ["business_unit"])
    op.create_index("ix_supplier_invoices_supplier", "supplier_invoices", ["supplier"])
    op.create_index(
        "ix_invoice_supplier_date", "supplier_invoices", ["supplier", "invoice_date"]
    )
    op.create_index("ix_invoice_status", "supplier_invoices", ["payment_status"])


def downgrade() -> None:
    """Drop the supplier_invoices table and its indexes."""
    op.drop_index("ix_invoice_status", table_name="supplier_invoices")
    op.drop_index("ix_invoice_supplier_date", table_name="supplier_invoices")
    op.drop_index("ix_supplier_invoices_supplier", table_name="supplier_invoices")
    op.drop_index("ix_supplier_invoices_business_unit", table_name="supplier_invoices")
    op.drop_index("ix_supplier_invoices_invoice_number", table_name="supplier_invoices")
    op.drop_table("supplier_invoices")
