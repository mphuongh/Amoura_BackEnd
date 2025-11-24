# app/database.py
from sqlmodel import SQLModel, create_engine, Session

from app.core.config import get_settings

settings = get_settings()

# Supabase Postgres connection; require SSL in cloud.
engine = create_engine(
    settings.DATABASE_URL + "?sslmode=require",
    echo=True,
    pool_pre_ping=True,
)


def create_db_and_tables() -> None:
    """
    Create tables if they do not exist.

    Called on app startup.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    FastAPI dependency that yields a SQLModel Session.

    Usage:
        def endpoint(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session
