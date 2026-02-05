"""FastAPI application entry point."""
import logging
import sys
import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, company, dashboard, insights, integrations, reports, onboarding, methodology
from app.config import get_settings

settings = get_settings()

# Structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("carbonly")

app = FastAPI(
    title="Carbonly API",
    description="Carbon accounting and emissions reporting platform for B2B SaaS SMBs",
    version="1.0.0",
    debug=settings.debug,
)

@app.on_event("startup")
async def startup_check():
    if settings.env == "production":
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is required in production")
        if not settings.secret_key or settings.secret_key.startswith("change-me-"):
            raise RuntimeError("SECRET_KEY must be set to a secure value in production")

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = uuid4().hex
    start_time = time.perf_counter()
    response = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        status_code = response.status_code if response else 500
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "Unexpected server error"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "detail": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": exc.errors()},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(company.router)
app.include_router(dashboard.router)
app.include_router(integrations.router)
app.include_router(reports.router)
app.include_router(insights.router)
app.include_router(onboarding.router)
app.include_router(methodology.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "app": "Carbonly API"}


@app.get("/health")
async def health():
    """Health check with DB connectivity verification."""
    from sqlalchemy import text

    from app.database import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.exception("DB health check failed")
        return {"status": "degraded", "database": "disconnected", "error": str(e)}


@app.get("/health/details")
async def health_details():
    """Detailed health endpoint (safe for prod)."""
    from sqlalchemy import text

    from app.database import engine

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "service": "carbonly-api",
            "environment": settings.env,
        }
    except Exception as e:
        logger.exception("Health details failed")
        return {
            "status": "degraded",
            "database": "disconnected",
            "service": "carbonly-api",
            "environment": settings.env,
            "error": str(e),
        }
