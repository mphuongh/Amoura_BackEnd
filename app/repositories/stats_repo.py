# app/repositories/stats_repo.py
from typing import List, Tuple

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.user import User
from app.models.order import Order, OrderItem
from app.models.product import Product


class StatsRepository:
    """
    Read-only aggregated queries for admin dashboard.
    """

    def count_customers(self, session: Session) -> int:
        stmt = select(func.count()).select_from(User).where(User.role == "user")
        # SQLModel's Session.exec() -> ScalarResult -> use .one()
        value = session.exec(stmt).one()
        return int(value or 0)

    def count_orders(self, session: Session) -> int:
        stmt = select(func.count()).select_from(Order)
        value = session.exec(stmt).one()
        return int(value or 0)

    def total_revenue(self, session: Session) -> float:
        """
        Sum of total_amount for all non-canceled orders.
        """
        stmt = (
            select(func.coalesce(func.sum(Order.total_amount), 0.0))
            .where(Order.status != "canceled")
        )
        value = session.exec(stmt).one()
        return float(value or 0.0)

    def daily_sales(
        self,
        session: Session,
        year: int,
        month: int,
    ) -> list[tuple]:
        """
        Aggregate revenue per day for a given month/year using Order.created_at.
        Excludes canceled orders.
        """
        day_expr = func.date_trunc("day", Order.created_at)

        stmt = (
            select(
                day_expr.label("day"),
                func.coalesce(func.sum(Order.total_amount), 0.0).label("revenue"),
                func.count(Order.id).label("order_count"),
            )
            .where(
                Order.status != "canceled",
                func.extract("year", Order.created_at) == year,
                func.extract("month", Order.created_at) == month,
            )
            .group_by(day_expr)
            .order_by(day_expr)
        )

        return list(session.exec(stmt).all())

    def top_products(
        self,
        session: Session,
        limit: int = 5,
    ) -> list[tuple]:
        """
        Top products by quantity sold across all non-canceled orders.
        """
        qty_sum = func.coalesce(func.sum(OrderItem.quantity), 0)
        revenue_sum = func.coalesce(
            func.sum(OrderItem.quantity * OrderItem.unit_price),
            0.0,
        )

        stmt = (
            select(
                OrderItem.product_id,
                Product.name,
                qty_sum.label("total_quantity"),
                revenue_sum.label("total_revenue"),
            )
            .join(Order, Order.id == OrderItem.order_id)
            .join(Product, Product.id == OrderItem.product_id)
            .where(Order.status != "canceled")
            .group_by(OrderItem.product_id, Product.name)
            .order_by(qty_sum.desc())
            .limit(limit)
        )

        return list(session.exec(stmt).all())

    def latest_orders(
        self,
        session: Session,
        limit: int = 5,
    ) -> list[Order]:
        """
        Latest N orders by created_at (any status).
        """
        stmt = (
            select(Order)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(session.exec(stmt).all())
