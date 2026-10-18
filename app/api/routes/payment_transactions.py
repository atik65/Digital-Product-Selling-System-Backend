from datetime import date
from typing import Literal, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schemas.pagination import PaginationParams, PaginatedData
from app.schemas.payment_transaction import PaymentTransactionResponse
from app.schemas.response import StandardResponse
from app.services.payment_transaction_service import PaymentTransactionService

router = APIRouter(tags=["Payment Transactions"])
service = PaymentTransactionService()


@router.get(
    "/admin/payment-transactions",
    response_model=StandardResponse[PaginatedData[PaymentTransactionResponse]],
    status_code=status.HTTP_200_OK,
    summary="History of all successful transactions per payment method",
)
def admin_list_payment_transactions(
    payment_method_id: Optional[int] = None,
    source_type: Optional[Literal["ORDER_PAYMENT", "WALLET_TOPUP"]] = None,
    search: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    pagination: PaginationParams = Depends(),
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    """
    Successful (verified / approved) transactions, newest first.
    `date_from` / `date_to` are inclusive calendar dates in Bangladesh time.
    `search` matches the transaction ID or sender number.
    """
    transactions = service.get_transactions(
        db,
        pagination,
        payment_method_id=payment_method_id,
        source_type=source_type,
        search=search,
        date_from=date_from,
        date_to=date_to,
    )
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment transactions retrieved successfully",
        "data": transactions,
    }
