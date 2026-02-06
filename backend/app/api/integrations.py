"""Integrations API endpoints."""
from datetime import date
from decimal import Decimal
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentCompany, CurrentUser, DbSession, NonDemoUser
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
from app.services.integration_service import (
    create_estimated_activity,
    create_mock_cloud_activities,
    ensure_connection,
    get_connection,
    has_mock_activities,
)
from app.services.idempotency import (
    get_idempotency_record,
    payload_hash,
    store_idempotency_record,
)
from app.services.audit import log_audit_action

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
    user: NonDemoUser = None,
    db: DbSession = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    """
    Sync data from a provider (AWS, GCP, Azure).
    For now, generates mock ActivityRecords, then recomputes estimates and summaries.
    """
    endpoint = f"POST /api/integrations/{provider}/sync"
    if idempotency_key:
        existing = await get_idempotency_record(
            db, company_id=company.id, endpoint=endpoint, key=idempotency_key
        )
        if existing:
            expected_hash = payload_hash({"provider": provider})
            if existing.request_hash and expected_hash and existing.request_hash != expected_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with different payload.",
                )
            return JSONResponse(content=existing.response_body, status_code=existing.response_status)

    conn = await get_connection(db, company_id=company.id, provider=provider)
    if conn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")

    # Allow sync to set status to connected (for mock flow: user "connects" by syncing)
    if conn.status != "connected":
        conn.status = "connected"
        await db.flush()

    year = company.reporting_year
    activities_created = 0
    if not await has_mock_activities(db, company_id=company.id, connection_id=conn.id, year=year):
        created = await create_mock_cloud_activities(
            db, company_id=company.id, connection=conn, year=year
        )
        activities_created = len(created)

    # Recompute emissions
    await compute_estimates_for_company(
        db, company.id, date(year, 1, 1), date(year, 12, 31), replace_existing=False
    )
    await refresh_emissions_summaries(db, company.id, year)
    await log_audit_action(
        db,
        user_id=user.id,
        company_id=company.id,
        action="integration_synced",
        entity_type="data_source_connection",
        entity_id=conn.id,
    )
    await db.commit()

    response_payload = {"status": "synced", "activities_created": activities_created}
    if idempotency_key:
        await store_idempotency_record(
            db,
            company_id=company.id,
            user_id=user.id,
            endpoint=endpoint,
            key=idempotency_key,
            request_payload={"provider": provider},
            response_body=response_payload,
            response_status=status.HTTP_200_OK,
        )
        await db.commit()

    return response_payload


@router.post("/{provider}/estimate")
async def estimate_integration(
    provider: str,
    company: CurrentCompany = None,
    user: NonDemoUser = None,
    db: DbSession = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    """
    Set provider to AI estimated and create estimated ActivityRecords.
    """
    endpoint = f"POST /api/integrations/{provider}/estimate"
    if idempotency_key:
        existing = await get_idempotency_record(
            db, company_id=company.id, endpoint=endpoint, key=idempotency_key
        )
        if existing:
            return JSONResponse(content=existing.response_body, status_code=existing.response_status)

    conn = await ensure_connection(
        db, company_id=company.id, provider=provider, status="ai_estimated"
    )

    conn.status = "ai_estimated"
    await db.flush()

    year = company.reporting_year
    await create_estimated_activity(db, company_id=company.id, connection=conn, year=year)

    # Recompute emissions
    await compute_estimates_for_company(
        db, company.id, date(year, 1, 1), date(year, 12, 31), replace_existing=False
    )
    await refresh_emissions_summaries(db, company.id, year)
    await log_audit_action(
        db,
        user_id=user.id,
        company_id=company.id,
        action="integration_estimated",
        entity_type="data_source_connection",
        entity_id=conn.id,
    )
    await db.commit()

    response_payload = {"status": "estimated", "activity_created": True}
    if idempotency_key:
        await store_idempotency_record(
            db,
            company_id=company.id,
            user_id=user.id,
            endpoint=endpoint,
            key=idempotency_key,
            request_payload={"provider": provider},
            response_body=response_payload,
            response_status=status.HTTP_200_OK,
        )
        await db.commit()

    return response_payload


@router.post("/manual/activity")
async def create_manual_activity(
    request: ManualActivityRequest,
    company: CurrentCompany = None,
    user: NonDemoUser = None,
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
    await log_audit_action(
        db,
        user_id=user.id,
        company_id=company.id,
        action="manual_activity_created",
        entity_type="activity_record",
        entity_id=activity.id,
    )
    await db.commit()

    return {"id": str(activity.id), "status": "created"}


@router.post("/manual/upload", response_model=CsvUploadResponse)
async def upload_manual_csv(
    file: UploadFile = File(..., description="CSV file with columns: scope, activity_type, quantity, unit, period_start, period_end"),
    company: CurrentCompany = None,
    user: NonDemoUser = None,
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
        await log_audit_action(
            db,
            user_id=user.id,
            company_id=company.id,
            action="manual_csv_uploaded",
            entity_type="activity_record",
            entity_id=None,
        )
    await db.commit()

    return CsvUploadResponse(inserted=inserted, errors=errors)
