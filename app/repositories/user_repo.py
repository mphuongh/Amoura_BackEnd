# app/repositories/user_repo.py
import uuid

from sqlmodel import Session, select

from app.models.user import User


class UserRepository:
    """
    Data access layer for User.

    Responsibilities:
      - Pure DB operations (CRUD + queries)
      - No FastAPI, no HTTP, no business logic
    """

    # ----- Basic CRUD -----

    def get_by_id(self, session: Session, user_id: uuid.UUID) -> User | None:
        """Return a User by primary key, or None if not found."""
        return session.get(User, user_id)

    def get_by_email(self, session: Session, email: str) -> User | None:
        """Return a User by unique email, or None if not found."""
        stmt = select(User).where(User.email == email)
        return session.exec(stmt).first()

    def list(self, session: Session, skip: int = 0, limit: int = 50) -> list[User]:
        """
        Paginated user listing.

        Args:
            skip: offset rows (for paging)
            limit: max number of rows returned

        Returns:
            List[User]
        """
        stmt = select(User).offset(skip).limit(limit)
        return session.exec(stmt).all()

    def create(self, session: Session, user: User) -> User:
        """Insert a new User and return the persisted row."""
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def update(self, session: Session, user: User) -> User:
        """Persist changes to an existing User."""
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    def delete(self, session: Session, user: User) -> None:
        """Delete a User."""
        session.delete(user)
        session.commit()
