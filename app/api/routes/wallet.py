from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.pagination import PaginationParams, PaginatedData
from app.schemas.wallet import (
    WalletResponse,
    WalletTransactionResponse,
    WalletAdjustRequest,
)
from app.schemas.topup import (
    TopUpResponse,
    TopUpCreateRequest,
    TopUpReviewRequest,
)
from app.services.wallet_service import WalletService
from app.services.topup_service import TopUpService

router = APIRouter(tags=["Wallet & Top-Ups"])
wallet_service = WalletService()
topup_service = TopUpService()


# ==========================================
# 1. Customer Wallet Operations
# ==========================================

@router.get(
    "/wallet/me",
    response_model=StandardResponse[WalletResponse],
    status_code=status.HTTP_200_OK,
    summary="Get customer wallet balance",
)
def get_my_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet = wallet_service.get_user_wallet(db, current_user.id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Wallet retrieved successfully",
        "data": wallet,
    }


@router.get(
    "/wallet/transactions",
    response_model=StandardResponse[PaginatedData[WalletTransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get customer wallet transaction history",
)
def get_wallet_transactions(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transactions = wallet_service.get_transactions(db, current_user.id, pagination)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Transactions retrieved successfully",
        "data": transactions,
    }


@router.post(
    "/orders/{order_number}/pay-with-wallet",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Pay for order directly using wallet balance",
)
def pay_order_with_wallet(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = wallet_service.pay_order_with_wallet(db, current_user.id, order_number)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Order paid successfully using wallet balance",
        "data": result,
    }


@router.post(
    "/wallet/topup",
    response_model=StandardResponse[TopUpResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit wallet funding top-up request",
)
def submit_topup(
    body: TopUpCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topup = topup_service.submit_topup(db, current_user.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Top-up request submitted. Awaiting admin approval.",
        "data": topup,
    }


@router.get(
    "/wallet/topups/me",
    response_model=StandardResponse[List[TopUpResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get customer top-up request history",
)
def get_my_topups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topups = topup_service.get_user_topups(db, current_user.id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Top-up requests retrieved successfully",
        "data": topups,
    }


# ==========================================
# 2. Admin Wallet & Top-Up Operations
# ==========================================

@router.get(
    "/admin/topups",
    response_model=StandardResponse[PaginatedData[TopUpResponse]],
    status_code=status.HTTP_200_OK,
    summary="List top-up requests for admin review",
)
def admin_list_topups(
    status_filter: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    topups = topup_service.get_all_topups(db, pagination, status=status_filter)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Top-up requests retrieved successfully",
        "data": topups,
    }


@router.post(
    "/admin/topups/{topup_id}/approve",
    response_model=StandardResponse[TopUpResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve top-up and atomically credit customer wallet",
)
def admin_approve_topup(
    topup_id: int,
    body: TopUpReviewRequest,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    topup = topup_service.approve_topup(db, topup_id, current_admin.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Top-up approved and customer wallet credited",
        "data": topup,
    }


@router.post(
    "/admin/topups/{topup_id}/reject",
    response_model=StandardResponse[TopUpResponse],
    status_code=status.HTTP_200_OK,
    summary="Reject top-up request",
)
def admin_reject_topup(
    topup_id: int,
    body: TopUpReviewRequest,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    topup = topup_service.reject_topup(db, topup_id, current_admin.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Top-up request rejected",
        "data": topup,
    }


@router.post(
    "/admin/wallets/{user_id}/adjust",
    response_model=StandardResponse[WalletResponse],
    status_code=status.HTTP_200_OK,
    summary="Admin manual balance credit or debit adjustment",
)
def admin_adjust_balance(
    user_id: int,
    body: WalletAdjustRequest,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    wallet = wallet_service.admin_adjust_balance(db, user_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Wallet balance adjusted successfully",
        "data": wallet,
    }
