# app/core/supabase_client.py
from functools import lru_cache
from supabase import create_client, Client

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def supabase_public() -> Client:
    """
    Create a Supabase client with the anon/public key.

    Use cases:
      - calling public edge functions
      - reading public buckets
      - verifying tokens via Supabase endpoints (if needed later)

    Note: This client still respects RLS.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


@lru_cache
def supabase_admin() -> Client:
    """
    Create a Supabase client with the service role key.

    Use cases:
      - uploading to private buckets
      - admin Auth operations
      - any operation that needs to bypass RLS

    WARNING:
      - Never expose service role key to frontend.
      - Only backend should call this.

    Raises:
        RuntimeError: if SUPABASE_SERVICE_ROLE_KEY is not set.
    """
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY in .env")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
