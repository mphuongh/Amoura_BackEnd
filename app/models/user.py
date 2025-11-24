# app/models/user.py
import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    """
    Persistent user profile for Amoura.

    Identity:
      - id: MUST match Supabase auth.users.id (UUID from JWT "sub")

    Role:
      - "user" | "admin"
      - "guest" is represented by the absence of a row / missing token.

    This table is *not* responsible for password hashes. Supabase Auth
    stores the password in its own schema. We only mirror identity,
    name, and application role.
    """

    __tablename__ = "users"

    id: uuid.UUID = Field(
        primary_key=True,
        index=True,
        description="Matches Supabase auth.users.id",
    )

    email: str = Field(
        unique=True,
        index=True,
        description="Email from Supabase auth.users",
    )

    # Display name for the user (e.g. customer name)
    name: str = Field(
        max_length=50,
        description="Customer display name; first part of email by default",
    )

    # Application role (not Supabase RLS role)
    role: str = Field(
        default="user",
        index=True,
        description="Application role: user | admin",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )
