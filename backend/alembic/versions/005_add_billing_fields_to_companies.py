"""Add billing fields to companies.

Revision ID: 005_add_billing_fields_to_companies
Revises: 005a_widen_alembic_version
Create Date: 2026-02-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "005_add_billing_fields_to_companies"
down_revision = "005a_widen_alembic_version"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("companies", sa.Column("stripe_customer_id", sa.String(length=255), nullable=True))
    op.add_column("companies", sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True))
    op.add_column(
        "companies",
        sa.Column("plan", sa.String(length=32), nullable=False, server_default="free"),
    )
    op.add_column(
        "companies",
        sa.Column("billing_status", sa.String(length=32), nullable=False, server_default="inactive"),
    )
    op.add_column(
        "companies",
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("companies", "current_period_end")
    op.drop_column("companies", "billing_status")
    op.drop_column("companies", "plan")
    op.drop_column("companies", "stripe_subscription_id")
    op.drop_column("companies", "stripe_customer_id")
