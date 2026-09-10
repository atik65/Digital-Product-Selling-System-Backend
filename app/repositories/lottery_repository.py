from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from app.models.lottery import Lottery, LotteryPrize, LotteryEntry
from app.schemas.pagination import PaginationParams
from app.utils.pagination import get_paginated_response
from app.core.exceptions import DatabaseException


class LotteryRepository:
    def get_active_lottery(self, db: Session) -> Optional[Lottery]:
        now = datetime.now(timezone.utc)
        return (
            db.query(Lottery)
            .options(joinedload(Lottery.prizes))
            .filter(
                Lottery.is_active.is_(True),
                Lottery.is_deleted.is_(False),
                (Lottery.starts_at.is_(None) | (Lottery.starts_at <= now)),
                (Lottery.ends_at.is_(None) | (Lottery.ends_at >= now)),
            )
            .first()
        )

    def get_by_id(self, db: Session, lottery_id: int) -> Optional[Lottery]:
        return (
            db.query(Lottery)
            .options(joinedload(Lottery.prizes))
            .filter(Lottery.id == lottery_id, Lottery.is_deleted.is_(False))
            .first()
        )

    def get_all(self, db: Session) -> List[Lottery]:
        return (
            db.query(Lottery)
            .options(joinedload(Lottery.prizes))
            .filter(Lottery.is_deleted.is_(False))
            .order_by(Lottery.id.desc())
            .all()
        )

    def create(self, db: Session, data: dict) -> Lottery:
        lottery = Lottery(**data)
        try:
            db.add(lottery)
            db.commit()
            db.refresh(lottery)
            return lottery
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create lottery: {str(e)}", original_exception=e
            )

    def add_prize(self, db: Session, prize_data: dict) -> LotteryPrize:
        prize = LotteryPrize(**prize_data)
        try:
            db.add(prize)
            db.commit()
            db.refresh(prize)
            return prize
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to add lottery prize: {str(e)}", original_exception=e
            )

    def decrement_prize_quantity(self, db: Session, prize_id: int) -> bool:
        try:
            rows = (
                db.query(LotteryPrize)
                .filter(LotteryPrize.id == prize_id, LotteryPrize.quantity > 0)
                .update({LotteryPrize.quantity: LotteryPrize.quantity - 1})
            )
            db.commit()
            return rows > 0
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to decrement prize: {str(e)}", original_exception=e
            )

    def create_entry(
        self, db: Session, lottery_id: int, user_id: int, prize_id: Optional[int]
    ) -> LotteryEntry:
        entry = LotteryEntry(
            lottery_id=lottery_id, user_id=user_id, lottery_prize_id=prize_id
        )
        try:
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to record lottery entry: {str(e)}", original_exception=e
            )

    def count_user_entries(self, db: Session, user_id: int, lottery_id: int) -> int:
        return (
            db.query(LotteryEntry)
            .filter(
                LotteryEntry.user_id == user_id,
                LotteryEntry.lottery_id == lottery_id,
                LotteryEntry.is_deleted.is_(False),
            )
            .count()
        )

    def get_user_entries(self, db: Session, user_id: int) -> List[LotteryEntry]:
        return (
            db.query(LotteryEntry)
            .options(joinedload(LotteryEntry.prize))
            .filter(LotteryEntry.user_id == user_id, LotteryEntry.is_deleted.is_(False))
            .order_by(LotteryEntry.id.desc())
            .all()
        )

    def get_all_entries(
        self, db: Session, lottery_id: int, pagination: PaginationParams
    ):
        try:
            query = (
                db.query(LotteryEntry)
                .options(joinedload(LotteryEntry.prize), joinedload(LotteryEntry.user))
                .filter(
                    LotteryEntry.lottery_id == lottery_id,
                    LotteryEntry.is_deleted.is_(False),
                )
            )
            total = query.count()
            items = (
                query.order_by(LotteryEntry.id.desc())
                .offset(pagination.offset)
                .limit(pagination.size)
                .all()
            )
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(
                f"Failed to fetch lottery entries: {str(e)}", original_exception=e
            )
