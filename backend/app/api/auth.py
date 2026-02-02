"""Authentication API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, text

from app.auth import (
    CurrentUser,
    DbSession,
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.config import get_settings
from app.models.company import Company
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, TokenResponse, UserResponse
from app.schemas.company import CompanyResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: DbSession):
    """Login with email and password. Returns JWT token."""
    result = await db.execute(
        select(User).where(User.email == request.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=MeResponse)
async def get_current_user_info(user: CurrentUser, db: DbSession):
    """Get current authenticated user and their company."""
    result = await db.execute(select(Company).where(Company.id == user.company_id))
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )

    return MeResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            company_id=str(user.company_id),
        ),
        company=CompanyResponse(
            id=str(company.id),
            name=company.name,
            industry=company.industry,
            employee_count=company.employee_count,
            hq_location=company.hq_location,
            reporting_year=company.reporting_year,
            email_notifications=company.email_notifications,
            monthly_summary_reports=company.monthly_summary_reports,
            unit_system=company.unit_system,
        ),
    )


@router.post("/dev-seed")
async def dev_seed(db: DbSession):
    """
    DEV ONLY: seeds a demo company + user + emission factors. Enabled only when DEBUG=true or ENV=local.
    Returns 404 when disabled.
    """
    if not settings.is_dev_mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    from decimal import Decimal
    from uuid import uuid4

    from app.models.emission_factor import EmissionFactor

    # Seed emission factors if none exist
    ef_exists = (await db.execute(select(EmissionFactor).limit(1))).scalar_one_or_none()
    if ef_exists is None:
        for f in [
            EmissionFactor(
                name="Cloud Compute (generic)",
                activity_type="cloud_compute_hours",
                factor_value=Decimal("0.00005"),
                unit="hours",
                scope=3,
                scope_3_category="cloud",
                source_citation="EPA/Cloud provider estimates",
            ),
            EmissionFactor(
                name="Cloud Storage (generic)",
                activity_type="cloud_storage_gb_months",
                factor_value=Decimal("0.00002"),
                unit="GB-months",
                scope=3,
                scope_3_category="cloud",
                source_citation="EPA/Cloud provider estimates",
            ),
        ]:
            db.add(f)
        await db.flush()

    result = await db.execute(select(User).where(User.email == "test@carbonly.com"))
    existing = result.scalar_one_or_none()
    if existing:
        return {
            "ok": True,
            "email": "test@carbonly.com",
            "password": "password123",
            "note": "already exists",
        }

    company = Company(
        name="Carbonly Demo Co",
        industry="B2B SaaS",
        employee_count=85,
        hq_location="San Francisco, CA",
        reporting_year=2025,
        email_notifications=True,
        monthly_summary_reports=True,
        unit_system="metric_tco2e",
    )
    db.add(company)
    await db.flush()

    user = User(
        email="test@carbonly.com",
        full_name="Demo User",
        company_id=company.id,
        is_active=True,
        password_hash=get_password_hash("password123"),
    )
    db.add(user)
    await db.commit()

    return {"ok": True, "email": "test@carbonly.com", "password": "password123"}


@router.get("/dev-db-check")
async def dev_db_check(db: DbSession):
    """
    DEV ONLY: returns current DB name, user, and user count. Enabled only when DEBUG=true or ENV=local.
    """
    if not settings.is_dev_mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    dbname = (await db.execute(text("SELECT current_database()"))).scalar_one()
    dbuser = (await db.execute(text("SELECT current_user"))).scalar_one()
    count_users = (
        await db.execute(select(func.count()).select_from(User))
    ).scalar_one()
    emails = (await db.execute(select(User.email))).scalars().all()

    return {
        "current_database": dbname,
        "current_user": dbuser,
        "users_count": count_users,
        "emails": [e for e in emails],
    }
