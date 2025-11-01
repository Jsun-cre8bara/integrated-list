import os
from functools import lru_cache
from datetime import timedelta


class Settings:
    """Application configuration loaded from environment variables."""

    PROJECT_NAME: str = "tCATS Stamp Network API"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-development-key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./tcats.db",
    )

    @property
    def access_token_expires(self) -> timedelta:
        return timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)


@lru_cache
def get_settings() -> Settings:
    return Settings()
