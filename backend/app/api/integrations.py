"""Integrations API endpoints."""
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentCompany, CurrentUser, DbSession
from app.models.activity_record import ActivityRecord
from app.models.data_source_connection import DataSourceConnection
from app.schemas.integrations import (
    CsvUploadResponse,
    IntegrationResponse,
    IntegrationsListResponse,
    ManualActivityRequest,
)
from app.services.csv_parser import parse_csv_activities
from app.services.emissions import compute_estimates_for_company, refresh_emissions_summaries

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("", response_model=IntegrationsListResponse)
async def list_integrations(
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """List all data source connections for the company."""
    result = await db.execute(
        select(DataSourceConnection).where(DataSourceConnection.company_id == company.id)
    )
    connections = result.scalars().all()

    # Ensure default cloud providers exist
    cloud_providers = {"aws": "AWS", "gcp": "GCP", "azure": "Azure"}
    existing_types = {c.source_type for c in connections}
    for source_type, display_name in cloud_providers.items():
        if source_type not in existing_types:
            conn = DataSourceConnection(
                id=uuid4(),
                company_id=company.id,
                source_type=source_type,
                display_name=display_name,
                status="not_connected",
            )
            db.add(conn)
            connections.append(conn)
    await db.flush()

    return IntegrationsListResponse(
        integrations=[
            IntegrationResponse(
                id=str(c.id),
                source_type=c.source_type,
                display_name=c.display_name,
                status=c.status,
                last_synced_at=c.last_synced_at,
            )
            for c in connections
        ]
    )


@router.post("/{provider}/sync")
async def sync_integration(
    provider: str,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """
    Sync data from a provider (AWS, GCP, Azure).
    For now, generates mock ActivityRecords, then recomputes estimates and summaries.
    """
    result = await db.execute(
        select(DataSourceConnection).where(
            DataSourceConnection.company_id == company.id,
            DataSourceConnection.source_type == provider,
        )
    )
    conn = result.scalar_one_or_none()
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    # Allow sync to set status to connected (for mock flow: user "connects" by syncing)
    if conn.status != "connected":
        conn.status = "connected"
        await db.flush()

    # Mock: create sample cloud usage activity records
    # In production, this would call provider APIs
    year = company.reporting_year
    period_start = date(year, 1, 1)
    period_end = date(year, 12, 31)

    # Mock cloud usage (e.g., compute hours, storage GB-months)
    mock_activities = [
        ActivityRecord(
            id=uuid4(),
            company_id=company.id,
            data_source_connection_id=conn.id,
            scope=3,
            scope_3_category="cloud",
            activity_type="cloud_compute_hours",
            quantity=Decimal("10000.0"),
            unit="hours",
            period_start=period_start,
            period_end=period_end,
            data_quality="measured",
            assumptions="Mock data from provider API",
            confidence_score=Decimal("95.0"),
        ),
        ActivityRecord(
            id=uuid4(),
            company_id=company.id,
            data_source_connection_id=conn.id,
            scope=3,
            scope_3_category="cloud",
            activity_type="cloud_storage_gb_months",
            quantity=Decimal("5000.0"),
            unit="GB-months",
            period_start=period_start,
            period_end=period_end,
            data_quality="measured",
            assumptions="Mock data from provider API",
            confidence_score=Decimal("95.0"),
        ),
    ]
    for activity in mock_activities:
        db.add(activity)
    await db.flush()

    # Update connection last_synced_at
    conn.last_synced_at = datetime.now()
    await db.flush()

    # Recompute emissions
    await compute_estimates_for_company(db, company.id, period_start, period_end, replace_existing=False)
    await refresh_emissions_summaries(db, company.id, year)
    await db.commit()

    return {"status": "synced", "activities_created": len(mock_activities)}


@router.post("/{provider}/estimate")
async def estimate_integration(
    provider: str,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """
    Set provider to AI estimated and create estimated ActivityRecords.
    """
    result = await db.execute(
        select(DataSourceConnection).where(
            DataSourceConnection.company_id == company.id,
            DataSourceConnection.source_type == provider,
        )
    )
    conn = result.scalar_one_or_none()
    if conn is None:
        # Create if doesn't exist
        display_names = {"aws": "AWS", "gcp": "GCP", "azure": "Azure"}
        conn = DataSourceConnection(
            id=uuid4(),
            company_id=company.id,
            source_type=provider,
            display_name=display_names.get(provider, provider.upper()),
            status="ai_estimated",
        )
        db.add(conn)
        await db.flush()

    conn.status = "ai_estimated"
    await db.flush()

    # Create estimated activity records
    year = company.reporting_year
    period_start = date(year, 1, 1)
    period_end = date(year, 12, 31)

    estimated_activity = ActivityRecord(
        id=uuid4(),
        company_id=company.id,
        data_source_connection_id=conn.id,
        scope=3,
        scope_3_category="cloud",
        activity_type="cloud_compute_hours",
        quantity=Decimal("8000.0"),  # Estimated
        unit="hours",
        period_start=period_start,
        period_end=period_end,
        data_quality="estimated",
        assumptions="AI estimated based on company size and industry benchmarks",
        confidence_score=Decimal("70.0"),
    )
    db.add(estimated_activity)
    await db.flush()

    # Recompute emissions
    await compute_estimates_for_company(db, company.id, period_start, period_end, replace_existing=False)
    await refresh_emissions_summaries(db, company.id, year)
    await db.commit()

    return {"status": "estimated", "activity_created": True}


@router.post("/manual/activity")
async def create_manual_activity(
    request: ManualActivityRequest,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """Create a manual activity record."""
    activity = ActivityRecord(
        id=uuid4(),
        company_id=company.id,
        data_source_connection_id=None,  # Manual entry
        scope=request.scope,
        scope_3_category=request.scope_3_category,
        activity_type=request.activity_type,
        quantity=Decimal(str(request.quantity)),
        unit=request.unit,
        period_start=date.fromisoformat(request.period_start),
        period_end=date.fromisoformat(request.period_end),
        data_quality=request.data_quality,
        assumptions=request.assumptions,
        confidence_score=Decimal(str(request.confidence_score)) if request.confidence_score else None,
    )
    db.add(activity)
    await db.flush()

    # Recompute emissions
    await compute_estimates_for_company(db, company.id, replace_existing=False)
    await refresh_emissions_summaries(db, company.id, company.reporting_year)
    await db.commit()

    return {"id": str(activity.id), "status": "created"}


@router.post("/manual/upload", response_model=CsvUploadResponse)
async def upload_manual_csv(
    file: UploadFile = File(..., description="CSV file with columns: scope, activity_type, quantity, unit, period_start, period_end"),
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """
    Upload CSV file to create multiple activity records.
    Expected columns: scope, activity_type, quantity, unit, period_start, period_end.
    Optional: scope_3_category, data_quality, assumptions, confidence_score.
    """
    content = await file.read()
    valid_rows, errors = parse_csv_activities(content)

    inserted = 0
    for row in valid_rows:
        activity = ActivityRecord(
            id=uuid4(),
            company_id=company.id,
            data_source_connection_id=None,
            scope=row["scope"],
            scope_3_category=row.get("scope_3_category"),
            activity_type=row["activity_type"],
            quantity=Decimal(str(row["quantity"])),
            unit=row["unit"],
            period_start=date.fromisoformat(row["period_start"]),
            period_end=date.fromisoformat(row["period_end"]),
            data_quality=row.get("data_quality") or "manual",
            assumptions=row.get("assumptions"),
            confidence_score=Decimal(str(row["confidence_score"])) if row.get("confidence_score") is not None else None,
        )
        db.add(activity)
        inserted += 1

    if inserted > 0:
        await db.flush()
        await compute_estimates_for_company(db, company.id, replace_existing=False)
        await refresh_emissions_summaries(db, company.id, company.reporting_year)
    await db.commit()

    return CsvUploadResponse(inserted=inserted, errors=errors)
