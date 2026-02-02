"""FastAPI application entry point."""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, company, dashboard, insights, integrations, reports
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
