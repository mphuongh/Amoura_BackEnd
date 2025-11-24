# app/services/user_service.py
import uuid

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserRoleUpdate


class UserService:
    """
    Business logic for User.

    Responsibilities:
      - enforce app rules (no email change, role constraints)
      - orchestrate repository operations
      - map domain errors to HTTP errors
    """

    def __init__(self, repo: UserRepository):
        self.repo = repo

    # ----- Self profile -----

    def get_me(self, current_user: User) -> User:
        """Return the current authenticated user."""
        return current_user

    def create_me(
        self,
        session: Session,
        current_user: User,
        payload: UserCreate,
    ) -> User:
        """
        First-time profile completion.

        The profile row is auto-provisioned in `get_current_user`.
        This method only fills editable fields.

        Rules:
          - email cannot be changed via this endpoint
          - only set name if provided
        """
        if payload.email and payload.email != current_user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email cannot be changed",
            )

        if payload.name is not None:
            current_user.name = payload.name

        return self.repo.update(session, current_user)

    def update_me(
        self,
        session: Session,
        current_user: User,
        payload: UserUpdate,
    ) -> User:
        """
        Partial update for profile edits.
        Currently, only `name` is editable.
        """
        if payload.name is not None:
            current_user.name = payload.name

        return self.repo.update(session, current_user)

    # ----- Admin operations -----

    def list_users(self, session: Session, skip: int, limit: int) -> list[User]:
        """List users with pagination (admin only)."""
        return self.repo.list(session, skip=skip, limit=limit)

    def get_user(self, session: Session, user_id: uuid.UUID) -> User:
        """
        Get a user by id (admin only).

        Raises:
            HTTPException(404): if not found.
        """
        user = self.repo.get_by_id(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def update_role(
        self,
        session: Session,
        user_id: uuid.UUID,
        payload: UserRoleUpdate,
    ) -> User:
        """
        Change user's role (admin only).

        Role validation is enforced by the schema (Literal).
        """
        user = self.get_user(session, user_id)
        user.role = payload.role
        return self.repo.update(session, user)

    def delete_user(self, session: Session, user_id: uuid.UUID) -> None:
        """Delete a user (admin only)."""
        user = self.get_user(session, user_id)
        self.repo.delete(session, user)
