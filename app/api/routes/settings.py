from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.setting import SiteSettingResponse, SiteSettingUpdate
from app.services.setting_service import SettingService

router = APIRouter(tags=["Site Settings"])
service = SettingService()


@router.get(
    "/settings",
    response_model=StandardResponse[SiteSettingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get public site settings",
)
def get_site_settings(db: Session = Depends(get_db)):
    settings_obj = service.get_settings(db)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Site settings retrieved successfully",
        "data": settings_obj,
    }


@router.put(
    "/admin/settings",
    response_model=StandardResponse[SiteSettingResponse],
    status_code=status.HTTP_200_OK,
    summary="Update site settings",
)
def update_site_settings(
    body: SiteSettingUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    updated = service.update_settings(db, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Site settings updated successfully",
        "data": updated,
    }
