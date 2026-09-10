from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.marketing import (
    BannerResponse,
    BannerCreate,
    BannerUpdate,
    PopupResponse,
    PopupCreate,
    PopupUpdate,
)
from app.services.marketing_service import MarketingService

router = APIRouter(tags=["Marketing (Banners & Popups)"])
service = MarketingService()


# Banners
@router.get(
    "/banners",
    response_model=StandardResponse[List[BannerResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get active banners for homepage display",
)
def get_banners(db: Session = Depends(get_db)):
    banners = service.get_banners(db, active_only=True)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Banners retrieved successfully",
        "data": banners,
    }


@router.get(
    "/admin/banners",
    response_model=StandardResponse[List[BannerResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all banners for admin",
)
def admin_get_banners(
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    banners = service.get_banners(db, active_only=False)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "All banners retrieved successfully",
        "data": banners,
    }


@router.post(
    "/admin/banners",
    response_model=StandardResponse[BannerResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create promotional banner",
)
def create_banner(
    body: BannerCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    banner = service.create_banner(db, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Banner created successfully",
        "data": banner,
    }


@router.put(
    "/admin/banners/{banner_id}",
    response_model=StandardResponse[BannerResponse],
    status_code=status.HTTP_200_OK,
    summary="Update banner",
)
def update_banner(
    banner_id: int,
    body: BannerUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    banner = service.update_banner(db, banner_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Banner updated successfully",
        "data": banner,
    }


@router.delete(
    "/admin/banners/{banner_id}",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete banner",
)
def delete_banner(
    banner_id: int,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    service.delete_banner(db, banner_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Banner deleted successfully",
        "data": {"id": banner_id},
    }


# Popups
@router.get(
    "/popups/active",
    response_model=StandardResponse[Optional[PopupResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get active announcement popup",
)
def get_active_popup(db: Session = Depends(get_db)):
    popup = service.get_active_popup(db)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Active popup retrieved successfully",
        "data": popup,
    }


@router.get(
    "/admin/popups",
    response_model=StandardResponse[List[PopupResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all popups for admin",
)
def admin_get_popups(
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    popups = service.get_all_popups(db)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Popups retrieved successfully",
        "data": popups,
    }


@router.post(
    "/admin/popups",
    response_model=StandardResponse[PopupResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create announcement popup",
)
def create_popup(
    body: PopupCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    popup = service.create_popup(db, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Popup created successfully",
        "data": popup,
    }


@router.put(
    "/admin/popups/{popup_id}",
    response_model=StandardResponse[PopupResponse],
    status_code=status.HTTP_200_OK,
    summary="Update popup",
)
def update_popup(
    popup_id: int,
    body: PopupUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    popup = service.update_popup(db, popup_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Popup updated successfully",
        "data": popup,
    }
