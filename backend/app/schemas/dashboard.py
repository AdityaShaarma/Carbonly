"""Dashboard response schemas."""
from decimal import Decimal
from pydantic import BaseModel


class ScopeTotal(BaseModel):
    scope: int
    scope_3_category: str | None
    total_kg_co2e: Decimal
    measured_kg_co2e: Decimal
    estimated_kg_co2e: Decimal
    manual_kg_co2e: Decimal
    confidence_score_avg: Decimal | None


class Scope3CategoryTotal(BaseModel):
    category: str
    total_kg_co2e: Decimal


class MonthlyTrendPoint(BaseModel):
    month: str  # "2024-01"
    scope_1: Decimal
    scope_2: Decimal
    scope_3: Decimal
    total: Decimal


class DataQualityStats(BaseModel):
    overall_confidence: Decimal | None
    connected_sources_count: int
    ai_estimated_sources_count: int
    manual_entries_count: int


class DashboardResponse(BaseModel):
    company_stats: dict[str, int | str]  # employees, cloud_providers_count, reporting_year
    annual_totals: dict  # Mixed: total_co2e (Decimal), scope_1/2/3 (Decimal), scope_totals (list[ScopeTotal]), scope3_by_category (list[Scope3CategoryTotal])
    data_quality: DataQualityStats
    monthly_trend: list[MonthlyTrendPoint]
