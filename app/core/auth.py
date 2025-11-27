# app/core/auth.py
import uuid
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlmodel import Session, select

from app.core.config import get_settings
from app.database import get_session
from app.models.user import User

settings = get_settings()

# HTTP Bearer scheme:
# - auto_error=False => missing Authorization header will NOT raise immediately
#   so we can support "guest" mode (unauthenticated).
bearer_scheme = HTTPBearer(auto_error=False)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a Supabase access token (JWT).

    Verification:
      - signature (HS256 using SUPABASE_JWT_SECRET)
      - expiration time (exp)
      - audience is NOT verified (Supabase 'aud' may vary)

    Args:
        token: raw JWT from the Authorization header.

    Returns:
        Decoded JWT claims.

    Raises:
        HTTPException(401): if token is invalid/expired.
    """
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.SUPABASE_JWT_ALG],
            options={"verify_aud": False},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def _default_name_from_email(email: str) -> str:
    """
    Derive a default display name from email if the user has not
    completed their profile yet.
    """
    if "@" in email:
        return email.split("@", 1)[0]
    return email


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
) -> User | None:
    """
    Resolve the current user from a Supabase JWT.

    Flow:
      1. If no Authorization header => guest => return None.
      2. Decode JWT => extract 'sub' (auth user id) and 'email'.
      3. Convert 'sub' to UUID to match User.id type.
      4. Find user profile in public.users.
      5. If missing, auto-provision minimal profile.

    Returns:
        User instance if authenticated, else None for guests.

    Raises:
        HTTPException(401): if token is malformed or missing required claims.
    """
    if credentials is None:
        return None  # guest mode

    payload = decode_access_token(credentials.credentials)
    sub = payload.get("sub")
    email = payload.get("email")

    if not sub or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing sub/email",
        )

    # Supabase provides sub as a string; enforce UUID
    try:
        sub_uuid = uuid.UUID(sub)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid sub in token",
        )

    user = session.exec(select(User).where(User.id == sub_uuid)).first()

    # Auto-provision profile if not found yet.
    # Default role = "user" (admin must be manually promoted).
    if user is None:
        user = User(
            id=sub_uuid,
            email=email,
            name=_default_name_from_email(email),
            role="user",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

    return user


def require_auth(user: User | None = Depends(get_current_user)) -> User:
    """
    Enforce authentication.

    If attached to a route, guests (missing/invalid JWT)
    will be rejected with 401.

    Returns:
        The authenticated User.

    Raises:
        HTTPException(401): if user is None.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user


def require_admin(user: User = Depends(require_auth)) -> User:
    """
    Enforce admin role.

    Route is accessible only if:
      - user.role == "admin"

    Returns:
        The authenticated admin User.

    Raises:
        HTTPException(403): if role is not admin.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def require_user(user: User = Depends(require_auth)) -> User:
    """
    Enforce that only normal customers (role='user') can access a route.

    Use this for:
      - cart endpoints
      - checkout endpoints
    Admins will be rejected with 403.
    """
    if user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer access required",
        )
    return user
