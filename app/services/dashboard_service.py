from sqlalchemy.orm import Session
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardSummaryResponse, RecentActivityResponse


class DashboardService:
    def __init__(self):
        self.repo = DashboardRepository()

    def get_summary(self, db: Session) -> DashboardSummaryResponse:
        data = self.repo.get_summary(db)
        return DashboardSummaryResponse(**data)

    def get_recent_activity(self, db: Session) -> RecentActivityResponse:
        data = self.repo.get_recent_activity(db)
        return RecentActivityResponse(**data)
