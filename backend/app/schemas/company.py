"""Company request/response schemas."""
from pydantic import BaseModel


class CompanyResponse(BaseModel):
    id: str
    name: str
    industry: str | None
    employee_count: int | None
    hq_location: str | None
    reporting_year: int
    email_notifications: bool
    monthly_summary_reports: bool
    unit_system: str

    class Config:
        from_attributes = True


class CompanyUpdateRequest(BaseModel):
    name: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    hq_location: str | None = None
    reporting_year: int | None = None


class PreferencesUpdateRequest(BaseModel):
    email_notifications: bool | None = None
    monthly_summary_reports: bool | None = None
    unit_system: str | None = None


class DeleteDataRequest(BaseModel):
    confirm: bool
