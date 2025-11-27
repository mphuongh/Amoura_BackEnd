# app/models/order.py
import uuid
from datetime import datetime, date, timezone

from sqlmodel import SQLModel, Field


class Order(SQLModel, table=True):
    """
    Customer order.

    Matches ERD:
      - id, user_id, full_address, province, ward,
        delivery_date, delivery_window, status,
        total_amount, created_at, receiver_name,
        phone_number, note
    """

    __tablename__ = "orders"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    user_id: uuid.UUID = Field(
        foreign_key="users.id",
        index=True,
    )

    # New fields
    receiver_name: str | None = Field(
        default=None,
        description="Name of the person receiving the order (optional)",
    )
    phone_number: str = Field(
        description="Contact phone number for delivery",
    )
    note: str | None = Field(
        default=None,
        description="Optional note / special instructions",
    )

    full_address: str = Field(
        description="Full delivery address",
    )
    province: str = Field(
        description="Province / city",
    )
    ward: str = Field(
        description="Ward / communes",
    )

    delivery_date: date = Field(
        description="Requested delivery date",
    )

    # morning | afternoon | evening | custom
    delivery_window: str = Field(
        description="Delivery window identifier",
    )

    # pending | confirmed | shipped | canceled
    status: str = Field(
        default="pending",
        index=True,
        description="Order status lifecycle",
    )

    # Total including tax (8%)
    total_amount: float = Field(
        description="Final amount for this order (including tax)",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )


class OrderItem(SQLModel, table=True):
    """
    Line item inside an order.

    Matches ERD:
      - id, order_id, product_id, quantity, unit_price
    """

    __tablename__ = "order_items"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
    )

    order_id: uuid.UUID = Field(
        foreign_key="orders.id",
        index=True,
    )

    product_id: uuid.UUID = Field(
        foreign_key="products.id",
        index=True,
    )

    quantity: int = Field(
        gt=0,
        description="Quantity ordered (>=1)",
    )

    # Pre-tax price at time of order
    unit_price: float = Field(
        description="Unit price at time of order (pre-tax)",
    )
