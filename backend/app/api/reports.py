"""Reports API endpoints."""
import secrets
from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentCompany, CurrentUser, DbSession, NonDemoUser, PaidCompany
from app.models.report import Report
from app.schemas.reports import (
    ReportCreateRequest,
    ReportDetailResponse,
    ReportListItem,
    ReportsListResponse,
)
from app.services.emissions import refresh_emissions_summaries
from app.services.report_service import build_report_snapshot
from app.services.pdf_report import render_report_pdf
from app.services.idempotency import (
    get_idempotency_record,
    payload_hash,
    store_idempotency_record,
)
from app.services.audit import log_audit_action
from app.models.base import utc_now

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("", response_model=ReportsListResponse)
async def list_reports(
    year: Annotated[int | None, Query(description="Filter by reporting year")] = None,
    company: PaidCompany = None,
    db: DbSession = None,
):
    """List all reports for the company."""
    q = select(Report).where(
        Report.company_id == company.id,
        Report.deleted_at.is_(None),
    )
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
    company: PaidCompany = None,
    user: NonDemoUser = None,
    db: DbSession = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    """Create a new report (draft) for the reporting year. Triggers recompute and summary refresh."""
    from app.services.emissions import compute_estimates_for_company

    endpoint = "POST /api/reports"
    if idempotency_key:
        existing = await get_idempotency_record(
            db, company_id=company.id, endpoint=endpoint, key=idempotency_key
        )
        if existing:
            expected_hash = payload_hash(request)
            if existing.request_hash and expected_hash and existing.request_hash != expected_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with different payload.",
                )
            return JSONResponse(content=existing.response_body, status_code=existing.response_status)

    # Ensure estimates and summaries are up to date
    await compute_estimates_for_company(db, company.id, replace_existing=True)
    await refresh_emissions_summaries(db, company.id, request.reporting_year)
    await db.flush()

    content_snapshot_raw, total_co2e = await build_report_snapshot(
        db, company_name=company.name, company_id=company.id, reporting_year=request.reporting_year
    )
    content_snapshot = jsonable_encoder(content_snapshot_raw)

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
    await log_audit_action(
        db,
        user_id=user.id,
        company_id=company.id,
        action="report_created",
        entity_type="report",
        entity_id=report.id,
    )
    await db.commit()
    await db.refresh(report)

    response_payload = ReportDetailResponse(
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
    if idempotency_key:
        await store_idempotency_record(
            db,
            company_id=company.id,
            user_id=user.id,
            endpoint=endpoint,
            key=idempotency_key,
            request_payload=request,
            response_body=jsonable_encoder(response_payload),
            response_status=status.HTTP_200_OK,
        )
        await db.commit()

    return response_payload


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: str,
    company: PaidCompany = None,
    db: DbSession = None,
):
    """Get report detail."""
    result = await db.execute(
        select(Report).where(
            Report.id == UUID(report_id),
            Report.company_id == company.id,
            Report.deleted_at.is_(None),
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.status != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft reports can be deleted",
        )

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
    company: PaidCompany = None,
    user: NonDemoUser = None,
    db: DbSession = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    """Publish a report and generate a shareable token."""
    endpoint = f"POST /api/reports/{report_id}/publish"
    if idempotency_key:
        existing = await get_idempotency_record(
            db, company_id=company.id, endpoint=endpoint, key=idempotency_key
        )
        if existing:
            return JSONResponse(content=existing.response_body, status_code=existing.response_status)

    result = await db.execute(
        select(Report).where(
            Report.id == UUID(report_id),
            Report.company_id == company.id,
            Report.deleted_at.is_(None),
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if report.status == "published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Report already published")

    report.status = "published"
    report.shareable_token = secrets.token_urlsafe(32)
    report.published_at = datetime.now()
    await log_audit_action(
        db,
        user_id=user.id,
        company_id=company.id,
        action="report_published",
        entity_type="report",
        entity_id=report.id,
    )
    await db.commit()

    response_payload = {"status": "published", "shareable_token": report.shareable_token}
    if idempotency_key:
        await store_idempotency_record(
            db,
            company_id=company.id,
            user_id=user.id,
            endpoint=endpoint,
            key=idempotency_key,
            request_payload={"report_id": report_id},
            response_body=response_payload,
            response_status=status.HTTP_200_OK,
        )
        await db.commit()

    return response_payload


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    company: PaidCompany = None,
    user: NonDemoUser = None,
    db: DbSession = None,
):
    """Soft delete a report."""
    result = await db.execute(
        select(Report).where(
            Report.id == UUID(report_id),
            Report.company_id == company.id,
            Report.deleted_at.is_(None),
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report.deleted_at = utc_now()
    await log_audit_action(
        db,
        user_id=user.id,
        company_id=company.id,
        action="report_deleted",
        entity_type="report",
        entity_id=report.id,
    )
    await db.commit()
    return {"status": "deleted"}


@router.get("/{report_id}/pdf")
async def get_report_pdf(
    report_id: str,
    company: PaidCompany = None,
    db: DbSession = None,
):
    """Generate and return PDF of the report."""
    result = await db.execute(
        select(Report).where(
            Report.id == UUID(report_id),
            Report.company_id == company.id,
            Report.deleted_at.is_(None),
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    content = report.content_snapshot or {}
    pdf_bytes = render_report_pdf(
        company_name=report.company_name_snapshot or company.name,
        reporting_year=report.reporting_year,
        total_kg_co2e=Decimal(report.total_kg_co2e),
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
            "Content-Disposition": f'attachment; filename="carbonly-report-{report.reporting_year}.pdf"',
            "Cache-Control": "private, max-age=60",
        },
    )


@router.get("/r/{share_token}")
async def get_public_report(
    share_token: str,
    db: DbSession = None,
):
    """Public share link (read-only report summary)."""
    result = await db.execute(
        select(Report).where(
            Report.shareable_token == share_token,
            Report.status == "published",
            Report.deleted_at.is_(None),
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    content = report.content_snapshot or {}
    scope_3_breakdown = content.get("scope_3_breakdown", {})

    return {
        "company_name": report.company_name_snapshot or "Unknown",
        "reporting_year": report.reporting_year,
        "total_co2e": report.total_kg_co2e,
        "executive_summary": content.get("executive_summary", ""),
        "scope_breakdown": {
            "scope_1": content.get("scope_1_kg_co2e", 0),
            "scope_2": content.get("scope_2_kg_co2e", 0),
            "scope_3": content.get("scope_3_kg_co2e", 0),
        },
        "scope_3_breakdown": scope_3_breakdown,
    }
