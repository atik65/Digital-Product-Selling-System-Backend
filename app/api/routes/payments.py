from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.pagination import PaginationParams, PaginatedData
from app.schemas.payment import (
    PaymentResponse,
    PaymentSubmitRequest,
    PaymentVerifyRequest,
    PaymentRejectRequest,
)
from app.services.payment_service import PaymentService

router = APIRouter(tags=["Payments"])
service = PaymentService()


@router.post(
    "/payments/submit",
    response_model=StandardResponse[PaymentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit manual payment transaction details",
)
def submit_payment(
    body: PaymentSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = service.submit_payment(db, current_user.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Payment submitted successfully. Awaiting admin verification.",
        "data": payment,
    }


@router.get(
    "/payments/order/{order_id}",
    response_model=StandardResponse[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get payment details for an order",
)
def get_order_payment(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = service.get_order_payment(db, order_id, current_user.id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment details retrieved successfully",
        "data": payment,
    }


@router.get(
    "/admin/payments",
    response_model=StandardResponse[PaginatedData[PaymentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List payments for verification",
)
def admin_list_payments(
    status_filter: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    payments = service.get_all_payments(db, pagination, status=status_filter)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payments retrieved successfully",
        "data": payments,
    }


@router.post(
    "/admin/payments/{payment_id}/verify",
    response_model=StandardResponse[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve payment (marks Payment VERIFIED & Order PAID)",
)
def admin_verify_payment(
    payment_id: int,
    body: PaymentVerifyRequest,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    payment = service.verify_payment(db, payment_id, current_admin.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment verified successfully. Order marked as PAID.",
        "data": payment,
    }


@router.post(
    "/admin/payments/{payment_id}/reject",
    response_model=StandardResponse[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Reject payment (reverts Order to PAYMENT_PENDING)",
)
def admin_reject_payment(
    payment_id: int,
    body: PaymentRejectRequest,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    payment = service.reject_payment(db, payment_id, current_admin.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment rejected.",
        "data": payment,
    }
