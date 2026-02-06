"""Authentication API endpoints."""
from typing import Annotated
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select, text

from app.auth import (
    CurrentUser,
    OptionalUser,
    DbSession,
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.config import get_settings
from app.models.company import Company
from app.models.user import User
from app.models.email_verification_token import EmailVerificationToken
from app.models.password_reset_token import PasswordResetToken
from app.services.email import send_email
from app.services.demo_seed import ensure_demo_data
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
    SignupRequest,
    SignupResponse,
    VerifyEmailRequest,
    TokenResponse,
    UserResponse,
)
from app.schemas.company import CompanyResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()

# In-memory rate limiter (MVP safe)
_rate_limits = defaultdict(lambda: deque())
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 10     # requests per window


def _rate_limit_key(request: Request, action: str) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"{client_ip}:{action}"


def rate_limit(request: Request, action: str):
    if not settings.rate_limit_enabled:
        return
    key = _rate_limit_key(request, action)
    now = time.time()
    q = _rate_limits[key]
    while q and now - q[0] > RATE_LIMIT_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
        )
    q.append(now)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, http_request: Request, db: DbSession):
    """Login with email and password. Returns JWT token."""
    rate_limit(http_request, "login")
    result = await db.execute(
        select(User).where(User.email == request.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "Incorrect email or password"}},
        )
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "invalid_credentials", "message": "Incorrect email or password"}},
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "company_not_found", "message": "Company not found"}},
        )

    return MeResponse(
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            company_id=str(user.company_id),
            is_email_verified=user.is_email_verified,
            is_demo=user.is_demo,
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
            plan=company.plan,
            billing_status=company.billing_status,
            subscription_status=company.subscription_status,
            current_period_end=company.current_period_end.isoformat()
            if company.current_period_end
            else None,
        ),
    )


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, http_request: Request, db: DbSession):
    """Register a new company + user."""
    rate_limit(http_request, "register")
    existing = (await db.execute(select(User).where(User.email == request.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "email_exists", "message": "Email already registered"}},
        )

    company = Company(
        name=request.company_name,
        industry="SaaS",
        employee_count=10,
        hq_location="",
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
    db.add(company)
    await db.flush()

    user = User(
        email=request.email,
        full_name=None,
        company_id=company.id,
        is_active=True,
        password_hash=get_password_hash(request.password),
        is_email_verified=False,
        is_demo=False,
    )
    db.add(user)
    await db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    return RegisterResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            company_id=str(user.company_id),
            is_email_verified=user.is_email_verified,
            is_demo=user.is_demo,
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
            plan=company.plan,
            billing_status=company.billing_status,
            subscription_status=company.subscription_status,
            current_period_end=company.current_period_end.isoformat()
            if company.current_period_end
            else None,
        ),
    )


def _token_hash(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _verification_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=24)


def _reset_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=45)


@router.post("/signup", response_model=SignupResponse)
async def signup(request: SignupRequest, http_request: Request, db: DbSession):
    rate_limit(http_request, "signup")
    existing = (await db.execute(select(User).where(User.email == request.email))).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": {"code": "email_exists", "message": "Email already registered"}},
        )

    company_name = request.email.split("@")[0].strip().title() or "New Company"
    company = Company(
        name=f"{company_name} Company",
        industry="SaaS",
        employee_count=1,
        hq_location="",
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
    db.add(company)
    await db.flush()

    user = User(
        email=request.email,
        full_name=request.full_name,
        company_id=company.id,
        is_active=True,
        password_hash=get_password_hash(request.password),
        is_email_verified=False,
        is_demo=False,
    )
    db.add(user)
    await db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})
    return SignupResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            company_id=str(user.company_id),
            is_email_verified=user.is_email_verified,
            is_demo=user.is_demo,
        ),
    )


@router.post("/verify/request")
async def request_email_verification(
    request: VerifyEmailRequest,
    http_request: Request,
    db: DbSession,
    user: OptionalUser = None,
):
    rate_limit(http_request, "verify_request")
    target_user = user
    if request.email:
        target_user = (
            await db.execute(select(User).where(User.email == request.email))
        ).scalar_one_or_none()

    if target_user:
        raw_token = secrets.token_urlsafe(32)
        token_hash = _token_hash(raw_token)
        db.add(
            EmailVerificationToken(
                user_id=target_user.id,
                token_hash=token_hash,
                expires_at=_verification_expires_at(),
            )
        )
        await db.commit()
        verify_link = f"{settings.frontend_base_url}/verify-email?token={raw_token}"
        send_email(
            to=target_user.email,
            subject="Verify your Carbonly email",
            body=f"Verify your email: {verify_link}",
        )
    return {"ok": True}


@router.get("/verify")
async def verify_email(token: str, db: DbSession):
    token_hash = _token_hash(token)
    record = (
        await db.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
        )
    ).scalar_one_or_none()
    if not record or record.used_at or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_token", "message": "Verification token is invalid or expired"}},
        )
    user = (await db.execute(select(User).where(User.id == record.user_id))).scalar_one()
    user.is_email_verified = True
    record.used_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@router.post("/password/forgot")
async def password_forgot(request: PasswordResetRequest, http_request: Request, db: DbSession):
    rate_limit(http_request, "password_forgot")
    user = (await db.execute(select(User).where(User.email == request.email))).scalar_one_or_none()
    if user:
        raw_token = secrets.token_urlsafe(32)
        token_hash = _token_hash(raw_token)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=_reset_expires_at(),
            )
        )
        await db.commit()
        reset_link = f"{settings.frontend_base_url}/reset-password?token={raw_token}"
        send_email(
            to=user.email,
            subject="Reset your Carbonly password",
            body=f"Reset your password: {reset_link}",
        )
    return {"ok": True}


@router.post("/password/reset")
async def password_reset(request: PasswordResetConfirm, http_request: Request, db: DbSession):
    rate_limit(http_request, "password_reset")
    token_hash = _token_hash(request.token)
    record = (
        await db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
    ).scalar_one_or_none()
    if not record or record.used_at or record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_token", "message": "Reset token is invalid or expired"}},
        )
    user = (await db.execute(select(User).where(User.id == record.user_id))).scalar_one()
    user.password_hash = get_password_hash(request.new_password)
    record.used_at = datetime.now(timezone.utc)
    await db.commit()
    return {"ok": True}


@router.post("/demo")
async def demo_login(db: DbSession):
    if not settings.demo_mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    user = await ensure_demo_data(db)
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/dev-seed")
async def dev_seed(db: DbSession):
    """
    DEV ONLY: seeds a demo company + user + emission factors. Enabled only when ENV=development.
    Returns 404 when disabled.
    """
    if not settings.is_dev_mode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    from decimal import Decimal
    from uuid import uuid4
    from datetime import date

    from app.models.activity_record import ActivityRecord
    from app.models.emission_factor import EmissionFactor
    from app.services.emissions import compute_estimates_for_company, refresh_emissions_summaries

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
        onboarding_state={
            "connect_aws": False,
            "upload_csv": False,
            "add_manual_activity": False,
            "create_report": False,
        },
    )
    db.add(company)
    await db.flush()

    user = User(
        email="test@carbonly.com",
        full_name="Demo User",
        company_id=company.id,
        is_active=True,
        password_hash=get_password_hash("password123"),
        is_email_verified=True,
        is_demo=False,
    )
    db.add(user)
    await db.flush()

    # Seed multi-month demo activity data
    year = 2025
    for month in range(1, 13):
        period_start = date(year, month, 1)
        period_end = date(year, month, 28)
        db.add(
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
        db.add(
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
    await db.flush()

    await compute_estimates_for_company(db, company.id, replace_existing=True)
    await refresh_emissions_summaries(db, company.id, year)
    await db.commit()

    return {"ok": True, "email": "test@carbonly.com", "password": "password123"}


@router.get("/dev-db-check")
async def dev_db_check(db: DbSession):
    """
    DEV ONLY: returns current DB name, user, and user count. Enabled only when ENV=development.
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
