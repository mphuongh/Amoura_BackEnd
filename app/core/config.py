# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings loaded from environment.

    Required env vars (.env):
      - SUPABASE_URL
      - SUPABASE_KEY (anon key)
      - DATABASE_URL (Supabase Postgres connection string)
      - SUPABASE_JWT_SECRET (JWT signing secret from Supabase project settings)

    Optional:
      - SUPABASE_SERVICE_ROLE_KEY (only used for admin Supabase client)
    """

    PROJECT_NAME: str = "SmartForm Backend"
    API_V1_STR: str = "/api/v1"

    # Supabase / DB config
    SUPABASE_URL: str
    SUPABASE_KEY: str
    DATABASE_URL: str

    # JWT verification (backend-side)
    SUPABASE_JWT_SECRET: str
    SUPABASE_JWT_ALG: str = "HS256"

    # Service role key bypasses RLS (backend only)
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings loader.
    Ensures we don't re-parse .env on every import / request.
    """
    return Settings()
