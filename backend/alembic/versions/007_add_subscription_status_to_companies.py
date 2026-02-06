"""Add subscription_status to companies.

Revision ID: 007_add_subscription_status_to_companies
Revises: 006_update_billing_defaults_and_indexes
Create Date: 2026-02-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007_add_subscription_status_to_companies"
down_revision: Union[str, None] = "006_update_billing_defaults_and_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("subscription_status", sa.String(length=32), nullable=False, server_default="inactive"),
    )
    op.execute("UPDATE companies SET subscription_status = billing_status")
    op.alter_column("companies", "subscription_status", server_default=None)


def downgrade() -> None:
    op.drop_column("companies", "subscription_status")
