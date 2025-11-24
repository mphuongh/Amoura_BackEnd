# app/schemas/user.py
import uuid
from datetime import datetime
from typing import Literal

from pydantic import EmailStr, ConfigDict, field_validator
from sqlmodel import SQLModel, Field

# App-level roles. "guest" = no token, so we don't store it here.
Role = Literal["user", "admin"]


class UserBase(SQLModel):
    """
    Shared fields for read models.

    Validation rules:
      - email must be a valid EmailStr
      - name cannot be empty or whitespace
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    name: str = Field(max_length=50)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v


class UserCreate(SQLModel):
    """
    Payload for first-time profile completion (after Supabase sign-up).

    We allow optional email only for cross-check; it must match token email.
    """

    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = None
    name: str | None = Field(default=None, max_length=200)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v


class UserRead(UserBase):
    """Response schema returned to clients."""

    id: uuid.UUID
    role: Role
    created_at: datetime


class UserUpdate(SQLModel):
    """
    Partial profile update for authenticated users.
    Only editable field is `name` here.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=200)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v


class UserRoleUpdate(SQLModel):
    """
    Admin-only role update schema.
    """

    model_config = ConfigDict(extra="forbid")
    role: Role
