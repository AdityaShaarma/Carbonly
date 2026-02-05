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

    # Database
    database_url: str = "postgresql+asyncpg://localhost:5432/carbonly"

    # JWT
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours (env: ACCESS_TOKEN_EXPIRE_MINUTES)

    # CORS - comma-separated origins
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Google OAuth (optional)
    google_client_id: str | None = None
    google_client_secret: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_dev_mode(self) -> bool:
        """True if dev-only endpoints (dev-seed, dev-db-check) should be enabled."""
        return self.env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
