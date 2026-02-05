"""Company model."""
import uuid
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Company(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(64), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hq_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reporting_year: Mapped[int] = mapped_column(Integer, nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    monthly_summary_reports: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    unit_system: Mapped[str] = mapped_column(String(32), default="metric_tco2e", nullable=False)
    onboarding_state: Mapped[dict | None] = mapped_column("onboarding_state", JSONB, nullable=True)

    users: Mapped[list["User"]] = relationship("User", back_populates="company")
    data_source_connections: Mapped[list["DataSourceConnection"]] = relationship(
        "DataSourceConnection", back_populates="company"
    )
    activity_records: Mapped[list["ActivityRecord"]] = relationship(
        "ActivityRecord", back_populates="company"
    )
    emission_estimates: Mapped[list["EmissionEstimate"]] = relationship(
        "EmissionEstimate", back_populates="company"
    )
    emissions_summaries: Mapped[list["EmissionsSummary"]] = relationship(
        "EmissionsSummary", back_populates="company"
    )
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="company")
