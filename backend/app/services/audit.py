"""Audit logging utilities."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.base import utc_now


async def log_audit_action(
    session: AsyncSession,
    *,
    user_id: UUID,
    company_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        company_id=company_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        created_at=utc_now(),
    )
    session.add(entry)
    await session.flush()
