# app/schemas/cart.py
import uuid
from datetime import datetime

from sqlmodel import SQLModel, Field


class CartItemBase(SQLModel):
    """
    Base fields for create/update payloads.
    """

    product_id: uuid.UUID
    quantity: int = Field(gt=0)


class CartItemCreate(CartItemBase):
    """
    Payload for adding to cart.
    """

    pass


class CartItemUpdate(SQLModel):
    """
    Payload for updating quantity of a cart item.
    """

    quantity: int = Field(gt=0)


class CartItemRead(SQLModel):
    """
    Read model for a single cart item, including line_total.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    snapshot_price: float
    product_name: str | None = None
    product_hero_image_url: str | None = None
    line_total: float
    created_at: datetime


class CartSummary(SQLModel):
    """
    Full cart response model with totals.
    """

    items: list[CartItemRead]
    total_quantity: int
    total_price: float
