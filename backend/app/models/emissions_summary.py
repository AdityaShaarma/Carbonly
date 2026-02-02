"""EmissionsSummary model: pre-aggregated totals for dashboard/reports."""
import uuid
from decimal import Decimal
from sqlalchemy import String, Integer, SmallInteger, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class EmissionsSummary(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "emissions_summaries"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "reporting_year",
            "period_type",
            "period_value",
            "scope",
            "scope_3_category",
            name="uq_emissions_summary_period_scope",
        ),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reporting_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_type: Mapped[str] = mapped_column(String(16), nullable=False)  # annual, monthly
    period_value: Mapped[str] = mapped_column(String(16), nullable=False)  # 2024, 2024-01
    scope: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    scope_3_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    total_kg_co2e: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    measured_kg_co2e: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=0, nullable=False)
    estimated_kg_co2e: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=0, nullable=False)
    manual_kg_co2e: Mapped[Decimal] = mapped_column(Numeric(18, 6), default=0, nullable=False)
    confidence_score_avg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="emissions_summaries")
