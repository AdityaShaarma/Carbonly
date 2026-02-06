"""Widen alembic_version.version_num to TEXT.

Revision ID: 005a_widen_alembic_version
Revises: 004
Create Date: 2026-02-01
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "005a_widen_alembic_version"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expand alembic_version.version_num to TEXT for long revision IDs.
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE TEXT")


def downgrade() -> None:
    # Optional: revert to VARCHAR(32) if needed.
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(32)")
