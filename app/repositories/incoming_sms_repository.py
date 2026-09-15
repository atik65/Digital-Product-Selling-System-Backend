from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.incoming_sms import IncomingSms
from app.schemas.pagination import PaginationParams
from app.utils.pagination import get_paginated_response
from app.core.exceptions import DatabaseException


class IncomingSmsRepository:
    def create(self, db: Session, data: dict) -> IncomingSms:
        try:
            sms = IncomingSms(**data)
            db.add(sms)
            db.commit()
            db.refresh(sms)
            return sms
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to record incoming SMS: {str(e)}", original_exception=e
            )

    def get_by_id(self, db: Session, sms_id: int) -> Optional[IncomingSms]:
        return (
            db.query(IncomingSms)
            .filter(IncomingSms.id == sms_id, IncomingSms.is_deleted.is_(False))
            .first()
        )

    def get_by_trx_id(self, db: Session, trx_id: str) -> Optional[IncomingSms]:
        return (
            db.query(IncomingSms)
            .filter(
                IncomingSms.transaction_id == trx_id.strip(),
                IncomingSms.is_deleted.is_(False),
            )
            .first()
        )

    def get_unmatched_by_trx_id(
        self, db: Session, trx_id: str
    ) -> Optional[IncomingSms]:
        return (
            db.query(IncomingSms)
            .filter(
                IncomingSms.transaction_id == trx_id.strip(),
                IncomingSms.is_matched.is_(False),
                IncomingSms.is_deleted.is_(False),
            )
            .first()
        )

    def mark_as_matched(
        self,
        db: Session,
        sms: IncomingSms,
        entity_type: str,
        entity_id: int,
    ) -> IncomingSms:
        try:
            sms.is_matched = True
            sms.matched_entity_type = entity_type
            sms.matched_entity_id = entity_id
            sms.matched_at = datetime.now(timezone.utc)
            sms.status = "PROCESSED"
            db.commit()
            db.refresh(sms)
            return sms
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update matched SMS: {str(e)}", original_exception=e
            )

    def get_all(
        self,
        db: Session,
        pagination: PaginationParams,
        is_matched: Optional[bool] = None,
        provider: Optional[str] = None,
        search: Optional[str] = None,
    ):
        try:
            query = db.query(IncomingSms).filter(IncomingSms.is_deleted.is_(False))

            if is_matched is not None:
                query = query.filter(IncomingSms.is_matched == is_matched)

            if provider:
                query = query.filter(IncomingSms.provider == provider.upper())

            if search:
                term = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        IncomingSms.transaction_id.ilike(term),
                        IncomingSms.sender_phone.ilike(term),
                        IncomingSms.raw_message.ilike(term),
                    )
                )

            total = query.count()
            items = (
                query.order_by(IncomingSms.id.desc())
                .offset(pagination.offset)
                .limit(pagination.size)
                .all()
            )
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(
                f"Failed to query incoming SMS logs: {str(e)}",
                original_exception=e,
            )
