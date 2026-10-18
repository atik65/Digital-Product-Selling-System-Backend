from datetime import date, datetime, timezone
from typing import Optional, Union
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.models.payment_method import PaymentMethod
from app.models.payment_transaction import PaymentTransaction
from app.models.topup import TopUp
from app.repositories.payment_transaction_repository import (
    PaymentTransactionRepository,
)
from app.schemas.pagination import PaginationParams
from app.schemas.payment_method import PaymentMethodAdminResponse
from app.utils.period import day_range_utc, month_range_utc

ORDER_PAYMENT = "ORDER_PAYMENT"
WALLET_TOPUP = "WALLET_TOPUP"


class PaymentTransactionService:
    def __init__(self):
        self.repo = PaymentTransactionRepository()

    def _record(
        self,
        db: Session,
        source: Union[Payment, TopUp],
        source_type: str,
        fallback_sender_number: Optional[str],
        commit: bool,
    ) -> PaymentTransaction:
        return self.repo.record(
            db,
            {
                "payment_method_id": source.payment_method_id,
                "source_type": source_type,
                "source_id": source.id,
                "user_id": source.user_id,
                "transaction_id": source.transaction_id,
                "sender_number": source.sender_number or fallback_sender_number,
                "amount": source.amount,
                "transaction_at": datetime.now(timezone.utc),
            },
            commit=commit,
        )

    def record_payment_success(
        self,
        db: Session,
        payment: Payment,
        fallback_sender_number: Optional[str] = None,
        commit: bool = True,
    ) -> PaymentTransaction:
        """Call when an order payment becomes VERIFIED."""
        return self._record(db, payment, ORDER_PAYMENT, fallback_sender_number, commit)

    def record_topup_success(
        self,
        db: Session,
        topup: TopUp,
        fallback_sender_number: Optional[str] = None,
        commit: bool = True,
    ) -> PaymentTransaction:
        """Call when a wallet top-up becomes APPROVED."""
        return self._record(db, topup, WALLET_TOPUP, fallback_sender_number, commit)

    def revoke_payment(self, db: Session, payment: Payment) -> None:
        """Call when a previously verified payment is rejected."""
        self.repo.revoke(db, ORDER_PAYMENT, payment.id)

    def attach_usage(
        self, db: Session, methods: list[PaymentMethod]
    ) -> list[PaymentMethodAdminResponse]:
        """Builds admin responses with today's / this month's transaction counts."""
        daily = self.repo.count_by_method(db, *day_range_utc())
        monthly = self.repo.count_by_method(db, *month_range_utc())

        results = []
        for method in methods:
            daily_count = daily.get(method.id, 0)
            monthly_count = monthly.get(method.id, 0)
            daily_limit = method.daily_transaction_limit
            monthly_limit = method.monthly_transaction_limit
            results.append(
                PaymentMethodAdminResponse.model_validate(method).model_copy(
                    update={
                        "daily_transaction_count": daily_count,
                        "monthly_transaction_count": monthly_count,
                        "daily_remaining": (
                            max(daily_limit - daily_count, 0)
                            if daily_limit is not None
                            else None
                        ),
                        "monthly_remaining": (
                            max(monthly_limit - monthly_count, 0)
                            if monthly_limit is not None
                            else None
                        ),
                    }
                )
            )
        return results

    def get_transactions(
        self,
        db: Session,
        pagination: PaginationParams,
        payment_method_id: Optional[int] = None,
        source_type: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ):
        return self.repo.get_all(
            db,
            pagination,
            payment_method_id=payment_method_id,
            source_type=source_type,
            search=search,
            date_from=date_from,
            date_to=date_to,
        )
