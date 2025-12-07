# app/routers/admin_stats.py
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.auth import require_admin
from app.database import get_session
from app.repositories.stats_repo import StatsRepository
from app.schemas.stats import AdminDashboardStats
from app.services.stats_service import StatsService

router = APIRouter(prefix="/admin/stats", tags=["Admin Stats"])

repo = StatsRepository()
service = StatsService(repo)


@router.get(
    "",
    response_model=AdminDashboardStats,
    dependencies=[Depends(require_admin)],
)
def get_admin_dashboard_stats(
    year: int | None = None,
    month: int | None = None,
    session: Session = Depends(get_session),
):
    """
    Aggregated statistics for the admin dashboard.

    Query params (optional):
      - year: integer, defaults to current year
      - month: integer 1–12, defaults to current month

    Only accessible to users with role='admin'.
    """
    return service.get_admin_dashboard_stats(
        session=session,
        year=year,
        month=month,
    )
