# app/services/stats_service.py
from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session

from app.repositories.stats_repo import StatsRepository
from app.schemas.stats import (
    AdminDashboardStats,
    DailySales,
    LatestOrderSummary,
    TopProduct,
)


class StatsService:
    """
    Orchestrates aggregated admin dashboard statistics.
    """

    def __init__(self, repo: StatsRepository):
        self.repo = repo

    def get_admin_dashboard_stats(
        self,
        session: Session,
        year: int | None = None,
        month: int | None = None,
        top_n_products: int = 5,
        latest_n_orders: int = 5,
    ) -> AdminDashboardStats:
        # Default to current month/year if not provided
        today = datetime.utcnow().date()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        if not 1 <= month <= 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="month must be between 1 and 12",
            )

        total_customers = self.repo.count_customers(session)
        total_orders = self.repo.count_orders(session)
        total_revenue = self.repo.total_revenue(session)

        # Daily sales
        daily_rows = self.repo.daily_sales(session, year=year, month=month)
        daily_sales: list[DailySales] = []
        for day_ts, revenue, order_count in daily_rows:
            # date_trunc('day', ...) returns a datetime
            day = day_ts.date()
            daily_sales.append(
                DailySales(
                    date=day,
                    total_revenue=float(revenue or 0.0),
                    order_count=int(order_count or 0),
                )
            )

        # Top products
        top_rows = self.repo.top_products(session, limit=top_n_products)
        top_products: list[TopProduct] = []
        for product_id, name, total_quantity, product_revenue in top_rows:
            top_products.append(
                TopProduct(
                    product_id=product_id,
                    name=name,
                    total_quantity=int(total_quantity or 0),
                    total_revenue=float(product_revenue or 0.0),
                )
            )

        # Latest orders
        latest_order_models = self.repo.latest_orders(session, limit=latest_n_orders)
        latest_orders: list[LatestOrderSummary] = []
        for o in latest_order_models:
            latest_orders.append(
                LatestOrderSummary(
                    id=o.id,
                    created_at=o.created_at,
                    user_id=o.user_id,
                    receiver_name=o.receiver_name,
                    total_amount=o.total_amount,
                    status=o.status,  # string compatible with OrderStatus Literal
                )
            )

        return AdminDashboardStats(
            total_customers=int(total_customers or 0),
            total_orders=int(total_orders or 0),
            total_revenue=float(total_revenue or 0.0),
            daily_sales=daily_sales,
            top_products=top_products,
            latest_orders=latest_orders,
        )
