"""Insights response schemas."""
from pydantic import BaseModel


class InsightResponse(BaseModel):
    id: str
    title: str
    description: str
    impact_level: str  # High, Medium, Low
    estimated_reduction_percent: float | None
    category: str | None = None


class InsightsResponse(BaseModel):
    insights: list[InsightResponse]
