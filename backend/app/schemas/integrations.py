"""Integrations request/response schemas."""
from datetime import datetime
from pydantic import BaseModel


class IntegrationResponse(BaseModel):
    id: str
    source_type: str
    display_name: str
    status: str  # connected, ai_estimated, not_connected, manual
    last_synced_at: datetime | None

    class Config:
        from_attributes = True


class IntegrationsListResponse(BaseModel):
    integrations: list[IntegrationResponse]


class ManualActivityRequest(BaseModel):
    scope: int
    scope_3_category: str | None = None
    activity_type: str
    quantity: float
    unit: str
    period_start: str  # YYYY-MM-DD
    period_end: str  # YYYY-MM-DD
    data_quality: str = "manual"  # measured, estimated, manual
    assumptions: str | None = None
    confidence_score: float | None = None


class CsvRowSchema(BaseModel):
    """Schema for validating a single CSV row (activity record)."""

    scope: int
    activity_type: str
    quantity: float
    unit: str
    period_start: str  # YYYY-MM-DD
    period_end: str  # YYYY-MM-DD
    scope_3_category: str | None = None
    data_quality: str = "manual"
    assumptions: str | None = None
    confidence_score: float | None = None


class CsvUploadResponse(BaseModel):
    inserted: int
    errors: list[dict]  # [{row: int, error: str}, ...]
