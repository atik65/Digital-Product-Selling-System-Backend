from datetime import date, datetime, timedelta
from typing import Dict, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload
from app.models.payment_transaction import PaymentTransaction
from app.models.user import User
from app.schemas.pagination import PaginationParams
from app.utils.pagination import get_paginated_response
from app.utils.period import business_date_start_utc
from app.core.exceptions import DatabaseException


class PaymentTransactionRepository:
    def get_by_source(
        self, db: Session, source_type: str, source_id: int
    ) -> Optional[PaymentTransaction]:
        """Looks up the ledger row for a payment / top-up, including revoked ones."""
        return (
            db.query(PaymentTransaction)
            .filter(
                PaymentTransaction.source_type == source_type,
                PaymentTransaction.source_id == source_id,
            )
            .first()
        )

    def record(
        self, db: Session, data: dict, commit: bool = True
    ) -> PaymentTransaction:
        """
        Idempotently records a successful transaction. A row that was revoked
        earlier is revived instead of duplicated.
        """
        try:
            tx = self.get_by_source(db, data["source_type"], data["source_id"])
            if tx is None:
                tx = PaymentTransaction(**data)
                db.add(tx)
            elif tx.is_deleted:
                # Re-verified after a rejection: revive with the fresh details.
                tx.restore()
                for key, val in data.items():
                    setattr(tx, key, val)
            else:
                return tx
            if commit:
                db.commit()
                db.refresh(tx)
            return tx
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to record payment transaction: {str(e)}", original_exception=e
            )

    def revoke(
        self, db: Session, source_type: str, source_id: int, commit: bool = True
    ) -> None:
        try:
            tx = self.get_by_source(db, source_type, source_id)
            if tx is None or tx.is_deleted:
                return
            tx.soft_delete()
            if commit:
                db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to revoke payment transaction: {str(e)}", original_exception=e
            )

    def count_by_method(
        self, db: Session, start: datetime, end: datetime
    ) -> Dict[int, int]:
        """Counts successful transactions per payment method within [start, end)."""
        rows = (
            db.query(
                PaymentTransaction.payment_method_id, func.count(PaymentTransaction.id)
            )
            .filter(
                PaymentTransaction.is_deleted.is_(False),
                PaymentTransaction.transaction_at >= start,
                PaymentTransaction.transaction_at < end,
            )
            .group_by(PaymentTransaction.payment_method_id)
            .all()
        )
        return {method_id: count for method_id, count in rows}

    def get_all(
        self,
        db: Session,
        pagination: PaginationParams,
        payment_method_id: Optional[int] = None,
        source_type: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ):
        try:
            query = (
                db.query(PaymentTransaction)
                .options(
                    joinedload(PaymentTransaction.payment_method),
                    joinedload(PaymentTransaction.user).joinedload(User.wallet),
                )
                .filter(PaymentTransaction.is_deleted.is_(False))
            )
            if payment_method_id is not None:
                query = query.filter(
                    PaymentTransaction.payment_method_id == payment_method_id
                )
            if source_type:
                query = query.filter(PaymentTransaction.source_type == source_type)
            if search and search.strip():
                term = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        PaymentTransaction.transaction_id.ilike(term),
                        PaymentTransaction.sender_number.ilike(term),
                    )
                )
            if date_from:
                query = query.filter(
                    PaymentTransaction.transaction_at
                    >= business_date_start_utc(date_from)
                )
            if date_to:
                query = query.filter(
                    PaymentTransaction.transaction_at
                    < business_date_start_utc(date_to + timedelta(days=1))
                )

            total = query.count()
            items = (
                query.order_by(
                    PaymentTransaction.transaction_at.desc(),
                    PaymentTransaction.id.desc(),
                )
                .offset(pagination.offset)
                .limit(pagination.size)
                .all()
            )
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(
                f"Failed to fetch payment transactions: {str(e)}", original_exception=e
            )
