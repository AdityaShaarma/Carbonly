"""Insights API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.auth import PaidCompany, DbSession
from app.schemas.insights import InsightResponse, InsightsResponse

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("", response_model=InsightsResponse)
async def get_insights(
    year: Annotated[int, Query(description="Reporting year")] = 2025,
    company: PaidCompany = None,
    db: DbSession = None,
):
    """
    Get reduction recommendations/insights.
    For now, returns static mocked insights matching the UI.
    """
    # Mock insights - in production, these could be generated based on company data
    insights = [
        InsightResponse(
            id="1",
            title="Optimize cloud resources",
            description="Review and right-size cloud compute instances. Consider reserved instances for predictable workloads.",
            impact_level="High",
            estimated_reduction_percent=15.0,
            category="cloud",
        ),
        InsightResponse(
            id="2",
            title="Choose renewable-powered regions",
            description="Migrate workloads to cloud regions powered by renewable energy sources.",
            impact_level="Medium",
            estimated_reduction_percent=30.0,
            category="cloud",
        ),
        InsightResponse(
            id="3",
            title="Maintain remote-first policy",
            description="Continue remote work policies to reduce commuting and office energy consumption.",
            impact_level="Medium",
            estimated_reduction_percent=10.0,
            category="remote_work",
        ),
        InsightResponse(
            id="4",
            title="Extend hardware lifecycle",
            description="Extend laptop and device replacement cycles from 3 to 4-5 years to reduce Scope 3 emissions.",
            impact_level="Low",
            estimated_reduction_percent=5.0,
            category="purchased_services",
        ),
    ]

    return InsightsResponse(insights=insights)
