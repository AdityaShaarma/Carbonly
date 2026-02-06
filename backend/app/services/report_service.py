"""Report generation helpers."""
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.emissions import get_annual_totals_by_scope, get_monthly_breakdown_by_scope


async def build_report_snapshot(
    session: AsyncSession, *, company_name: str, company_id: UUID, reporting_year: int
) -> tuple[dict[str, Any], Decimal]:
    annual_totals = await get_annual_totals_by_scope(session, company_id, reporting_year)
    total_co2e = sum(row[2] for row in annual_totals)

    scope_1_total = sum(row[2] for row in annual_totals if row[0] == 1)
    scope_2_total = sum(row[2] for row in annual_totals if row[0] == 2)
    scope_3_total = sum(row[2] for row in annual_totals if row[0] == 3)

    scope_3_breakdown: dict[str, Decimal] = {}
    for row in annual_totals:
        if row[0] == 3 and row[1]:
            scope_3_breakdown[row[1]] = scope_3_breakdown.get(row[1], Decimal("0")) + row[2]

    monthly_rows = await get_monthly_breakdown_by_scope(session, company_id, reporting_year)
    monthly_by_month: dict[str, dict[int, Decimal]] = {}
    for period_value, scope, scope_3_cat, total in monthly_rows:
        if period_value not in monthly_by_month:
            monthly_by_month[period_value] = {1: Decimal("0"), 2: Decimal("0"), 3: Decimal("0")}
        monthly_by_month[period_value][scope] += total

    monthly_breakdown = []
    for month in sorted(monthly_by_month.keys()):
        total_month = sum(monthly_by_month[month].values())
        monthly_breakdown.append(
            {
                "month": month,
                "scope_1": monthly_by_month[month].get(1, Decimal("0")),
                "scope_2": monthly_by_month[month].get(2, Decimal("0")),
                "scope_3": monthly_by_month[month].get(3, Decimal("0")),
                "total": total_month,
            }
        )

    executive_summary = (
        f"This carbon disclosure report presents {company_name}'s greenhouse gas (GHG) "
        f"emissions for {reporting_year}. Total annual emissions: {total_co2e:.2f} kg CO₂e "
        f"({(total_co2e / Decimal('1000')).quantize(Decimal('0.01'))} tCO₂e). "
        f"Scope 1: {scope_1_total:.2f} kg CO₂e. "
        f"Scope 2: {scope_2_total:.2f} kg CO₂e. "
        f"Scope 3: {scope_3_total:.2f} kg CO₂e."
    )

    content_snapshot = {
        "executive_summary": executive_summary.strip(),
        "scope_1_kg_co2e": scope_1_total,
        "scope_2_kg_co2e": scope_2_total,
        "scope_3_kg_co2e": scope_3_total,
        "scope_3_breakdown": scope_3_breakdown,
        "methodology_notes": (
            "Emissions calculated using activity data multiplied by emission factors. "
            "Activity data sources include connected cloud providers, AI-estimated values, "
            "and manual entries. Each estimate tracks data quality (measured/estimated/manual), "
            "assumptions, and confidence scores."
        ),
        "assumptions_limitations": (
            "Emission factors are sourced from recognized databases (EPA, DEFRA, provider-specific "
            "factors). Scope 3 coverage is limited to cloud services, travel, remote work, "
            "commuting, and purchased services. Some estimates may be based on industry benchmarks."
        ),
        "emission_factor_citations": [
            {"source": "EPA", "url_or_ref": "EPA Emission Factors Hub"},
            {"source": "DEFRA", "url_or_ref": "UK Government Conversion Factors"},
            {"source": "Cloud Providers", "url_or_ref": "AWS/GCP/Azure sustainability reports"},
        ],
        "monthly_breakdown": monthly_breakdown,
    }

    return content_snapshot, total_co2e
