from typing import List
from sqlalchemy.orm import Session
from app.repositories.topup_repository import TopUpRepository
from app.repositories.wallet_repository import WalletRepository
from app.repositories.payment_method_repository import PaymentMethodRepository
from app.models.topup import TopUp
from app.schemas.topup import TopUpCreateRequest, TopUpReviewRequest
from app.schemas.pagination import PaginationParams
from app.core.exceptions import NotFoundException, ValidationException


class TopUpService:
    def __init__(self):
        self.topup_repo = TopUpRepository()
        self.wallet_repo = WalletRepository()
        self.method_repo = PaymentMethodRepository()

    def submit_topup(self, db: Session, user_id: int, req: TopUpCreateRequest) -> TopUp:
        if req.amount <= 0:
            raise ValidationException(
                "Top-up amount must be strictly greater than zero"
            )

        method = self.method_repo.get_by_id(db, req.payment_method_id)
        if not method or not method.is_active:
            raise NotFoundException("Invalid or inactive payment method")

        data = {
            "user_id": user_id,
            "payment_method_id": method.id,
            "amount": req.amount,
            "transaction_id": req.transaction_id.strip(),
            "sender_number": req.sender_number.strip(),
            "status": "PENDING",
        }
        topup = self.topup_repo.create(db, data)

        # Check if SMS already arrived for this transaction
        from app.services.sms_reconciliation_service import SmsReconciliationService
        from datetime import datetime, timezone

        sms_service = SmsReconciliationService()
        matched_sms = sms_service.check_and_match_unclaimed(
            db,
            transaction_id=topup.transaction_id,
            required_amount=topup.amount,
            entity_type="WALLET_TOPUP",
            entity_id=topup.id,
        )
        if matched_sms:
            topup.status = "APPROVED"
            topup.verified_at = datetime.now(timezone.utc)
            topup.admin_note = (
                f"Auto-approved instantly via SMS ({matched_sms.provider})"
            )
            wallet = self.wallet_repo.get_by_user_id(db, user_id, for_update=True)
            if not wallet:
                wallet = self.wallet_repo.create_wallet(db, user_id)
            self.wallet_repo.update_balance_with_transaction(
                db,
                wallet=wallet,
                amount=topup.amount,
                tx_type="credit",
                reference_type="topup",
                description=f"Wallet TopUp via {matched_sms.provider} (TrxID: {topup.transaction_id})",
            )
            db.commit()
            db.refresh(topup)

        return topup

    def get_user_topups(self, db: Session, user_id: int) -> List[TopUp]:
        return self.topup_repo.get_user_topups(db, user_id)

    def get_all_topups(
        self, db: Session, pagination: PaginationParams, status: str = None
    ):
        return self.topup_repo.get_all(db, pagination, status)

    def approve_topup(
        self, db: Session, topup_id: int, admin_id: int, req: TopUpReviewRequest
    ) -> TopUp:
        topup = self.topup_repo.get_by_id(db, topup_id)
        if not topup:
            raise NotFoundException(f"Top-up with id {topup_id} not found")
        if topup.status != "PENDING":
            raise ValidationException(
                f"Cannot approve top-up that is already in '{topup.status}' status"
            )

        # 1. Update top-up status to APPROVED
        updated_topup = self.topup_repo.update_status(
            db, topup, status="APPROVED", admin_id=admin_id, note=req.admin_note
        )

        # 2. Atomically credit customer wallet
        wallet = self.wallet_repo.get_by_user_id(db, topup.user_id, for_update=True)
        if not wallet:
            wallet = self.wallet_repo.create_wallet(db, topup.user_id)

        self.wallet_repo.update_balance_with_transaction(
            db,
            wallet=wallet,
            amount=topup.amount,
            tx_type="TOPUP",
            reference_type="topup",
            reference_id=str(topup.id),
            description=f"Wallet Top-Up approved (TRX: {topup.transaction_id})",
        )

        return updated_topup

    def reject_topup(
        self, db: Session, topup_id: int, admin_id: int, req: TopUpReviewRequest
    ) -> TopUp:
        topup = self.topup_repo.get_by_id(db, topup_id)
        if not topup:
            raise NotFoundException(f"Top-up with id {topup_id} not found")
        if topup.status != "PENDING":
            raise ValidationException(
                f"Cannot reject top-up that is already in '{topup.status}' status"
            )

        return self.topup_repo.update_status(
            db, topup, status="REJECTED", admin_id=admin_id, note=req.admin_note
        )
