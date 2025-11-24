# app/models/product.py
import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class Product(SQLModel, table=True):
    """
    Product catalog entry for Amoura.

    Matches ERD:
      - id, name, slug, description, price, stock_on_hand,
        is_active, hero_image_url, created_at
    """

    __tablename__ = "products"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    name: str = Field(
        max_length=100,
        min_length=3,
        index=True,
        description="Display name of the cake/product",
    )

    slug: str = Field(
        max_length=255,
        unique=True,
        index=True,
        description="URL-friendly identifier (unique)",
    )

    description: str | None = Field(
        default=None,
        description="Optional long description / HTML",
    )

    price: float = Field(
        gt=0,
        description="Unit price (e.g. VND)",
    )

    stock_on_hand: int = Field(
        default=0,
        ge=0,
        description="How many units currently in stock",
    )

    is_active: bool = Field(
        default=True,
        index=True,
        description="Whether this product is visible on the storefront",
    )

    hero_image_url: str | None = Field(
        default=None,
        description="Main hero image URL",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )


class ProductImage(SQLModel, table=True):
    """
    Additional gallery images for a product.

    Matches ERD:
      - id, product_id, image_url, sort_order
    """

    __tablename__ = "product_images"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    product_id: uuid.UUID = Field(
        foreign_key="products.id",
        index=True,
        description="FK to products.id",
    )

    image_url: str = Field(
        description="Public URL stored in Supabase Storage",
    )

    sort_order: int = Field(
        default=0,
        ge=0,
        description="Ordering index within the gallery",
    )
