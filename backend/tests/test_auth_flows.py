"""Auth flow integration tests."""
from datetime import datetime, timedelta, timezone
import hashlib
import uuid

import pytest
from httpx import AsyncClient

from app.auth import get_password_hash, verify_password
from app.models.company import Company
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User
from app.config import get_settings


@pytest.mark.asyncio
async def test_signup_creates_user_and_returns_token(client: AsyncClient):
    email = f"signup-{uuid.uuid4().hex[:8]}@example.com"
    r = await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "password123", "full_name": "Signup User"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["user"]["email"] == email
    assert data["user"]["is_email_verified"] is False


@pytest.mark.asyncio
async def test_forgot_password_always_200(client: AsyncClient):
    r = await client.post("/api/auth/password/forgot", json={"email": "nope@example.com"})
    assert r.status_code == 200
    assert r.json().get("ok") is True


@pytest.mark.asyncio
async def test_reset_password_changes_hash_and_token_single_use(client: AsyncClient, db_session):
    company = Company(
        name="Reset Co",
        industry="SaaS",
        employee_count=5,
        hq_location="",
        reporting_year=2025,
        email_notifications=True,
        monthly_summary_reports=True,
        unit_system="metric_tco2e",
        onboarding_state=None,
    )
    db_session.add(company)
    await db_session.flush()

    user = User(
        email=f"reset-{uuid.uuid4().hex[:8]}@example.com",
        full_name="Reset User",
        company_id=company.id,
        is_active=True,
        password_hash=get_password_hash("old-password"),
        is_email_verified=True,
        is_demo=False,
    )
    db_session.add(user)
    await db_session.flush()

    raw_token = f"reset-{uuid.uuid4().hex}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db_session.add(reset_record)
    await db_session.commit()

    old_hash = user.password_hash

    r = await client.post(
        "/api/auth/password/reset",
        json={"token": raw_token, "new_password": "new-password-123"},
    )
    assert r.status_code == 200
    assert r.json().get("ok") is True

    await db_session.refresh(user)
    assert user.password_hash != old_hash
    assert verify_password("new-password-123", user.password_hash)

    r = await client.post(
        "/api/auth/password/reset",
        json={"token": raw_token, "new_password": "another-password"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_demo_login_requires_demo_mode(client: AsyncClient):
    settings = get_settings()
    r = await client.post("/api/auth/demo")
    if settings.demo_mode:
        assert r.status_code == 200
        assert "access_token" in r.json()
    else:
        assert r.status_code == 404
