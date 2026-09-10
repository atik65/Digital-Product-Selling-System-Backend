from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.response import StandardResponse
from app.schemas.health import HealthResponse
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=StandardResponse[HealthResponse],
    summary="Health check endpoint for monitoring service and database status",
)
def health_check(response: Response, db: Session = Depends(get_db)):
    db_status = "connected"
    is_healthy = True

    try:
        # Ping the database
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
        is_healthy = False

    current_time = datetime.now(timezone.utc).isoformat()

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "success": False,
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
            "message": "Service is degraded: database unreachable",
            "data": {
                "status": "unhealthy",
                "database": db_status,
                "version": settings.VERSION,
                "timestamp": current_time,
            },
        }

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Service is healthy",
        "data": {
            "status": "healthy",
            "database": db_status,
            "version": settings.VERSION,
            "timestamp": current_time,
        },
    }
