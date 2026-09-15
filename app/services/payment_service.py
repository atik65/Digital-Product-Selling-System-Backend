from sqlalchemy.orm import Session
from app.repositories.payment_repository import PaymentRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_method_repository import PaymentMethodRepository
from app.models.payment import Payment
from app.schemas.payment import (
    PaymentSubmitRequest,
    PaymentVerifyRequest,
    PaymentRejectRequest,
)
from app.schemas.pagination import PaginationParams
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    ForbiddenException,
)


class PaymentService:
    def __init__(self):
        self.payment_repo = PaymentRepository()
        self.order_repo = OrderRepository()
        self.method_repo = PaymentMethodRepository()

    def submit_payment(
        self, db: Session, user_id: int, req: PaymentSubmitRequest
    ) -> Payment:
        order = self.order_repo.get_by_id(db, req.order_id)
        if not order:
            raise NotFoundException(f"Order with id {req.order_id} not found")
        if order.user_id != user_id:
            raise ForbiddenException(
                "You cannot submit payment for an order that is not yours"
            )
        if order.status not in ["PENDING", "PAYMENT_PENDING"]:
            raise ValidationException(
                f"Order is already in '{order.status}' status and cannot accept payment"
            )

        method = self.method_repo.get_by_id(db, req.payment_method_id)
        if not method or not method.is_active:
            raise NotFoundException("Selected payment method is invalid or inactive")

        payment_data = {
            "order_id": order.id,
            "user_id": user_id,
            "payment_method_id": method.id,
            "amount": req.amount,
            "transaction_id": req.transaction_id.strip(),
            "sender_number": req.sender_number.strip(),
            "status": "VERIFYING",
        }
        payment = self.payment_repo.create(db, payment_data)

        # Check if SMS already arrived for this transaction
        from app.services.sms_reconciliation_service import SmsReconciliationService
        from datetime import datetime, timezone

        sms_service = SmsReconciliationService()
        matched_sms = sms_service.check_and_match_unclaimed(
            db,
            transaction_id=payment.transaction_id,
            required_amount=payment.amount,
            entity_type="ORDER_PAYMENT",
            entity_id=payment.id,
        )
        if matched_sms:
            payment.status = "VERIFIED"
            payment.verified_at = datetime.now(timezone.utc)
            payment.admin_note = (
                f"Auto-verified instantly via SMS ({matched_sms.provider})"
            )
            self.order_repo.update_status(db, order, "PAID")
            db.commit()
            db.refresh(payment)

        return payment

    def get_order_payment(self, db: Session, order_id: int, user_id: int) -> Payment:
        order = self.order_repo.get_by_id(db, order_id)
        if not order:
            raise NotFoundException(f"Order with id {order_id} not found")
        if order.user_id != user_id:
            raise ForbiddenException("Unauthorized")

        payment = self.payment_repo.get_by_order_id(db, order_id)
        if not payment:
            raise NotFoundException("No payment found for this order")
        return payment

    def get_all_payments(
        self, db: Session, pagination: PaginationParams, status: str = None
    ):
        return self.payment_repo.get_all(db, pagination, status)

    def verify_payment(
        self, db: Session, payment_id: int, admin_id: int, req: PaymentVerifyRequest
    ) -> Payment:
        payment = self.payment_repo.get_by_id(db, payment_id)
        if not payment:
            raise NotFoundException(f"Payment with id {payment_id} not found")

        # 1. Mark payment VERIFIED
        updated_payment = self.payment_repo.update_verification(
            db, payment, status="VERIFIED", admin_id=admin_id, note=req.admin_note
        )

        # 2. Automatically mark order as PAID
        order = payment.order
        if order and order.status in ["PENDING", "PAYMENT_PENDING"]:
            self.order_repo.update_status(db, order, "PAID")

        return updated_payment

    def reject_payment(
        self, db: Session, payment_id: int, admin_id: int, req: PaymentRejectRequest
    ) -> Payment:
        payment = self.payment_repo.get_by_id(db, payment_id)
        if not payment:
            raise NotFoundException(f"Payment with id {payment_id} not found")

        updated_payment = self.payment_repo.update_verification(
            db, payment, status="REJECTED", admin_id=admin_id, note=req.admin_note
        )

        # Ensure order stays in PAYMENT_PENDING
        order = payment.order
        if order and order.status == "PENDING":
            self.order_repo.update_status(db, order, "PAYMENT_PENDING")

        return updated_payment
