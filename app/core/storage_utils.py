# app/core/storage_utils.py
import uuid

from app.core.supabase_client import supabase_admin

supabase = supabase_admin()

BUCKET = "assets"


def upload_to_storage(path: str, file_bytes: bytes) -> str:
    """
    Upload a file to Supabase Storage and return its public URL.

    If a file already exists at this path, it will be overwritten
    thanks to the 'upsert' option.
    Upload raw bytes to Supabase Storage and return a public URL.

    Args:
        path: Full object path inside the bucket.
              Example: "users/user_<uuid>/avatar.png"
        file_bytes: File content in bytes.

    Returns:
        Public URL to the uploaded file.

    Raises:
        Any exception raised by Supabase client if upload fails.
    """
    supabase.storage.from_(BUCKET).upload(path, file_bytes, {"upsert": "true"})
    return supabase.storage.from_(BUCKET).get_public_url(path)


def delete_from_storage(path: str) -> None:
    """
    Delete a file from Supabase Storage by its object path.

    Example path (relative to bucket):
        'users/user_<uuid>/avatar.png'
    """
    # Supabase Python client expects a list of paths. :contentReference[oaicite:0]{index=0}
    supabase.storage.from_(BUCKET).remove([path])


def extract_path_from_public_url(url: str) -> str | None:
    """
    Given a public URL, extract the object path relative to the bucket.

    Example:
        https://<proj>.supabase.co/storage/v1/object/public/assets/users/u/avatar.png
        -> 'users/u/avatar.png'
    """
    marker = f"/storage/v1/object/public/{BUCKET}/"
    idx = url.find(marker)
    if idx == -1:
        return None
    return url[idx + len(marker) :]


def delete_public_url(url: str) -> None:
    """
    Convenience helper: delete a file by its public URL.
    No-op if the URL does not belong to this bucket.
    """
    path = extract_path_from_public_url(url)
    if path:
        delete_from_storage(path)


def generate_filename(ext: str) -> str:
    """
    Generate a random filename using UUID4.

    Args:
        ext: File extension without dot (e.g. "png", "jpg")

    Returns:
        A filename like "<uuid4>.png"
    """
    return f"{uuid.uuid4()}.{ext}"
