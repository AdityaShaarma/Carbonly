"""Integration service logic (mock ingestion, estimates)."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_record import ActivityRecord
from app.models.data_source_connection import DataSourceConnection


async def get_connection(
    session: AsyncSession, *, company_id: UUID, provider: str
) -> DataSourceConnection | None:
    result = await session.execute(
        select(DataSourceConnection).where(
            DataSourceConnection.company_id == company_id,
            DataSourceConnection.source_type == provider,
        )
    )
    return result.scalar_one_or_none()


async def ensure_connection(
    session: AsyncSession, *, company_id: UUID, provider: str, status: str
) -> DataSourceConnection:
    conn = await get_connection(session, company_id=company_id, provider=provider)
    if conn is None:
        display_names = {"aws": "AWS", "gcp": "GCP", "azure": "Azure"}
        conn = DataSourceConnection(
            id=uuid4(),
            company_id=company_id,
            source_type=provider,
            display_name=display_names.get(provider, provider.upper()),
            status=status,
        )
        session.add(conn)
        await session.flush()
    return conn


async def has_mock_activities(
    session: AsyncSession, *, company_id: UUID, connection_id: UUID, year: int
) -> bool:
    result = await session.execute(
        select(ActivityRecord.id).where(
            ActivityRecord.company_id == company_id,
            ActivityRecord.data_source_connection_id == connection_id,
            ActivityRecord.period_start == date(year, 1, 1),
            ActivityRecord.period_end == date(year, 12, 31),
        )
    )
    return result.scalar_one_or_none() is not None


async def create_mock_cloud_activities(
    session: AsyncSession, *, company_id: UUID, connection: DataSourceConnection, year: int
) -> list[ActivityRecord]:
    period_start = date(year, 1, 1)
    period_end = date(year, 12, 31)

    mock_activities = [
        ActivityRecord(
            id=uuid4(),
            company_id=company_id,
            data_source_connection_id=connection.id,
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
            company_id=company_id,
            data_source_connection_id=connection.id,
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
        session.add(activity)
    await session.flush()
    connection.last_synced_at = datetime.now()
    await session.flush()
    return mock_activities


async def create_estimated_activity(
    session: AsyncSession, *, company_id: UUID, connection: DataSourceConnection, year: int
) -> ActivityRecord:
    period_start = date(year, 1, 1)
    period_end = date(year, 12, 31)
    activity = ActivityRecord(
        id=uuid4(),
        company_id=company_id,
        data_source_connection_id=connection.id,
        scope=3,
        scope_3_category="cloud",
        activity_type="cloud_compute_hours",
        quantity=Decimal("8000.0"),
        unit="hours",
        period_start=period_start,
        period_end=period_end,
        data_quality="estimated",
        assumptions="AI estimated based on company size and industry benchmarks",
        confidence_score=Decimal("70.0"),
    )
    session.add(activity)
    await session.flush()
    return activity
