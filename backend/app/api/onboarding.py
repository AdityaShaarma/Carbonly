"""Onboarding API endpoints."""
from fastapi import APIRouter, HTTPException
from app.auth import CurrentCompany, DbSession
from app.schemas.onboarding import (
    OnboardingResponse,
    OnboardingState,
    OnboardingUpdateRequest,
)

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


def _normalize_state(state: dict | None) -> OnboardingState:
    state = state or {}
    return OnboardingState(
        connect_aws=bool(state.get("connect_aws", False)),
        upload_csv=bool(state.get("upload_csv", False)),
        add_manual_activity=bool(state.get("add_manual_activity", False)),
        create_report=bool(state.get("create_report", False)),
    )


@router.get("", response_model=OnboardingResponse)
async def get_onboarding(company: CurrentCompany):
    state = _normalize_state(company.onboarding_state)
    completed = all(state.model_dump().values())
    return OnboardingResponse(completed=completed, state=state)


@router.put("", response_model=OnboardingResponse)
async def update_onboarding(
    request: OnboardingUpdateRequest,
    company: CurrentCompany,
    db: DbSession,
):
    state = _normalize_state(company.onboarding_state).model_dump()
    updates = request.model_dump(exclude_none=True)
    state.update(updates)
    company.onboarding_state = state
    await db.commit()
    state_obj = _normalize_state(state)
    completed = all(state_obj.model_dump().values())
    return OnboardingResponse(completed=completed, state=state_obj)
