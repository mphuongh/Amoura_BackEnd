# app/schemas/product.py
import uuid
from datetime import datetime

from pydantic import ConfigDict, field_validator
from sqlmodel import SQLModel, Field


class ProductBase(SQLModel):
    """
    Shared fields for product read models.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=100, min_length=3)
    slug: str
    description: str | None = None
    price: float = Field(gt=0)
    stock_on_hand: int = Field(default=0, ge=0)
    is_active: bool = True
    hero_image_url: str | None = None
    category: str = Field(
        max_length=50,
        description="Product category (must follow allowed values)"
    )

    @field_validator("name", "slug", "category")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("field cannot be empty")
        return v


class ProductCreate(SQLModel):
    """
    Payload for creating a product.

    - slug is optional: if omitted, generated from `name`.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(max_length=255)
    slug: str | None = None
    description: str | None = None
    price: float = Field(gt=0)
    stock_on_hand: int = Field(default=0, ge=0)
    is_active: bool = True
    category: str = Field(
        max_length=50,
        description="Product category"
    )

    @field_validator("name", "category")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("slug cannot be empty if provided")
        return v


class ProductRead(ProductBase):
    """
    Product representation for clients.
    """

    id: uuid.UUID
    created_at: datetime


class ProductUpdate(SQLModel):
    """
    Partial update payload for products.
    All fields are optional.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=255)
    slug: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    stock_on_hand: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    hero_image_url: str | None = None  # allow manual override if needed
    category: str | None = Field(
        default=None,
        max_length=50,
        description="Updated category if provided"
    )

    @field_validator("name", "category")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("slug cannot be empty")
        return v


class ProductImageRead(SQLModel):
    """
    Read model for gallery images.
    """

    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    product_id: uuid.UUID
    image_url: str
    sort_order: int
