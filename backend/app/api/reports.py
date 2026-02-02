"""Reports API endpoints."""
import secrets
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentCompany, CurrentUser, DbSession
from app.models.report import Report
from app.schemas.reports import (
    ReportCreateRequest,
    ReportDetailResponse,
    ReportListItem,
    ReportsListResponse,
)
from app.services.emissions import (
    get_annual_totals_by_scope,
    get_monthly_breakdown_by_scope,
    refresh_emissions_summaries,
)
from app.services.pdf_report import render_report_pdf

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=ReportsListResponse)
async def list_reports(
    year: Annotated[int | None, Query(description="Filter by reporting year")] = None,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """List all reports for the company."""
    q = select(Report).where(Report.company_id == company.id)
    if year is not None:
        q = q.where(Report.reporting_year == year)
    q = q.order_by(Report.created_at.desc())
    result = await db.execute(q)
    reports = result.scalars().all()

    return ReportsListResponse(
        reports=[
            ReportListItem(
                id=str(r.id),
                title=r.title,
                company_name_snapshot=r.company_name_snapshot,
                reporting_year=r.reporting_year,
                total_kg_co2e=r.total_kg_co2e,
                status=r.status,
                created_at=r.created_at,
                shareable_token=r.shareable_token,
            )
            for r in reports
        ]
    )


@router.post("", response_model=ReportDetailResponse)
async def create_report(
    request: ReportCreateRequest,
    company: CurrentCompany = None,
    user: CurrentUser = None,
    db: DbSession = None,
):
    """Create a new report (draft) for the reporting year. Triggers recompute and summary refresh."""
    from app.services.emissions import compute_estimates_for_company

    # Ensure estimates and summaries are up to date
    await compute_estimates_for_company(db, company.id, replace_existing=True)
    await refresh_emissions_summaries(db, company.id, request.reporting_year)
    await db.flush()

    # Get annual totals
    annual_totals = await get_annual_totals_by_scope(db, company.id, request.reporting_year)
    total_co2e = sum(row[2] for row in annual_totals)  # row[2] is total_kg_co2e

    # Build content snapshot
    scope_1_total = sum(row[2] for row in annual_totals if row[0] == 1)
    scope_2_total = sum(row[2] for row in annual_totals if row[0] == 2)
    scope_3_total = sum(row[2] for row in annual_totals if row[0] == 3)
    scope_3_breakdown = {}
    for row in annual_totals:
        if row[0] == 3 and row[1]:  # scope 3 with category
            scope_3_breakdown[row[1]] = scope_3_breakdown.get(row[1], Decimal("0")) + row[2]

    # Monthly breakdown
    monthly_rows = await get_monthly_breakdown_by_scope(db, company.id, request.reporting_year)
    monthly_breakdown = []
    monthly_by_month: dict[str, dict[int, Decimal]] = {}
    for period_value, scope, scope_3_cat, total in monthly_rows:
        if period_value not in monthly_by_month:
            monthly_by_month[period_value] = {1: Decimal("0"), 2: Decimal("0"), 3: Decimal("0")}
        monthly_by_month[period_value][scope] += total

    for month in sorted(monthly_by_month.keys()):
        monthly_breakdown.append({
            "month": month,
            "scope_1": float(monthly_by_month[month].get(1, Decimal("0"))),
            "scope_2": float(monthly_by_month[month].get(2, Decimal("0"))),
            "scope_3": float(monthly_by_month[month].get(3, Decimal("0"))),
            "total": float(sum(monthly_by_month[month].values())),
        })

    # Generate executive summary
    executive_summary = f"""
This carbon disclosure report presents {company.name}'s greenhouse gas (GHG) emissions for {request.reporting_year}.
Total annual emissions: {total_co2e:.2f} kg CO₂e ({total_co2e / 1000:.2f} tCO₂e).

Scope 1 (direct emissions): {scope_1_total:.2f} kg CO₂e
Scope 2 (indirect emissions from purchased energy): {scope_2_total:.2f} kg CO₂e
Scope 3 (other indirect emissions): {scope_3_total:.2f} kg CO₂e

This report follows the GHG Protocol Corporate Standard and is suitable for enterprise procurement and vendor onboarding processes.
"""

    content_snapshot = {
        "executive_summary": executive_summary.strip(),
        "scope_1_kg_co2e": float(scope_1_total),
        "scope_2_kg_co2e": float(scope_2_total),
        "scope_3_kg_co2e": float(scope_3_total),
        "scope_3_breakdown": {k: float(v) for k, v in scope_3_breakdown.items()},
        "methodology_notes": "Emissions calculated using activity data multiplied by emission factors. Activity data sources include connected cloud providers, AI-estimated values, and manual entries. Each estimate tracks data quality (measured/estimated/manual), assumptions, and confidence scores.",
        "assumptions_limitations": "Emission factors are sourced from recognized databases (EPA, DEFRA, provider-specific factors). Scope 3 coverage is limited to cloud services, travel, remote work, commuting, and purchased services. Some estimates may be based on industry benchmarks.",
        "emission_factor_citations": [
            {"source": "EPA", "url_or_ref": "EPA Emission Factors Hub"},
            {"source": "DEFRA", "url_or_ref": "UK Government Conversion Factors"},
            {"source": "Cloud Providers", "url_or_ref": "AWS/GCP/Azure sustainability reports"},
        ],
        "monthly_breakdown": monthly_breakdown,
    }

    report = Report(
        company_id=company.id,
        created_by_user_id=user.id,
        title=request.title,
        company_name_snapshot=company.name,
        reporting_year=request.reporting_year,
        total_kg_co2e=total_co2e,
        status="draft",
        shareable_token=None,  # Generated on publish
        content_snapshot=content_snapshot,
        generated_at=datetime.now(),
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return ReportDetailResponse(
        id=str(report.id),
        title=report.title,
        company_name_snapshot=report.company_name_snapshot,
        reporting_year=report.reporting_year,
        total_kg_co2e=report.total_kg_co2e,
        status=report.status,
        shareable_token=report.shareable_token,
        content_snapshot=report.content_snapshot,
        created_at=report.created_at,
        generated_at=report.generated_at,
        published_at=report.published_at,
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: str,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """Get report detail."""
    result = await db.execute(
        select(Report).where(Report.id == UUID(report_id), Report.company_id == company.id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    return ReportDetailResponse(
        id=str(report.id),
        title=report.title,
        company_name_snapshot=report.company_name_snapshot,
        reporting_year=report.reporting_year,
        total_kg_co2e=report.total_kg_co2e,
        status=report.status,
        shareable_token=report.shareable_token,
        content_snapshot=report.content_snapshot,
        created_at=report.created_at,
        generated_at=report.generated_at,
        published_at=report.published_at,
    )


@router.post("/{report_id}/publish")
async def publish_report(
    report_id: str,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """Publish a report and generate a shareable token."""
    result = await db.execute(
        select(Report).where(Report.id == UUID(report_id), Report.company_id == company.id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if report.status == "published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report already published")

    report.status = "published"
    report.shareable_token = secrets.token_urlsafe(32)
    report.published_at = datetime.now()
    await db.commit()

    return {"status": "published", "shareable_token": report.shareable_token}


@router.get("/{report_id}/pdf")
async def get_report_pdf(
    report_id: str,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """Generate and return PDF of the report."""
    result = await db.execute(
        select(Report).where(Report.id == UUID(report_id), Report.company_id == company.id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    content = report.content_snapshot or {}
    pdf_bytes = render_report_pdf(
        company_name=report.company_name_snapshot or company.name,
        reporting_year=report.reporting_year,
        total_kg_co2e=float(report.total_kg_co2e),
        scope_1_kg=content.get("scope_1_kg_co2e", 0),
        scope_2_kg=content.get("scope_2_kg_co2e", 0),
        scope_3_kg=content.get("scope_3_kg_co2e", 0),
        scope_3_breakdown=content.get("scope_3_breakdown") or {},
        executive_summary=content.get("executive_summary", ""),
        methodology_notes=content.get("methodology_notes", ""),
        assumptions_limitations=content.get("assumptions_limitations", ""),
        emission_factor_citations=content.get("emission_factor_citations") or [],
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="carbonly-report-{report.reporting_year}.pdf"'
        },
    )


@router.get("/r/{share_token}")
async def get_public_report(
    share_token: str,
    db: DbSession = None,
):
    """Public share link (read-only report summary)."""
    result = await db.execute(
        select(Report).where(Report.shareable_token == share_token, Report.status == "published")
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    content = report.content_snapshot or {}
    scope_3_breakdown = content.get("scope_3_breakdown", {})

    return {
        "company_name": report.company_name_snapshot or "Unknown",
        "reporting_year": report.reporting_year,
        "total_co2e": float(report.total_kg_co2e),
        "executive_summary": content.get("executive_summary", ""),
        "scope_breakdown": {
            "scope_1": content.get("scope_1_kg_co2e", 0),
            "scope_2": content.get("scope_2_kg_co2e", 0),
            "scope_3": content.get("scope_3_kg_co2e", 0),
        },
        "scope_3_breakdown": scope_3_breakdown,
    }
