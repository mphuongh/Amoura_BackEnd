# app/models/cart.py
import uuid
from datetime import datetime, timezone

from sqlmodel import SQLModel, Field


class CartItem(SQLModel, table=True):
    """
    Shopping cart entry for a user.
    One user cannot have 2 rows for the same product.
    """

    __tablename__ = "cart_items"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        index=True,
    )

    product_id: uuid.UUID = Field(
        foreign_key="products.id",
        index=True,
    )

    quantity: int = Field(
        gt=0,
        description="Must be >= 1",
    )

    snapshot_price: float = Field(
        description="Price when added to cart",
    )

    product_name: str | None = None
    product_hero_image_url: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
