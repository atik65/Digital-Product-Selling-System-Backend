from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.topup import TopUp
from app.models.order import Order
from app.models.incoming_sms import IncomingSms
from app.schemas.sms_webhook import SmsWebhookPayload, SmsWebhookResponse
from app.services.sms_parser_service import SmsParserService
from app.repositories.incoming_sms_repository import IncomingSmsRepository
from app.repositories.wallet_repository import WalletRepository


class SmsReconciliationService:
    def __init__(self):
        self.sms_repo = IncomingSmsRepository()
        self.wallet_repo = WalletRepository()

    def process_incoming_sms(
        self, db: Session, payload: SmsWebhookPayload
    ) -> SmsWebhookResponse:
        # 1. Parse SMS
        parsed = SmsParserService.parse(payload.sender, payload.message)

        # 2. Check for duplicate TrxID if available
        if parsed.transaction_id:
            existing = self.sms_repo.get_by_trx_id(db, parsed.transaction_id)
            if existing:
                return SmsWebhookResponse(
                    received=True,
                    matched=existing.is_matched,
                    provider=existing.provider,
                    transaction_id=existing.transaction_id,
                    amount=existing.amount,
                    sender_phone=existing.sender_phone,
                    matched_entity_type=existing.matched_entity_type,
                    matched_entity_id=existing.matched_entity_id,
                    message="Duplicate SMS received (idempotent ignore)",
                )

        # 3. Store in IncomingSms table
        sms_data = {
            "sender": payload.sender,
            "raw_message": payload.message,
            "provider": parsed.provider,
            "transaction_id": parsed.transaction_id,
            "amount": parsed.amount,
            "sender_phone": parsed.sender_phone,
            "balance": parsed.balance,
            "sim_slot": payload.sim_slot,
            "device_id": payload.device_id,
            "is_matched": False,
            "status": "PENDING" if parsed.is_received_money else "IGNORED",
        }
        sms_record = self.sms_repo.create(db, sms_data)

        if not parsed.is_received_money or not parsed.transaction_id:
            return SmsWebhookResponse(
                received=True,
                matched=False,
                provider=parsed.provider,
                transaction_id=parsed.transaction_id,
                amount=parsed.amount,
                message="SMS recorded, not an incoming payment",
            )

        # 4. Try matching against existing Order Payment
        payment = (
            db.query(Payment)
            .filter(
                Payment.transaction_id == parsed.transaction_id,
                Payment.status.in_(["VERIFYING", "PENDING"]),
                Payment.is_deleted.is_(False),
            )
            .first()
        )
        if payment:
            if parsed.amount and parsed.amount >= payment.amount:
                # Settle Payment & Order
                payment.status = "VERIFIED"
                payment.verified_at = datetime.now(timezone.utc)
                payment.admin_note = (
                    f"Auto-verified via SMS Webhook ({parsed.provider})"
                )

                order = db.query(Order).filter(Order.id == payment.order_id).first()
                if order and order.status in ["PENDING", "PAYMENT_PENDING"]:
                    order.status = "PAID"

                self.sms_repo.mark_as_matched(
                    db, sms_record, "ORDER_PAYMENT", payment.id
                )
                db.commit()

                return SmsWebhookResponse(
                    received=True,
                    matched=True,
                    provider=parsed.provider,
                    transaction_id=parsed.transaction_id,
                    amount=parsed.amount,
                    sender_phone=parsed.sender_phone,
                    matched_entity_type="ORDER_PAYMENT",
                    matched_entity_id=payment.id,
                    message=f"Order #{payment.order_id} auto-verified and marked PAID",
                )
            else:
                payment.admin_note = f"Amount mismatch: required {payment.amount} BDT, received {parsed.amount} BDT"
                sms_record.status = "MISMATCH"
                db.commit()
                return SmsWebhookResponse(
                    received=True,
                    matched=False,
                    provider=parsed.provider,
                    transaction_id=parsed.transaction_id,
                    amount=parsed.amount,
                    message="Amount mismatch with existing pending payment",
                )

        # 5. Try matching against existing Wallet Top-Up
        topup = (
            db.query(TopUp)
            .filter(
                TopUp.transaction_id == parsed.transaction_id,
                TopUp.status == "PENDING",
                TopUp.is_deleted.is_(False),
            )
            .first()
        )
        if topup:
            if parsed.amount and parsed.amount >= topup.amount:
                # Approve TopUp & Credit Balance
                topup.status = "APPROVED"
                topup.verified_at = datetime.now(timezone.utc)
                topup.admin_note = f"Auto-approved via SMS Webhook ({parsed.provider})"

                wallet = self.wallet_repo.get_by_user_id(
                    db, topup.user_id, for_update=True
                )
                if not wallet:
                    wallet = self.wallet_repo.create_wallet(db, topup.user_id)

                self.wallet_repo.update_balance_with_transaction(
                    db,
                    wallet=wallet,
                    amount=topup.amount,
                    tx_type="credit",
                    reference_type="topup",
                    description=f"Wallet TopUp via {parsed.provider} (TrxID: {parsed.transaction_id})",
                )

                self.sms_repo.mark_as_matched(db, sms_record, "WALLET_TOPUP", topup.id)
                db.commit()

                return SmsWebhookResponse(
                    received=True,
                    matched=True,
                    provider=parsed.provider,
                    transaction_id=parsed.transaction_id,
                    amount=parsed.amount,
                    sender_phone=parsed.sender_phone,
                    matched_entity_type="WALLET_TOPUP",
                    matched_entity_id=topup.id,
                    message=f"Wallet top-up #{topup.id} auto-approved and balance credited",
                )
            else:
                topup.admin_note = f"Amount mismatch: requested {topup.amount} BDT, received {parsed.amount} BDT"
                sms_record.status = "MISMATCH"
                db.commit()
                return SmsWebhookResponse(
                    received=True,
                    matched=False,
                    provider=parsed.provider,
                    transaction_id=parsed.transaction_id,
                    amount=parsed.amount,
                    message="Amount mismatch with existing pending top-up",
                )

        # 6. No matching record yet (Scenario B)
        return SmsWebhookResponse(
            received=True,
            matched=False,
            provider=parsed.provider,
            transaction_id=parsed.transaction_id,
            amount=parsed.amount,
            sender_phone=parsed.sender_phone,
            message="SMS received and queued for customer reconciliation",
        )

    def check_and_match_unclaimed(
        self,
        db: Session,
        transaction_id: str,
        required_amount: float,
        entity_type: str,
        entity_id: int,
    ) -> Optional[IncomingSms]:
        """Check if an incoming SMS arrived prior to customer submission."""
        sms = self.sms_repo.get_unmatched_by_trx_id(db, transaction_id)
        if not sms:
            return None

        if sms.amount and sms.amount >= required_amount:
            self.sms_repo.mark_as_matched(db, sms, entity_type, entity_id)
            return sms

        return None
