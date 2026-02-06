"""Billing API endpoints (Stripe)."""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from app.auth import CurrentCompany, CurrentUser, DbSession
from app.config import get_settings
from app.models.company import Company

import stripe

router = APIRouter(prefix="/api/billing", tags=["billing"])
settings = get_settings()


class CheckoutSessionRequest(BaseModel):
    plan: Literal["starter", "pro"]


class CheckoutSessionResponse(BaseModel):
    url: str


class CheckoutSuccessRequest(BaseModel):
    session_id: str


class CheckoutSuccessResponse(BaseModel):
    plan: str
    billing_status: str
    current_period_end: str | None


def _price_for_plan(plan: str) -> str:
    if plan == "starter":
        return settings.stripe_price_starter
    if plan == "pro":
        return settings.stripe_price_pro
    return ""


def _plan_for_price(price_id: str) -> str:
    if price_id == settings.stripe_price_starter:
        return "starter"
    if price_id == settings.stripe_price_pro:
        return "pro"
    return "demo"


def _success_url() -> str:
    return f"{settings.frontend_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"


def _cancel_url() -> str:
    return f"{settings.frontend_url}/billing/cancel"


def _normalize_status(status_value: str | None) -> str:
    if status_value in {"active", "trialing"}:
        return "active"
    if status_value in {"past_due", "unpaid", "incomplete", "incomplete_expired"}:
        return "past_due"
    if status_value in {"canceled", "cancelled"}:
        return "canceled"
    return "inactive"


def _set_company_billing(
    company: Company,
    *,
    customer_id: str | None,
    subscription_id: str | None,
    price_id: str | None,
    status_value: str | None,
    period_end: int | None,
) -> None:
    company.stripe_customer_id = customer_id or company.stripe_customer_id
    company.stripe_subscription_id = subscription_id or company.stripe_subscription_id
    plan = _plan_for_price(price_id or "")
    normalized = _normalize_status(status_value)
    company.subscription_status = normalized
    company.billing_status = normalized
    if period_end:
        company.current_period_end = datetime.fromtimestamp(int(period_end), tz=timezone.utc)
    if normalized != "active":
        company.plan = "demo"
        if normalized == "canceled":
            company.stripe_subscription_id = None
    else:
        company.plan = plan


@router.post("/portal-session")
async def create_portal_session(
    company: CurrentCompany = None,
    user: CurrentUser = None,
):
    if user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "detail": "Demo sandbox users cannot subscribe"},
        )
    if not settings.stripe_secret_key or not settings.frontend_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe environment is not fully configured.",
        )
    if not company or not company.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe customer not found for this organization.",
        )
    stripe.api_key = settings.stripe_secret_key

    def _create_portal():
        return stripe.billing_portal.Session.create(
            customer=company.stripe_customer_id,
            return_url=f"{settings.frontend_url}/billing",
        )

    try:
        session = await run_in_threadpool(_create_portal)
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.user_message or str(exc)),
        )
    return {"url": session.url}


@router.post("/checkout-success", response_model=CheckoutSuccessResponse)
async def checkout_success(
    request: CheckoutSuccessRequest,
    company: CurrentCompany = None,
    user: CurrentUser = None,
    db: DbSession = None,
):
    if user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "detail": "Demo sandbox users cannot subscribe"},
        )
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe environment is not fully configured.",
        )
    stripe.api_key = settings.stripe_secret_key

    def _retrieve_session():
        return stripe.checkout.Session.retrieve(
            request.session_id, expand=["subscription", "customer"]
        )

    try:
        session = await run_in_threadpool(_retrieve_session)
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.user_message or str(exc)),
        )

    if session.get("payment_status") not in {"paid"} and session.get("status") != "complete":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Checkout session is not complete.",
        )

    subscription = session.get("subscription")
    customer = session.get("customer")
    subscription_id = subscription.get("id") if isinstance(subscription, dict) else None
    customer_id = customer.get("id") if isinstance(customer, dict) else None
    items = (subscription.get("items") or {}).get("data") if isinstance(subscription, dict) else []
    price_id = items[0].get("price", {}).get("id") if items else None
    period_end = subscription.get("current_period_end") if isinstance(subscription, dict) else None

    _set_company_billing(
        company,
        customer_id=customer_id,
        subscription_id=subscription_id,
        price_id=price_id,
        status_value="active",
        period_end=period_end,
    )
    await db.commit()
    await db.refresh(company)

    return CheckoutSuccessResponse(
        plan=company.plan,
        billing_status=company.billing_status,
        current_period_end=company.current_period_end.isoformat()
        if company.current_period_end
        else None,
    )


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    company: CurrentCompany = None,
    user: CurrentUser = None,
    db: DbSession = None,
):
    if user.is_demo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "detail": "Demo sandbox users cannot subscribe"},
        )
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "stripe_not_configured", "message": "Billing is unavailable."}},
        )
    if not settings.stripe_price_starter or not settings.stripe_price_pro or not settings.frontend_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe environment is not fully configured.",
        )
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "company_not_found", "message": "Company not found."}},
        )
    price_id = _price_for_plan(request.plan)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "invalid_plan", "message": "Unknown plan requested."}},
        )

    stripe.api_key = settings.stripe_secret_key

    def _ensure_customer():
        if company.stripe_customer_id:
            return company.stripe_customer_id
        customer = stripe.Customer.create(
            email=user.email,
            name=company.name,
            metadata={"company_id": str(company.id)},
        )
        return customer.id

    try:
        customer_id = await run_in_threadpool(_ensure_customer)
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.user_message or str(exc)),
        )
    if company.stripe_customer_id != customer_id:
        company.stripe_customer_id = customer_id
        if company.stripe_customer_id is not None and not isinstance(
            company.stripe_customer_id, str
        ):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe customer id type error",
            )
        await db.commit()
        await db.refresh(company)

    def _create_session():
        return stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=_success_url(),
            cancel_url=_cancel_url(),
            customer=customer_id,
            metadata={"company_id": str(company.id), "plan": request.plan},
        )

    try:
        session = await run_in_threadpool(_create_session)
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.user_message or str(exc)),
        )
    if not getattr(session, "url", None):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe session URL missing",
        )
    return CheckoutSessionResponse(url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: DbSession):
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook not configured")

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    stripe.api_key = settings.stripe_secret_key

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    event_type = event.get("type")
    data_object = event.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        company_id = (data_object.get("metadata") or {}).get("company_id")
        subscription_id = data_object.get("subscription")
        customer_id = data_object.get("customer")
        subscription = None
        if subscription_id:
            subscription = await run_in_threadpool(stripe.Subscription.retrieve, subscription_id)

        if company_id:
            result = await db.execute(select(Company).where(Company.id == company_id))
            company = result.scalar_one_or_none()
            if company:
                price_id = None
                items = (subscription.get("items") or {}).get("data") if subscription else []
                if items:
                    price_id = items[0].get("price", {}).get("id")
                _set_company_billing(
                    company,
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    price_id=price_id,
                    status_value=subscription.get("status") if subscription else "active",
                    period_end=subscription.get("current_period_end") if subscription else None,
                )
                await db.commit()

    if event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        subscription_id = data_object.get("id")
        customer_id = data_object.get("customer")
        price_id = None
        items = (data_object.get("items") or {}).get("data") or []
        if items:
            price_id = items[0].get("price", {}).get("id")
        period_end = data_object.get("current_period_end")
        status_value = data_object.get("status") or "inactive"

        q = select(Company).where(
            (Company.stripe_subscription_id == subscription_id)
            | (Company.stripe_customer_id == customer_id)
        )
        result = await db.execute(q)
        company = result.scalar_one_or_none()
        if company:
            _set_company_billing(
                company,
                customer_id=customer_id,
                subscription_id=subscription_id,
                price_id=price_id,
                status_value=status_value,
                period_end=period_end,
            )
            await db.commit()

    if event_type == "invoice.payment_failed":
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("subscription")
        result = await db.execute(
            select(Company).where(
                (Company.stripe_customer_id == customer_id)
                | (Company.stripe_subscription_id == subscription_id)
            )
        )
        company = result.scalar_one_or_none()
        if company:
            company.billing_status = "past_due"
            company.subscription_status = "past_due"
            await db.commit()

    return {"received": True}
