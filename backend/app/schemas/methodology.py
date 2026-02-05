"""Methodology schema."""
from pydantic import BaseModel


class MethodologyResponse(BaseModel):
    factors_source: str
    supported_scopes: list[str]
    confidence_calculation: str
    measured_vs_estimated: str
