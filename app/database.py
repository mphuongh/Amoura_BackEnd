# app/database.py
from sqlmodel import SQLModel, create_engine, Session

from app.core.config import get_settings

settings = get_settings()

# ---------------------------------------------------------
# Supabase Postgres connection (via pooler)
#
# - sslmode=require   : enforce SSL when running in the cloud
# - pool_size=1       : keep only 1 connection to the Supabase pooler
# - max_overflow=0    : do not open extra connections beyond the pool
# - pool_pre_ping=True: validate connections before using them
#
# Reason:
# Supabase Session mode limits the number of clients. If each backend
# process opens many connections (SQLAlchemy default pool_size 5+),
# you can easily hit:
#   "MaxClientsInSessionMode: max clients reached"
# ---------------------------------------------------------

db_url = settings.DATABASE_URL

# Append sslmode=require if it is not already present
if "sslmode=" not in db_url:
    if "?" in db_url:
        db_url = db_url + "&sslmode=require"
    else:
        db_url = db_url + "?sslmode=require"

engine = create_engine(
    db_url,
    echo=False,        # set to True if you want to debug SQL queries
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0,
)


def create_db_and_tables() -> None:
    """
    Create all tables defined in SQLModel metadata if they do not exist.

    This is called once on application startup.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    FastAPI dependency that yields a SQLModel Session.

    Usage:

        from fastapi import Depends

        @router.get("/example")
        def example_endpoint(session: Session = Depends(get_session)):
            ...
    """
    with Session(engine) as session:
        yield session
