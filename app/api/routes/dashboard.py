from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.dashboard import DashboardSummaryResponse, RecentActivityResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/admin/dashboard", tags=["Admin - Dashboard"])
service = DashboardService()


@router.get(
    "/summary",
    response_model=StandardResponse[DashboardSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get operational dashboard metrics",
)
def get_dashboard_summary(
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    summary = service.get_summary(db)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Dashboard summary retrieved successfully",
        "data": summary,
    }


@router.get(
    "/recent-activity",
    response_model=StandardResponse[RecentActivityResponse],
    status_code=status.HTTP_200_OK,
    summary="Get recent orders and payments stream",
)
def get_recent_activity(
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    activity = service.get_recent_activity(db)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Recent activity retrieved successfully",
        "data": activity,
    }
