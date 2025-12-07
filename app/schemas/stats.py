# app/schemas/stats.py
import uuid
from datetime import date, datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel

from app.schemas.order import OrderStatus


class DailySales(SQLModel):
    """
    Revenue per day for a given month/year.
    """
    model_config = ConfigDict(extra="forbid")

    date: date
    total_revenue: float
    order_count: int


class TopProduct(SQLModel):
    """
    Aggregated stats for top-selling products.
    """
    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    name: str
    total_quantity: int
    total_revenue: float


class LatestOrderSummary(SQLModel):
    """
    Lightweight info for last N orders.
    """
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID
    receiver_name: str | None
    total_amount: float
    status: OrderStatus


class AdminDashboardStats(SQLModel):
    """
    Full payload for admin dashboard.
    """
    model_config = ConfigDict(extra="forbid")

    total_customers: int
    total_orders: int
    total_revenue: float
    daily_sales: list[DailySales]
    top_products: list[TopProduct]
    latest_orders: list[LatestOrderSummary]
