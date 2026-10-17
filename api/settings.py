from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- инфраструктура ---
    database_url: str
    direct_url: str | None = None
    environment: str = "development"
    log_level: str = "INFO"

    # --- бизнес-конфиг (можно менять без деплоя) ---
    fallback_phone: str = "+375 (25) 111 11 11"
    rate_limit_max: int = Field(default=5, ge=1, le=100)
    rate_limit_window_minutes: int = Field(default=60, ge=1, le=1440)
    duplicate_window_minutes: int = Field(default=10, ge=1, le=1440)

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
