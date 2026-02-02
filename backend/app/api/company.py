"""Company/Settings API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentCompany, CurrentUser, DbSession
from app.models.activity_record import ActivityRecord
from app.models.data_source_connection import DataSourceConnection
from app.models.emission_estimate import EmissionEstimate
from app.models.emissions_summary import EmissionsSummary
from app.models.report import Report
from app.schemas.company import (
    CompanyResponse,
    CompanyUpdateRequest,
    DeleteDataRequest,
    PreferencesUpdateRequest,
)

router = APIRouter(prefix="/api/company", tags=["company"])


@router.get("", response_model=CompanyResponse)
async def get_company(
    company: CurrentCompany = None,
):
    """Get company profile and preferences."""
    return CompanyResponse(
        id=str(company.id),
        name=company.name,
        industry=company.industry,
        employee_count=company.employee_count,
        hq_location=company.hq_location,
        reporting_year=company.reporting_year,
        email_notifications=company.email_notifications,
        monthly_summary_reports=company.monthly_summary_reports,
        unit_system=company.unit_system,
    )


@router.put("", response_model=CompanyResponse)
async def update_company(
    request: CompanyUpdateRequest,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """Update company profile."""
    if request.name is not None:
        company.name = request.name
    if request.industry is not None:
        company.industry = request.industry
    if request.employee_count is not None:
        company.employee_count = request.employee_count
    if request.hq_location is not None:
        company.hq_location = request.hq_location
    if request.reporting_year is not None:
        company.reporting_year = request.reporting_year

    await db.commit()
    await db.refresh(company)

    return CompanyResponse(
        id=str(company.id),
        name=company.name,
        industry=company.industry,
        employee_count=company.employee_count,
        hq_location=company.hq_location,
        reporting_year=company.reporting_year,
        email_notifications=company.email_notifications,
        monthly_summary_reports=company.monthly_summary_reports,
        unit_system=company.unit_system,
    )


@router.put("/preferences", response_model=CompanyResponse)
async def update_preferences(
    request: PreferencesUpdateRequest,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """Update company preferences."""
    if request.email_notifications is not None:
        company.email_notifications = request.email_notifications
    if request.monthly_summary_reports is not None:
        company.monthly_summary_reports = request.monthly_summary_reports
    if request.unit_system is not None:
        company.unit_system = request.unit_system

    await db.commit()
    await db.refresh(company)

    return CompanyResponse(
        id=str(company.id),
        name=company.name,
        industry=company.industry,
        employee_count=company.employee_count,
        hq_location=company.hq_location,
        reporting_year=company.reporting_year,
        email_notifications=company.email_notifications,
        monthly_summary_reports=company.monthly_summary_reports,
        unit_system=company.unit_system,
    )


@router.delete("/data")
async def delete_company_data(
    request: DeleteDataRequest,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """Delete all company data (activities, estimates, summaries, reports). Requires confirmation flag."""
    if not request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation required. Set 'confirm: true' in request body.",
        )

    # Delete in order (respecting foreign keys)
    await db.execute(delete(Report).where(Report.company_id == company.id))
    await db.execute(delete(EmissionsSummary).where(EmissionsSummary.company_id == company.id))
    await db.execute(delete(EmissionEstimate).where(EmissionEstimate.company_id == company.id))
    await db.execute(delete(ActivityRecord).where(ActivityRecord.company_id == company.id))
    await db.execute(delete(DataSourceConnection).where(DataSourceConnection.company_id == company.id))
    await db.commit()

    return {"status": "deleted", "message": "All company data has been deleted"}
