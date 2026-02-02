"""EmissionFactor model (reference/lookup table)."""
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy import String, Text, SmallInteger, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class EmissionFactor(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "emission_factors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    factor_value: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    scope_3_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_citation: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str | None] = mapped_column(String(64), nullable=True)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    emission_estimates: Mapped[list["EmissionEstimate"]] = relationship(
        "EmissionEstimate", back_populates="emission_factor"
    )
