"""Dashboard API endpoints."""
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import CurrentCompany, CurrentUser, DbSession, NonDemoUser
from app.models.activity_record import ActivityRecord
from app.models.data_source_connection import DataSourceConnection
from app.schemas.dashboard import (
    DashboardResponse,
    DataQualityStats,
    MonthlyTrendPoint,
    Scope3CategoryTotal,
    ScopeTotal,
)
from app.services.emissions import (
    DATA_QUALITY_ESTIMATED,
    DATA_QUALITY_MANUAL,
    DATA_QUALITY_MEASURED,
    get_annual_totals_by_scope,
    get_monthly_breakdown_by_scope,
)
from app.services.idempotency import (
    get_idempotency_record,
    payload_hash,
    store_idempotency_record,
)
from app.services.audit import log_audit_action

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    year: Annotated[int, Query(description="Reporting year")] = 2025,
    company: CurrentCompany = None,
    db: DbSession = None,
):
    """Get dashboard data: company stats, annual totals, data quality, monthly trend, scope 3 breakdown."""
    # Company stats
    cloud_providers = await db.execute(
        select(func.count(DataSourceConnection.id)).where(
            DataSourceConnection.company_id == company.id,
            DataSourceConnection.source_type.in_(["aws", "gcp", "azure"]),
        )
    )
    cloud_providers_count = cloud_providers.scalar() or 0

    company_stats = {
        "employees": company.employee_count or 0,
        "cloud_providers_count": cloud_providers_count,
        "reporting_year": year,
    }

    # Annual totals by scope
    annual_totals_rows = await get_annual_totals_by_scope(db, company.id, year)
    total_co2e = Decimal("0")
    scope_1_total = Decimal("0")
    scope_2_total = Decimal("0")
    scope_3_total = Decimal("0")
    scope_totals: list[ScopeTotal] = []
    scope3_by_category: dict[str, Decimal] = {}

    for scope, scope_3_cat, total, measured, estimated, manual, conf_avg in annual_totals_rows:
        total_co2e += total
        if scope == 1:
            scope_1_total += total
        elif scope == 2:
            scope_2_total += total
        elif scope == 3:
            scope_3_total += total
            if scope_3_cat:
                scope3_by_category[scope_3_cat] = scope3_by_category.get(scope_3_cat, Decimal("0")) + total

        scope_totals.append(
            ScopeTotal(
                scope=scope,
                scope_3_category=scope_3_cat,
                total_kg_co2e=total,
                measured_kg_co2e=measured,
                estimated_kg_co2e=estimated,
                manual_kg_co2e=manual,
                confidence_score_avg=conf_avg,
            )
        )

    # Data quality stats
    activity_counts = await db.execute(
        select(
            func.count(ActivityRecord.id).filter(ActivityRecord.data_quality == DATA_QUALITY_MEASURED).label("measured"),
            func.count(ActivityRecord.id).filter(ActivityRecord.data_quality == DATA_QUALITY_ESTIMATED).label("estimated"),
            func.count(ActivityRecord.id).filter(ActivityRecord.data_quality == DATA_QUALITY_MANUAL).label("manual"),
        ).where(ActivityRecord.company_id == company.id)
    )
    row = activity_counts.first()
    connected_count = row.measured if row else 0
    ai_estimated_count = row.estimated if row else 0
    manual_count = row.manual if row else 0

    # Overall confidence: average from annual totals
    conf_scores = [s.confidence_score_avg for s in scope_totals if s.confidence_score_avg is not None]
    overall_confidence = (sum(conf_scores) / len(conf_scores)).quantize(Decimal("0.01")) if conf_scores else None

    data_quality = DataQualityStats(
        overall_confidence=overall_confidence,
        connected_sources_count=connected_count,
        ai_estimated_sources_count=ai_estimated_count,
        manual_entries_count=manual_count,
    )
    lineage = {
        "measured_kg_co2e": sum(s.measured_kg_co2e for s in scope_totals),
        "estimated_kg_co2e": sum(s.estimated_kg_co2e for s in scope_totals),
        "manual_kg_co2e": sum(s.manual_kg_co2e for s in scope_totals),
        "measured_count": connected_count,
        "estimated_count": ai_estimated_count,
        "manual_count": manual_count,
    }

    # Monthly trend
    monthly_rows = await get_monthly_breakdown_by_scope(db, company.id, year)
    monthly_by_month: dict[str, dict[int, Decimal]] = {}
    for period_value, scope, scope_3_cat, total in monthly_rows:
        if period_value not in monthly_by_month:
            monthly_by_month[period_value] = {1: Decimal("0"), 2: Decimal("0"), 3: Decimal("0")}
        monthly_by_month[period_value][scope] += total

    monthly_trend = [
        MonthlyTrendPoint(
            month=month,
            scope_1=monthly_by_month[month].get(1, Decimal("0")),
            scope_2=monthly_by_month[month].get(2, Decimal("0")),
            scope_3=monthly_by_month[month].get(3, Decimal("0")),
            total=sum(monthly_by_month[month].values()),
        )
        for month in sorted(monthly_by_month.keys())
    ]

    # Scope 3 category breakdown
    scope3_category_totals = [
        Scope3CategoryTotal(category=cat, total_kg_co2e=total)
        for cat, total in sorted(scope3_by_category.items())
    ]

    # Build annual_totals dict matching schema
    annual_totals_dict = {
        "total_co2e": total_co2e,
        "scope_1": scope_1_total,
        "scope_2": scope_2_total,
        "scope_3": scope_3_total,
        "scope_totals": scope_totals,
        "scope3_by_category": scope3_category_totals,
    }

    return DashboardResponse(
        company_stats=company_stats,
        annual_totals=annual_totals_dict,
        data_quality=data_quality,
        monthly_trend=monthly_trend,
        data_lineage=lineage,
    )


@router.post("/recompute")
async def recompute_emissions(
    year: Annotated[int, Query(description="Reporting year")] = 2025,
    company: CurrentCompany = None,
    user: NonDemoUser = None,
    db: DbSession = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    """Recompute emissions estimates and summaries for the company and year."""
    from app.services.emissions import compute_estimates_for_company, refresh_emissions_summaries

    endpoint = "POST /api/dashboard/recompute"
    if idempotency_key:
        existing = await get_idempotency_record(
            db, company_id=company.id, endpoint=endpoint, key=idempotency_key
        )
        if existing:
            expected_hash = payload_hash({"year": year})
            if existing.request_hash and expected_hash and existing.request_hash != expected_hash:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with different payload.",
                )
            return JSONResponse(content=existing.response_body, status_code=existing.response_status)

    count = await compute_estimates_for_company(db, company.id, replace_existing=True)
    summary_count = await refresh_emissions_summaries(db, company.id, year)
    await log_audit_action(
        db,
        user_id=user.id,
        company_id=company.id,
        action="emissions_recomputed",
        entity_type="company",
        entity_id=company.id,
    )
    await db.commit()

    response_payload = {"estimates_created": count, "summaries_refreshed": summary_count}
    if idempotency_key:
        await store_idempotency_record(
            db,
            company_id=company.id,
            user_id=user.id,
            endpoint=endpoint,
            key=idempotency_key,
            request_payload={"year": year},
            response_body=response_payload,
            response_status=status.HTTP_200_OK,
        )
        await db.commit()

    return response_payload
