from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.models.payment import Payment
from app.schemas.pagination import PaginationParams
from app.utils.pagination import get_paginated_response
from app.core.exceptions import DatabaseException


class PaymentRepository:
    def create(self, db: Session, data: dict) -> Payment:
        payment = Payment(**data)
        try:
            db.add(payment)
            db.commit()
            db.refresh(payment)
            return payment
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to submit payment: {str(e)}", original_exception=e)

    def get_by_id(self, db: Session, payment_id: int) -> Optional[Payment]:
        return (
            db.query(Payment)
            .options(joinedload(Payment.payment_method), joinedload(Payment.order))
            .filter(Payment.id == payment_id, Payment.is_deleted.is_(False))
            .first()
        )

    def get_by_order_id(self, db: Session, order_id: int) -> Optional[Payment]:
        return (
            db.query(Payment)
            .options(joinedload(Payment.payment_method))
            .filter(Payment.order_id == order_id, Payment.is_deleted.is_(False))
            .order_by(Payment.id.desc())
            .first()
        )

    def get_all(self, db: Session, pagination: PaginationParams, status: Optional[str] = None):
        try:
            query = db.query(Payment).options(joinedload(Payment.payment_method), joinedload(Payment.order), joinedload(Payment.user)).filter(Payment.is_deleted.is_(False))
            if status:
                query = query.filter(Payment.status == status)

            total = query.count()
            items = query.order_by(Payment.id.desc()).offset(pagination.offset).limit(pagination.size).all()
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(f"Failed to fetch payments: {str(e)}", original_exception=e)

    def update_verification(self, db: Session, payment: Payment, status: str, admin_id: int, note: Optional[str] = None) -> Payment:
        from datetime import datetime, timezone
        try:
            payment.status = status
            payment.verified_by = admin_id
            payment.verified_at = datetime.now(timezone.utc)
            if note is not None:
                payment.admin_note = note
            db.commit()
            db.refresh(payment)
            return payment
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to update payment status: {str(e)}", original_exception=e)
