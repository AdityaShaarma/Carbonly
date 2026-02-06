"""Idempotency helpers for safe retries."""
import hashlib
import json
from typing import Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency_key import IdempotencyKey


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(jsonable_encoder(payload), sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


async def get_idempotency_record(
    session: AsyncSession,
    *,
    company_id: UUID,
    endpoint: str,
    key: str,
) -> IdempotencyKey | None:
    result = await session.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.company_id == company_id,
            IdempotencyKey.endpoint == endpoint,
            IdempotencyKey.idempotency_key == key,
        )
    )
    return result.scalar_one_or_none()


async def store_idempotency_record(
    session: AsyncSession,
    *,
    company_id: UUID,
    user_id: UUID | None,
    endpoint: str,
    key: str,
    request_payload: Any | None,
    response_body: Any,
    response_status: int,
) -> IdempotencyKey:
    record = IdempotencyKey(
        company_id=company_id,
        user_id=user_id,
        endpoint=endpoint,
        idempotency_key=key,
        request_hash=_hash_payload(request_payload) if request_payload is not None else None,
        response_status=response_status,
        response_body=jsonable_encoder(response_body),
    )
    session.add(record)
    await session.flush()
    return record


def payload_hash(payload: Any | None) -> str | None:
    if payload is None:
        return None
    return _hash_payload(payload)
