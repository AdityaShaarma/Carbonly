"""Onboarding schemas."""
from pydantic import BaseModel


class OnboardingState(BaseModel):
    connect_aws: bool = False
    upload_csv: bool = False
    add_manual_activity: bool = False
    create_report: bool = False
    confirm_company_details: bool = False


class OnboardingResponse(BaseModel):
    completed: bool
    state: OnboardingState


class OnboardingUpdateRequest(BaseModel):
    connect_aws: bool | None = None
    upload_csv: bool | None = None
    add_manual_activity: bool | None = None
    create_report: bool | None = None
    confirm_company_details: bool | None = None
