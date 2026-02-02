"""
Emissions calculation service (core engine).

Formula: Emissions = Activity data × Emission factor

Supports Scope 1, Scope 2, and limited Scope 3 (cloud, commuting, travel, remote_work, purchased_services).
Every value tracks: measured vs estimated vs manual, assumptions, confidence score.
"""
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_record import ActivityRecord
from app.models.emission_factor import EmissionFactor
from app.models.emission_estimate import EmissionEstimate
from app.models.emissions_summary import EmissionsSummary


# Scope 3 categories supported by the engine
SCOPE_3_CATEGORIES = (
    "cloud",
    "travel",
    "remote_work",
    "commuting",
    "purchased_services",
)

DATA_QUALITY_MEASURED = "measured"
DATA_QUALITY_ESTIMATED = "estimated"
DATA_QUALITY_MANUAL = "manual"


async def get_matching_factor(
    session: AsyncSession,
    activity_type: str,
    unit: str,
    scope: int,
    scope_3_category: str | None,
    period_start: date,
    period_end: date,
) -> EmissionFactor | None:
    """
    Find an emission factor that matches the activity (activity_type, unit, scope, scope_3_category)
    and is valid for the period. Prefer most recent validity.
    """
    conditions = [
        EmissionFactor.activity_type == activity_type,
        EmissionFactor.unit == unit,
        EmissionFactor.scope == scope,
        (EmissionFactor.valid_from.is_(None)) | (EmissionFactor.valid_from <= period_end),
        (EmissionFactor.valid_to.is_(None)) | (EmissionFactor.valid_to >= period_start),
    ]
    if scope == 3:
        if scope_3_category:
            conditions.append(EmissionFactor.scope_3_category == scope_3_category)
        else:
            conditions.append(EmissionFactor.scope_3_category.is_(None))
    else:
        conditions.append(EmissionFactor.scope_3_category.is_(None))

    q = (
        select(EmissionFactor)
        .where(and_(*conditions))
        .order_by(
            EmissionFactor.valid_to.desc().nullslast(),
            EmissionFactor.valid_from.desc().nullslast(),
        )
        .limit(1)
    )
    result = await session.execute(q)
    return result.scalar_one_or_none()


async def compute_estimate_for_activity(
    session: AsyncSession,
    record: ActivityRecord,
) -> EmissionEstimate | None:
    """
    For one activity record: find a matching emission factor, compute
    emissions_kg_co2e = quantity × factor_value, and create an EmissionEstimate.
    Returns the new estimate or None if no matching factor.
    """
    factor = await get_matching_factor(
        session,
        activity_type=record.activity_type,
        unit=record.unit,
        scope=record.scope,
        scope_3_category=record.scope_3_category,
        period_start=record.period_start,
        period_end=record.period_end,
    )
    if factor is None:
        return None

    emissions_kg_co2e = (record.quantity * factor.factor_value).quantize(Decimal("0.000001"))

    estimate = EmissionEstimate(
        company_id=record.company_id,
        activity_record_id=record.id,
        emission_factor_id=factor.id,
        scope=record.scope,
        scope_3_category=record.scope_3_category,
        activity_quantity=record.quantity,
        factor_value=factor.factor_value,
        emissions_kg_co2e=emissions_kg_co2e,
        data_quality=record.data_quality,
        assumptions=record.assumptions,
        confidence_score=record.confidence_score,
        period_start=record.period_start,
        period_end=record.period_end,
    )
    session.add(estimate)
    await session.flush()
    return estimate


async def ensure_estimates_for_activity(
    session: AsyncSession,
    record: ActivityRecord,
    replace_existing: bool = False,
) -> EmissionEstimate | None:
    """
    Ensure there is exactly one EmissionEstimate for this activity record.
    If replace_existing is True, delete existing estimates for this record first.
    """
    if replace_existing:
        await session.execute(
            delete(EmissionEstimate).where(EmissionEstimate.activity_record_id == record.id)
        )
        await session.flush()
    else:
        existing = await session.execute(
            select(EmissionEstimate).where(EmissionEstimate.activity_record_id == record.id).limit(1)
        )
        if existing.scalar_one_or_none() is not None:
            return None

    return await compute_estimate_for_activity(session, record)


async def compute_estimates_for_company(
    session: AsyncSession,
    company_id: UUID,
    period_start: date | None = None,
    period_end: date | None = None,
    replace_existing: bool = False,
) -> int:
    """
    For all activity records of a company (optionally filtered by period),
    ensure each has an emission estimate. Returns count of new estimates created.
    """
    q = select(ActivityRecord).where(ActivityRecord.company_id == company_id)
    if period_start is not None:
        q = q.where(ActivityRecord.period_end >= period_start)
    if period_end is not None:
        q = q.where(ActivityRecord.period_start <= period_end)
    result = await session.execute(q)
    records = result.scalars().all()
    count = 0
    for record in records:
        if replace_existing:
            await session.execute(
                delete(EmissionEstimate).where(EmissionEstimate.activity_record_id == record.id)
            )
        else:
            existing = await session.execute(
                select(EmissionEstimate).where(EmissionEstimate.activity_record_id == record.id).limit(1)
            )
            if existing.scalar_one_or_none() is not None:
                continue
        est = await compute_estimate_for_activity(session, record)
        if est is not None:
            count += 1
    await session.flush()
    return count


def _period_value(period_start: date, period_type: str) -> str:
    if period_type == "monthly":
        return period_start.strftime("%Y-%m")
    return str(period_start.year)


async def refresh_emissions_summaries(
    session: AsyncSession,
    company_id: UUID,
    reporting_year: int,
) -> int:
    """
    Rebuild emissions_summaries for the company and year from emission_estimates.
    Creates/updates rows for annual and monthly period_type, by scope and scope_3_category.
    Returns number of summary rows upserted.
    """
    # Delete existing summaries for this company and year
    await session.execute(
        delete(EmissionsSummary).where(
            and_(
                EmissionsSummary.company_id == company_id,
                EmissionsSummary.reporting_year == reporting_year,
            )
        )
    )
    await session.flush()

    # Get all estimates for company in this year
    q = select(EmissionEstimate).where(
        and_(
            EmissionEstimate.company_id == company_id,
            EmissionEstimate.period_start >= date(reporting_year, 1, 1),
            EmissionEstimate.period_end <= date(reporting_year, 12, 31),
        )
    )
    result = await session.execute(q)
    estimates = result.scalars().all()

    # Group by (period_type, period_value, scope, scope_3_category)
    buckets: dict[tuple[str, str, int, str | None], list[EmissionEstimate]] = {}
    for est in estimates:
        key_annual = ("annual", str(reporting_year), est.scope, est.scope_3_category)
        buckets.setdefault(key_annual, []).append(est)
        month_val = est.period_start.strftime("%Y-%m")
        key_monthly = ("monthly", month_val, est.scope, est.scope_3_category)
        buckets.setdefault(key_monthly, []).append(est)

    count = 0
    for (period_type, period_value, scope, scope_3_cat), group in buckets.items():
        total = sum(e.emissions_kg_co2e for e in group)
        measured = sum(e.emissions_kg_co2e for e in group if e.data_quality == DATA_QUALITY_MEASURED)
        estimated = sum(e.emissions_kg_co2e for e in group if e.data_quality == DATA_QUALITY_ESTIMATED)
        manual = sum(e.emissions_kg_co2e for e in group if e.data_quality == DATA_QUALITY_MANUAL)
        conf_scores = [e.confidence_score for e in group if e.confidence_score is not None]
        conf_avg = (sum(conf_scores) / len(conf_scores)).quantize(Decimal("0.01")) if conf_scores else None

        summary = EmissionsSummary(
            company_id=company_id,
            reporting_year=reporting_year,
            period_type=period_type,
            period_value=period_value,
            scope=scope,
            scope_3_category=scope_3_cat,
            total_kg_co2e=total,
            measured_kg_co2e=measured,
            estimated_kg_co2e=estimated,
            manual_kg_co2e=manual,
            confidence_score_avg=conf_avg,
        )
        session.add(summary)
        count += 1
    await session.flush()
    return count


async def get_annual_totals_by_scope(
    session: AsyncSession,
    company_id: UUID,
    reporting_year: int,
) -> list[tuple[int, str | None, Decimal, Decimal, Decimal, Decimal, Decimal | None]]:
    """
    Return emissions_summaries for annual period_type: (scope, scope_3_category, total, measured, estimated, manual, confidence_avg).
    """
    q = (
        select(
            EmissionsSummary.scope,
            EmissionsSummary.scope_3_category,
            EmissionsSummary.total_kg_co2e,
            EmissionsSummary.measured_kg_co2e,
            EmissionsSummary.estimated_kg_co2e,
            EmissionsSummary.manual_kg_co2e,
            EmissionsSummary.confidence_score_avg,
        )
        .where(
            and_(
                EmissionsSummary.company_id == company_id,
                EmissionsSummary.reporting_year == reporting_year,
                EmissionsSummary.period_type == "annual",
            )
        )
    )
    result = await session.execute(q)
    return list(result.all())


async def get_monthly_breakdown_by_scope(
    session: AsyncSession,
    company_id: UUID,
    reporting_year: int,
) -> list[tuple[str, int, str | None, Decimal]]:
    """
    Return monthly emissions: (period_value e.g. 2024-01, scope, scope_3_category, total_kg_co2e).
    """
    q = (
        select(
            EmissionsSummary.period_value,
            EmissionsSummary.scope,
            EmissionsSummary.scope_3_category,
            EmissionsSummary.total_kg_co2e,
        )
        .where(
            and_(
                EmissionsSummary.company_id == company_id,
                EmissionsSummary.reporting_year == reporting_year,
                EmissionsSummary.period_type == "monthly",
            )
        )
        .order_by(EmissionsSummary.period_value, EmissionsSummary.scope)
    )
    result = await session.execute(q)
    return list(result.all())
