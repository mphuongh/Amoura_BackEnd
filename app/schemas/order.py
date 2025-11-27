# app/schemas/order.py
import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import ConfigDict, field_validator
from sqlmodel import SQLModel, Field

DeliveryWindow = Literal["morning", "afternoon", "evening", "custom"]
OrderStatus = Literal["pending", "confirmed", "shipped", "canceled"]


class OrderCreate(SQLModel):
    """
    Payload for creating an order from the current cart.

    User provides:
      - receiver_name (optional)
      - note (optional)
      - phone_number
      - shipping address
      - delivery date
      - delivery window

    Backend derives:
      - user_id from token
      - status = 'pending'
      - total_amount from cart (with extra 8% tax)
      - items from cart
    """

    model_config = ConfigDict(extra="forbid")

    receiver_name: str | None = None
    phone_number: str
    full_address: str
    province: str
    ward: str
    delivery_date: date
    delivery_window: DeliveryWindow
    note: str | None = None

    @field_validator("full_address", "province", "ward", "phone_number")
    @classmethod
    def not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("field cannot be empty")
        return v

    @field_validator("receiver_name")
    @classmethod
    def normalize_receiver(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        return v or None

    @field_validator("note", mode="before", check_fields=False)
    @classmethod
    def normalize_note(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        return v or None


class OrderRead(SQLModel):
    """
    Lightweight representation of an order (without items).
    """

    id: uuid.UUID
    user_id: uuid.UUID
    receiver_name: str | None
    phone_number: str
    note: str | None
    full_address: str
    province: str
    ward: str
    delivery_date: date
    delivery_window: DeliveryWindow
    status: OrderStatus
    total_amount: float
    created_at: datetime


class OrderItemRead(SQLModel):
    """
    Representation of a single order line item.
    """

    id: uuid.UUID
    order_id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    unit_price: float
    line_total: float


class OrderWithItemsRead(OrderRead):
    """
    Full order view including items.
    """

    items: list[OrderItemRead]
    subtotal: float
    tax_amount: float


class OrderStatusUpdate(SQLModel):
    """
    Admin payload to change order status.
    """

    model_config = ConfigDict(extra="forbid")

    status: OrderStatus
