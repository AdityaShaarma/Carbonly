"""EmissionEstimate model: Activity × Factor = Emissions (auditable)."""
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy import String, Text, SmallInteger, Numeric, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class EmissionEstimate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "emission_estimates"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity_records.id", ondelete="CASCADE"), nullable=False, index=True
    )
    emission_factor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("emission_factors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    scope: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    scope_3_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    activity_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    factor_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    emissions_kg_co2e: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    data_quality: Mapped[str] = mapped_column(String(32), nullable=False)
    assumptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="emission_estimates")
    activity_record: Mapped["ActivityRecord"] = relationship(
        "ActivityRecord", back_populates="emission_estimates"
    )
    emission_factor: Mapped["EmissionFactor"] = relationship(
        "EmissionFactor", back_populates="emission_estimates"
    )
