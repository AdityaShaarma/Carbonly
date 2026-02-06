"""Update billing defaults and add indexes.

Revision ID: 006_update_billing_defaults_and_indexes
Revises: 004
Create Date: 2026-02-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "006_update_billing_defaults_and_indexes"
down_revision = "005_add_billing_fields_to_companies"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "companies",
        "plan",
        existing_type=sa.String(length=32),
        server_default="demo",
        existing_nullable=False,
    )
    op.execute("UPDATE companies SET plan='demo' WHERE plan='free'")
    op.create_index(
        "ix_companies_stripe_customer_id",
        "companies",
        ["stripe_customer_id"],
        unique=False,
    )
    op.create_index(
        "ix_companies_stripe_subscription_id",
        "companies",
        ["stripe_subscription_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_companies_stripe_subscription_id", table_name="companies")
    op.drop_index("ix_companies_stripe_customer_id", table_name="companies")
    op.alter_column(
        "companies",
        "plan",
        existing_type=sa.String(length=32),
        server_default="free",
        existing_nullable=False,
    )
