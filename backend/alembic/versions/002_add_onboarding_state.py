"""Add onboarding_state to companies.

Revision ID: 002
Revises: 001
Create Date: 2026-02-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "companies",
        sa.Column("onboarding_state", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("companies", "onboarding_state")
