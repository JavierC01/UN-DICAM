from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


VERSION = "1.0.0"


class Settings(BaseSettings):
    PROJECT_NAME: str = "UN-DICAM Backend"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["*"]

    DATABASE_URL: str = Field(default="postgresql+psycopg://undicam:undicam@db:5432/undicam")
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/1")
    STORAGE_DIR: str = "storage"

    # Obligatoria: sin ella la API no arranca. Generala con: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = Field(min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    MAX_UPLOAD_MB: int = 500
    # Commit del codigo, para los metadatos de reproducibilidad (en Docker no hay .git; pasarlo por .env).
    GIT_COMMIT: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
