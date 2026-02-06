#!/usr/bin/env python3
"""
CLI script to seed demo company + user + emission factors for local development.
Usage: python scripts/seed_dev.py (run from backend/ directory)
"""
import asyncio
import os
import sys
from decimal import Decimal
from datetime import date
from uuid import uuid4

# Ensure app is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.auth import get_password_hash
from app.config import get_settings
from app.models.company import Company
from app.models.activity_record import ActivityRecord
from app.models.emission_factor import EmissionFactor
from app.models.user import User
from app.services.emissions import compute_estimates_for_company, refresh_emissions_summaries


async def seed():
    settings = get_settings()
    if settings.env == "production":
        raise RuntimeError("Refusing to seed data in production environment.")
    engine = create_async_engine(settings.database_url_async, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Seed emission factors if none exist (needed for compute_estimates)
        ef_count = (await session.execute(select(EmissionFactor).limit(1))).scalars().first()
        if ef_count is None:
            factors = [
                EmissionFactor(
                    id=uuid4(),
                    name="Cloud Compute (generic)",
                    activity_type="cloud_compute_hours",
                    factor_value=Decimal("0.00005"),  # kg CO2e per hour (simplified)
                    unit="hours",
                    scope=3,
                    scope_3_category="cloud",
                    source_citation="EPA/Cloud provider estimates",
                ),
                EmissionFactor(
                    id=uuid4(),
                    name="Cloud Storage (generic)",
                    activity_type="cloud_storage_gb_months",
                    factor_value=Decimal("0.00002"),  # kg CO2e per GB-month
                    unit="GB-months",
                    scope=3,
                    scope_3_category="cloud",
                    source_citation="EPA/Cloud provider estimates",
                ),
            ]
            for f in factors:
                session.add(f)
            await session.flush()
            print("Seeded emission factors")

        result = await session.execute(select(User).where(User.email == "test@carbonly.com"))
        existing = result.scalar_one_or_none()

        if existing:
            print("Demo user already exists: test@carbonly.com / password123")
            # Load company so we can re-seed activity data after TRUNCATE
            company = await session.get(Company, existing.company_id)
            if company is None:
                raise RuntimeError("Demo user exists but company not found")
        else:
            company = Company(
                name="Carbonly Demo Co",
                industry="B2B SaaS",
                employee_count=85,
                hq_location="San Francisco, CA",
                reporting_year=2025,
                email_notifications=True,
                monthly_summary_reports=True,
                unit_system="metric_tco2e",
                onboarding_state={
                    "connect_aws": False,
                    "upload_csv": False,
                    "add_manual_activity": False,
                    "create_report": False,
                },
            )
            session.add(company)
            await session.flush()

            user = User(
                email="test@carbonly.com",
                full_name="Demo User",
                company_id=company.id,
                is_active=True,
                password_hash=get_password_hash("password123"),
            )
            session.add(user)
            await session.flush()


        # Seed activity records across multiple months for charts
        year = 2025
        for month in range(1, 13):
            period_start = date(year, month, 1)
            period_end = date(year, month, 28)
            session.add(
                ActivityRecord(
                    id=uuid4(),
                    company_id=company.id,
                    data_source_connection_id=None,
                    scope=3,
                    scope_3_category="cloud",
                    activity_type="cloud_compute_hours",
                    quantity=Decimal("800") + Decimal(month * 10),
                    unit="hours",
                    period_start=period_start,
                    period_end=period_end,
                    data_quality="estimated",
                    assumptions="Seeded demo data",
                    confidence_score=Decimal("75.0"),
                )
            )
            session.add(
                ActivityRecord(
                    id=uuid4(),
                    company_id=company.id,
                    data_source_connection_id=None,
                    scope=3,
                    scope_3_category="cloud",
                    activity_type="cloud_storage_gb_months",
                    quantity=Decimal("500") + Decimal(month * 5),
                    unit="GB-months",
                    period_start=period_start,
                    period_end=period_end,
                    data_quality="estimated",
                    assumptions="Seeded demo data",
                    confidence_score=Decimal("75.0"),
                )
            )
        await session.flush()

        # Compute estimates and summaries
        await compute_estimates_for_company(session, company.id, replace_existing=True)
        await refresh_emissions_summaries(session, company.id, year)
        await session.commit()
        print("Seeded demo user + monthly activity data: test@carbonly.com / password123")


if __name__ == "__main__":
    asyncio.run(seed())
