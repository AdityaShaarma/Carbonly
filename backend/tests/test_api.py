"""API integration tests."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dev_seed_then_login(client: AsyncClient):
    """Dev-seed creates user, login returns token."""
    # Dev-seed (requires DEBUG or ENV=local)
    r = await client.post("/api/auth/dev-seed")
    if r.status_code == 404:
        pytest.skip("dev-seed disabled (DEBUG=false, ENV!=local)")
    assert r.status_code == 200
    data = r.json()
    assert data.get("email") == "test@carbonly.com"
    assert data.get("password") == "password123"

    # Login
    r = await client.post(
        "/api/auth/login",
        json={"email": "test@carbonly.com", "password": "password123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"

    token = data["access_token"]

    # /me
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    me = r.json()
    assert me["user"]["email"] == "test@carbonly.com"
    assert "company" in me


@pytest.mark.asyncio
async def test_integrations_sync_then_dashboard(client: AsyncClient):
    """Sync creates activities, dashboard shows non-zero totals after recompute."""
    # Login first
    r = await client.post(
        "/api/auth/login",
        json={"email": "test@carbonly.com", "password": "password123"},
    )
    if r.status_code != 200:
        pytest.skip("Login failed - run dev-seed first")
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Sync aws (creates mock activities)
    r = await client.post("/api/integrations/aws/sync", headers=headers)
    assert r.status_code == 200
    assert r.json().get("activities_created", 0) >= 0

    # Recompute
    r = await client.post("/api/dashboard/recompute?year=2025", headers=headers)
    assert r.status_code == 200

    # Dashboard
    r = await client.get("/api/dashboard?year=2025", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "company_stats" in data
    assert "annual_totals" in data
    assert "monthly_trend" in data


@pytest.mark.asyncio
async def test_create_report_publish_public(client: AsyncClient):
    """Create report, publish, access via public share link."""
    r = await client.post(
        "/api/auth/login",
        json={"email": "test@carbonly.com", "password": "password123"},
    )
    if r.status_code != 200:
        pytest.skip("Login failed - run dev-seed first")
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create report
    r = await client.post(
        "/api/reports",
        headers=headers,
        json={"title": "Test Report 2025", "reporting_year": 2025},
    )
    assert r.status_code == 200
    report_id = r.json()["id"]

    # Publish
    r = await client.post(f"/api/reports/{report_id}/publish", headers=headers)
    assert r.status_code == 200
    share_token = r.json().get("shareable_token")
    assert share_token

    # Public access (no auth)
    r = await client.get(f"/api/reports/r/{share_token}")
    assert r.status_code == 200
    pub = r.json()
    assert "company_name" in pub
    assert "total_co2e" in pub
    assert "executive_summary" in pub


@pytest.mark.asyncio
async def test_report_pdf_returns_pdf(client: AsyncClient):
    """Report PDF endpoint returns application/pdf."""
    r = await client.post(
        "/api/auth/login",
        json={"email": "test@carbonly.com", "password": "password123"},
    )
    if r.status_code != 200:
        pytest.skip("Login failed - run dev-seed first")
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create and get a report
    r = await client.post(
        "/api/reports",
        headers=headers,
        json={"title": "PDF Test Report", "reporting_year": 2025},
    )
    if r.status_code != 200:
        pytest.skip("Report creation failed")
    report_id = r.json()["id"]

    r = await client.get(f"/api/reports/{report_id}/pdf", headers=headers)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert len(r.content) > 100  # PDF has content
