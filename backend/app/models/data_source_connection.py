"""DataSourceConnection model."""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class DataSourceConnection(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "data_source_connections"
    __table_args__ = (UniqueConstraint("company_id", "source_type", name="uq_company_source_type"),)

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # connected, ai_estimated, not_connected, manual
    credentials_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(nullable=True)

    company: Mapped["Company"] = relationship("Company", back_populates="data_source_connections")
    activity_records: Mapped[list["ActivityRecord"]] = relationship(
        "ActivityRecord", back_populates="data_source_connection"
    )
