from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.payment_method import (
    PaymentMethodResponse,
    PaymentMethodCreate,
    PaymentMethodUpdate,
)
from app.services.payment_method_service import PaymentMethodService

router = APIRouter(tags=["Payment Methods"])
service = PaymentMethodService()


@router.get(
    "/payment-methods",
    response_model=StandardResponse[List[PaymentMethodResponse]],
    status_code=status.HTTP_200_OK,
    summary="List active payment methods (bKash, Nagad, Rocket)",
)
def get_payment_methods(db: Session = Depends(get_db)):
    methods = service.get_payment_methods(db, active_only=True)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment methods retrieved successfully",
        "data": methods,
    }


@router.get(
    "/admin/payment-methods",
    response_model=StandardResponse[List[PaymentMethodResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all payment methods for admin",
)
def admin_get_payment_methods(
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    methods = service.get_payment_methods(db, active_only=False)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "All payment methods retrieved successfully",
        "data": methods,
    }


@router.post(
    "/admin/payment-methods",
    response_model=StandardResponse[PaymentMethodResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create payment method channel",
)
def create_payment_method(
    body: PaymentMethodCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    method = service.create_payment_method(db, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Payment method created successfully",
        "data": method,
    }


@router.put(
    "/admin/payment-methods/{method_id}",
    response_model=StandardResponse[PaymentMethodResponse],
    status_code=status.HTTP_200_OK,
    summary="Update payment method channel",
)
def update_payment_method(
    method_id: int,
    body: PaymentMethodUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    method = service.update_payment_method(db, method_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment method updated successfully",
        "data": method,
    }


@router.delete(
    "/admin/payment-methods/{method_id}",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete payment method channel",
)
def delete_payment_method(
    method_id: int,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    service.delete_payment_method(db, method_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment method deleted successfully",
        "data": {"id": method_id},
    }
