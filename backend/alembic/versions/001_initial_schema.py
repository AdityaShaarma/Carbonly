"""Initial schema: users, companies, data_source_connections, activity_records, emission_factors, emission_estimates, emissions_summaries, reports.

Revision ID: 001
Revises:
Create Date: 2025-02-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("industry", sa.String(64), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("hq_location", sa.String(255), nullable=True),
        sa.Column("reporting_year", sa.Integer(), nullable=False),
        sa.Column("email_notifications", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("monthly_summary_reports", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("unit_system", sa.String(32), nullable=False, server_default="metric_tco2e"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("google_id"),
    )
    op.create_index("ix_users_company_id", "users", ["company_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_google_id", "users", ["google_id"])

    op.create_table(
        "data_source_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "source_type", name="uq_company_source_type"),
    )
    op.create_index("ix_data_source_connections_company_id", "data_source_connections", ["company_id"])

    op.create_table(
        "emission_factors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("activity_type", sa.String(64), nullable=False),
        sa.Column("factor_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("scope", sa.SmallInteger(), nullable=False),
        sa.Column("scope_3_category", sa.String(64), nullable=True),
        sa.Column("source_citation", sa.Text(), nullable=True),
        sa.Column("region", sa.String(64), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emission_factors_activity_type", "emission_factors", ["activity_type"])

    op.create_table(
        "activity_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("data_source_connection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope", sa.SmallInteger(), nullable=False),
        sa.Column("scope_3_category", sa.String(64), nullable=True),
        sa.Column("activity_type", sa.String(64), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("unit", sa.String(32), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("data_quality", sa.String(32), nullable=False),
        sa.Column("assumptions", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["data_source_connection_id"], ["data_source_connections.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_records_company_id", "activity_records", ["company_id"])
    op.create_index("ix_activity_records_data_source_connection_id", "activity_records", ["data_source_connection_id"])

    op.create_table(
        "emission_estimates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_record_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("emission_factor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scope", sa.SmallInteger(), nullable=False),
        sa.Column("scope_3_category", sa.String(64), nullable=True),
        sa.Column("activity_quantity", sa.Numeric(18, 6), nullable=False),
        sa.Column("factor_value", sa.Numeric(18, 6), nullable=False),
        sa.Column("emissions_kg_co2e", sa.Numeric(18, 6), nullable=False),
        sa.Column("data_quality", sa.String(32), nullable=False),
        sa.Column("assumptions", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["activity_record_id"], ["activity_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["emission_factor_id"], ["emission_factors.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emission_estimates_company_id", "emission_estimates", ["company_id"])
    op.create_index("ix_emission_estimates_activity_record_id", "emission_estimates", ["activity_record_id"])
    op.create_index("ix_emission_estimates_emission_factor_id", "emission_estimates", ["emission_factor_id"])

    op.create_table(
        "emissions_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reporting_year", sa.Integer(), nullable=False),
        sa.Column("period_type", sa.String(16), nullable=False),
        sa.Column("period_value", sa.String(16), nullable=False),
        sa.Column("scope", sa.SmallInteger(), nullable=False),
        sa.Column("scope_3_category", sa.String(64), nullable=True),
        sa.Column("total_kg_co2e", sa.Numeric(18, 6), nullable=False),
        sa.Column("measured_kg_co2e", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("estimated_kg_co2e", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("manual_kg_co2e", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("confidence_score_avg", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "reporting_year", "period_type", "period_value", "scope", "scope_3_category",
            name="uq_emissions_summary_period_scope",
        ),
    )
    op.create_index("ix_emissions_summaries_company_id", "emissions_summaries", ["company_id"])

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company_name_snapshot", sa.String(255), nullable=True),
        sa.Column("reporting_year", sa.Integer(), nullable=False),
        sa.Column("total_kg_co2e", sa.Numeric(18, 6), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("shareable_token", sa.String(64), nullable=True),
        sa.Column("pdf_path", sa.String(512), nullable=True),
        sa.Column("content_snapshot", postgresql.JSONB(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("shareable_token"),
    )
    op.create_index("ix_reports_company_id", "reports", ["company_id"])
    op.create_index("ix_reports_created_by_user_id", "reports", ["created_by_user_id"])
    op.create_index("ix_reports_shareable_token", "reports", ["shareable_token"])


def downgrade() -> None:
    op.drop_index("ix_reports_shareable_token", "reports")
    op.drop_index("ix_reports_created_by_user_id", "reports")
    op.drop_index("ix_reports_company_id", "reports")
    op.drop_table("reports")
    op.drop_index("ix_emissions_summaries_company_id", "emissions_summaries")
    op.drop_table("emissions_summaries")
    op.drop_index("ix_emission_estimates_emission_factor_id", "emission_estimates")
    op.drop_index("ix_emission_estimates_activity_record_id", "emission_estimates")
    op.drop_index("ix_emission_estimates_company_id", "emission_estimates")
    op.drop_table("emission_estimates")
    op.drop_index("ix_activity_records_data_source_connection_id", "activity_records")
    op.drop_index("ix_activity_records_company_id", "activity_records")
    op.drop_table("activity_records")
    op.drop_index("ix_emission_factors_activity_type", "emission_factors")
    op.drop_table("emission_factors")
    op.drop_index("ix_data_source_connections_company_id", "data_source_connections")
    op.drop_table("data_source_connections")
    op.drop_index("ix_users_google_id", "users")
    op.drop_index("ix_users_email", "users")
    op.drop_index("ix_users_company_id", "users")
    op.drop_table("users")
    op.drop_table("companies")
