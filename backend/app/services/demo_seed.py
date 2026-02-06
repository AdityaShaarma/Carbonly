"""Demo data seeding."""
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_password_hash
from app.models.company import Company
from app.models.user import User
from app.models.report import Report


DEMO_EMAIL = "demo@carbonly.com"
DEMO_PASSWORD = "demo1234"
DEMO_COMPANY = "Carbonly Demo Co."


async def ensure_demo_data(session: AsyncSession) -> User:
    user = (await session.execute(select(User).where(User.email == DEMO_EMAIL))).scalar_one_or_none()
    if user:
        return user

    company = Company(
        id=uuid4(),
        name=DEMO_COMPANY,
        industry="SaaS",
        employee_count=42,
        hq_location="Remote",
        reporting_year=2025,
        email_notifications=False,
        monthly_summary_reports=False,
        unit_system="metric_tco2e",
        onboarding_state={"connect_aws": True, "upload_csv": True, "add_manual_activity": True, "create_report": True},
    )
    session.add(company)
    await session.flush()

    user = User(
        id=uuid4(),
        email=DEMO_EMAIL,
        full_name="Demo User",
        company_id=company.id,
        password_hash=get_password_hash(DEMO_PASSWORD),
        is_email_verified=True,
        is_demo=True,
    )
    session.add(user)
    await session.flush()

    report = Report(
        company_id=company.id,
        created_by_user_id=user.id,
        title="Demo Carbon Disclosure",
        company_name_snapshot=company.name,
        reporting_year=company.reporting_year,
        total_kg_co2e=0,
        status="published",
        shareable_token="demo-share-token",
        content_snapshot={},
    )
    session.add(report)
    await session.flush()

    return user
