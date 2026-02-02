"""Reports request/response schemas."""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class ReportListItem(BaseModel):
    id: str
    title: str
    company_name_snapshot: str | None
    reporting_year: int
    total_kg_co2e: Decimal
    status: str  # draft, published
    created_at: datetime
    shareable_token: str | None

    class Config:
        from_attributes = True


class ReportsListResponse(BaseModel):
    reports: list[ReportListItem]


class ReportCreateRequest(BaseModel):
    title: str
    reporting_year: int


class ReportDetailResponse(BaseModel):
    id: str
    title: str
    company_name_snapshot: str | None
    reporting_year: int
    total_kg_co2e: Decimal
    status: str
    shareable_token: str | None
    content_snapshot: dict | None
    created_at: datetime
    generated_at: datetime | None
    published_at: datetime | None

    class Config:
        from_attributes = True


class PublicReportResponse(BaseModel):
    """Public share link response (read-only summary)."""
    company_name: str
    reporting_year: int
    total_co2e: Decimal
    executive_summary: str | None
    scope_breakdown: dict[str, Decimal]
    scope_3_breakdown: dict[str, Decimal] | None
