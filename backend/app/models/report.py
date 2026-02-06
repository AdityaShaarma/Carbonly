"""Report model: carbon disclosure reports (draft/published)."""
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Report(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reports"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name_snapshot: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reporting_year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_kg_co2e: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)  # draft, published
    shareable_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="reports")
    created_by_user: Mapped["User"] = relationship(
        "User", back_populates="reports", foreign_keys=[created_by_user_id]
    )
