from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.coupon import (
    CouponResponse,
    CouponCreate,
    CouponUpdate,
    CouponValidateRequest,
    CouponValidateResponse,
)
from app.services.coupon_service import CouponService
from app.services.package_service import PackageService

router = APIRouter(tags=["Coupons"])
coupon_service = CouponService()
package_service = PackageService()


@router.post(
    "/coupons/validate",
    response_model=StandardResponse[CouponValidateResponse],
    status_code=status.HTTP_200_OK,
    summary="Validate coupon against a package",
)
def validate_coupon(
    body: CouponValidateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    package = package_service.get_by_id(db, body.package_id)
    subtotal = round(package.price * body.quantity, 2)
    discount, coupon = coupon_service.validate_and_calculate_discount(
        db, body.code, subtotal, user_id=current_user.id
    )

    data = CouponValidateResponse(
        valid=True,
        code=coupon.code,
        discount_type=coupon.type,
        discount_amount=discount,
        message=f"Coupon applied! You save {discount} BDT",
    )
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Coupon is valid",
        "data": data,
    }


@router.get(
    "/admin/coupons",
    response_model=StandardResponse[List[CouponResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all coupons for admin",
)
def admin_list_coupons(
    is_active: Optional[bool] = None,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    coupons = coupon_service.get_coupons(db, is_active=is_active)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Coupons retrieved successfully",
        "data": coupons,
    }


@router.post(
    "/admin/coupons",
    response_model=StandardResponse[CouponResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create coupon",
)
def create_coupon(
    body: CouponCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    coupon = coupon_service.create_coupon(db, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Coupon created successfully",
        "data": coupon,
    }


@router.put(
    "/admin/coupons/{coupon_id}",
    response_model=StandardResponse[CouponResponse],
    status_code=status.HTTP_200_OK,
    summary="Update coupon",
)
def update_coupon(
    coupon_id: int,
    body: CouponUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    coupon = coupon_service.update_coupon(db, coupon_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Coupon updated successfully",
        "data": coupon,
    }


@router.delete(
    "/admin/coupons/{coupon_id}",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete coupon",
)
def delete_coupon(
    coupon_id: int,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    coupon_service.delete_coupon(db, coupon_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Coupon deleted successfully",
        "data": {"id": coupon_id},
    }
