from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.payment_method import PaymentMethod
from app.core.exceptions import DatabaseException


class PaymentMethodRepository:
    def get_all(self, db: Session, active_only: bool = True) -> List[PaymentMethod]:
        query = db.query(PaymentMethod).filter(PaymentMethod.is_deleted.is_(False))
        if active_only:
            query = query.filter(PaymentMethod.is_active.is_(True))
        return query.order_by(
            PaymentMethod.sort_order.asc(), PaymentMethod.id.asc()
        ).all()

    def get_by_id(self, db: Session, method_id: int) -> Optional[PaymentMethod]:
        return (
            db.query(PaymentMethod)
            .filter(PaymentMethod.id == method_id, PaymentMethod.is_deleted.is_(False))
            .first()
        )

    def create(self, db: Session, data: dict) -> PaymentMethod:
        method = PaymentMethod(**data)
        try:
            db.add(method)
            db.commit()
            db.refresh(method)
            return method
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create payment method: {str(e)}", original_exception=e
            )

    def update(self, db: Session, method: PaymentMethod, data: dict) -> PaymentMethod:
        try:
            for key, val in data.items():
                if val is not None and hasattr(method, key):
                    setattr(method, key, val)
            db.commit()
            db.refresh(method)
            return method
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update payment method: {str(e)}", original_exception=e
            )

    def delete(self, db: Session, method: PaymentMethod) -> None:
        try:
            method.soft_delete()
            db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to delete payment method: {str(e)}", original_exception=e
            )
