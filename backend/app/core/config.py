"""Application configuration from environment."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings; load from env and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Carbonly"
    debug: bool = False
    env: Literal["local", "development", "staging", "production"] = "local"
    enable_docs: bool = False
    trust_proxy_headers: bool = True
    rate_limit_enabled: bool = True
    demo_mode: bool = False
    frontend_base_url: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_starter: str = ""
    stripe_price_pro: str = ""
    stripe_test_mode: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/carbonly"

    # JWT
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours (env: ACCESS_TOKEN_EXPIRE_MINUTES)

    # CORS - comma-separated origins
    cors_origins: str = ""

    # Google OAuth (optional)
    google_client_id: str | None = None
    google_client_secret: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if origins:
            return origins
        if self.env in {"local", "development"}:
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]
        return []

    @property
    def is_dev_mode(self) -> bool:
        """True if dev-only endpoints (dev-seed, dev-db-check) should be enabled."""
        return self.env == "development"

    @property
    def database_url_async(self) -> str:
        """Normalize DATABASE_URL for async SQLAlchemy (Render uses postgres://)."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
