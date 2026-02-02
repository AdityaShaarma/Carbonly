"""ActivityRecord model."""
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy import String, Text, SmallInteger, Numeric, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class ActivityRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "activity_records"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    data_source_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("data_source_connections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scope: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1, 2, 3
    scope_3_category: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # cloud, travel, remote_work, commuting, purchased_services
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    data_quality: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # measured, estimated, manual
    assumptions: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="activity_records")
    data_source_connection: Mapped["DataSourceConnection | None"] = relationship(
        "DataSourceConnection", back_populates="activity_records"
    )
    emission_estimates: Mapped[list["EmissionEstimate"]] = relationship(
        "EmissionEstimate", back_populates="activity_record"
    )
