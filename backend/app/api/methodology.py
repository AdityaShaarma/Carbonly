"""Methodology API endpoints."""
from fastapi import APIRouter
from app.schemas.methodology import MethodologyResponse

router = APIRouter(prefix="/api/methodology", tags=["methodology"])


@router.get("", response_model=MethodologyResponse)
async def get_methodology():
    return MethodologyResponse(
        factors_source="EPA, DEFRA, and cloud provider sustainability reports",
        supported_scopes=[
            "Scope 1 (direct emissions)",
            "Scope 2 (purchased electricity)",
            "Scope 3 (cloud, commuting, travel, remote work, purchased services)",
        ],
        confidence_calculation="Confidence is derived from source quality (measured/estimated/manual) and data completeness.",
        measured_vs_estimated="Measured data comes from connected sources; estimated data is modeled from benchmarks; manual data is user-provided.",
    )
