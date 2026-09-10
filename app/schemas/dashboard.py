from typing import List, Any, Dict
from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    today_orders: int = 0
    today_sales: float = 0.0
    pending_payments: int = 0
    pending_orders: int = 0
    total_users: int = 0
    pending_topups: int = 0


class RecentActivityResponse(BaseModel):
    recent_orders: List[Dict[str, Any]] = []
    recent_payments: List[Dict[str, Any]] = []
