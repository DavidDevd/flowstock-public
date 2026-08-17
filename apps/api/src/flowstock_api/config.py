from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FLOWSTOCK_",
        extra="ignore",
    )

    service_name: str = "flowstock-api"
    environment: Literal["development", "acceptance", "pilot"] = "development"
    database_url: str
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    cors_origins: str = ""
    otel_enabled: bool = False
    otel_exporter_endpoint: str | None = None
    session_idle_minutes: int = 15
    session_absolute_hours: int = 12
    session_cookie_secure: bool = False
    secret_hash_key: str
    data_encryption_key: str

    @field_validator("database_url")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError("FLOWSTOCK_DATABASE_URL must use PostgreSQL")
        return value

    @field_validator("secret_hash_key", "data_encryption_key")
    @classmethod
    def require_strong_secret_hash_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("security keys must contain at least 32 characters")
        return value

    @property
    def allowed_host_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_hosts.split(",") if item.strip()]

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def docs_enabled(self) -> bool:
        return self.environment != "pilot"


@lru_cache
def get_settings() -> Settings:
    return Settings()
