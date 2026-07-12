from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mobile_base_url: str = Field(alias="MOBILE_BASE_URL")
    admin_base_url: str = Field(alias="ADMIN_BASE_URL")

    admin_email: str = Field(alias="ADMIN_EMAIL")
    admin_password: str = Field(alias="ADMIN_PASSWORD")

    test_account_email: str = Field(alias="TEST_ACCOUNT_EMAIL")
    test_account_password: str = Field(alias="TEST_ACCOUNT_PASSWORD")

    test_user_password: str = Field("E2eTest#12345", alias="TEST_USER_PASSWORD")
    test_email_domain: str = Field("innopolis.university", alias="TEST_EMAIL_DOMAIN")

    default_timeout_ms: int = Field(15_000, alias="DEFAULT_TIMEOUT_MS")
    navigation_timeout_ms: int = Field(30_000, alias="NAVIGATION_TIMEOUT_MS")
    map_load_timeout_ms: int = Field(5_000, alias="MAP_LOAD_TIMEOUT_MS")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
