from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from app.models.topup import TopUp
from app.schemas.pagination import PaginationParams
from app.utils.pagination import get_paginated_response
from app.core.exceptions import DatabaseException


class TopUpRepository:
    def create(self, db: Session, data: dict) -> TopUp:
        topup = TopUp(**data)
        try:
            db.add(topup)
            db.commit()
            db.refresh(topup)
            return topup
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to submit topup: {str(e)}", original_exception=e
            )

    def get_by_id(self, db: Session, topup_id: int) -> Optional[TopUp]:
        return (
            db.query(TopUp)
            .options(joinedload(TopUp.payment_method), joinedload(TopUp.user))
            .filter(TopUp.id == topup_id, TopUp.is_deleted.is_(False))
            .first()
        )

    def get_user_topups(self, db: Session, user_id: int) -> List[TopUp]:
        return (
            db.query(TopUp)
            .options(joinedload(TopUp.payment_method))
            .filter(TopUp.user_id == user_id, TopUp.is_deleted.is_(False))
            .order_by(TopUp.id.desc())
            .all()
        )

    def get_all(
        self, db: Session, pagination: PaginationParams, status: Optional[str] = None
    ):
        try:
            query = (
                db.query(TopUp)
                .options(joinedload(TopUp.payment_method), joinedload(TopUp.user))
                .filter(TopUp.is_deleted.is_(False))
            )
            if status:
                query = query.filter(TopUp.status == status)

            total = query.count()
            items = (
                query.order_by(TopUp.id.desc())
                .offset(pagination.offset)
                .limit(pagination.size)
                .all()
            )
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(
                f"Failed to fetch topups: {str(e)}", original_exception=e
            )

    def update_status(
        self,
        db: Session,
        topup: TopUp,
        status: str,
        admin_id: int,
        note: Optional[str] = None,
    ) -> TopUp:
        try:
            topup.status = status
            topup.verified_by = admin_id
            topup.verified_at = datetime.now(timezone.utc)
            if note is not None:
                topup.admin_note = note
            db.commit()
            db.refresh(topup)
            return topup
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update topup status: {str(e)}", original_exception=e
            )
