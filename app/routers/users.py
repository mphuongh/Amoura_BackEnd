# app/routers/users.py
import uuid

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.auth import require_auth, require_admin
from app.database import get_session
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserRead, UserCreate, UserUpdate, UserRoleUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

repo = UserRepository()
service = UserService(repo)


# -------- Self profile --------


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(require_auth)):
    """
    Return the authenticated user's profile.

    Auth:
      - Requires valid Supabase JWT.
    """
    return service.get_me(current_user)


@router.post("/me", response_model=UserRead)
def create_or_update_me(
    payload: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """
    First-time profile completion.

    The user profile row is auto-created on first request (auth dependency),
    with default name derived from email and role="user".

    This route lets the user set or override their `name`.

    Auth:
      - Requires valid Supabase JWT.
    """
    return service.create_me(session, current_user, payload)


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_auth),
):
    """
    Update the authenticated user's profile (partial update).

    Currently, only `name` is editable.

    Auth:
      - Requires valid Supabase JWT.
    """
    return service.update_me(session, current_user, payload)


# -------- Admin endpoints --------


@router.get(
    "",
    response_model=list[UserRead],
    dependencies=[Depends(require_admin)],
)
def list_users(
    session: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 50,
):
    """
    List all users (admin only).

    Pagination via skip/limit.
    """
    return service.list_users(session, skip, limit)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_admin)],
)
def get_user(
    user_id: uuid.UUID,
    session: Session = Depends(get_session),
):
    """
    Get a specific user by id (admin only).
    """
    return service.get_user(session, user_id)


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    dependencies=[Depends(require_admin)],
)
def change_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    session: Session = Depends(get_session),
):
    """
    Update a user's role (admin only).

    Allowed roles: user, admin.
    Guests are anonymous and don't have rows.
    """
    return service.update_role(session, user_id, payload)
