from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.coupon import Coupon
from app.core.exceptions import DatabaseException


class CouponRepository:
    def get_by_code(self, db: Session, code: str) -> Optional[Coupon]:
        return db.query(Coupon).filter(Coupon.code == code, Coupon.is_deleted.is_(False)).first()

    def get_by_id(self, db: Session, coupon_id: int) -> Optional[Coupon]:
        return db.query(Coupon).filter(Coupon.id == coupon_id, Coupon.is_deleted.is_(False)).first()

    def get_all(self, db: Session, is_active: Optional[bool] = None) -> List[Coupon]:
        query = db.query(Coupon).filter(Coupon.is_deleted.is_(False))
        if is_active is not None:
            query = query.filter(Coupon.is_active == is_active)
        return query.order_by(Coupon.id.desc()).all()

    def create(self, db: Session, data: dict) -> Coupon:
        coupon = Coupon(**data)
        try:
            db.add(coupon)
            db.commit()
            db.refresh(coupon)
            return coupon
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to create coupon: {str(e)}", original_exception=e)

    def update(self, db: Session, coupon: Coupon, data: dict) -> Coupon:
        try:
            for key, val in data.items():
                if val is not None and hasattr(coupon, key):
                    setattr(coupon, key, val)
            db.commit()
            db.refresh(coupon)
            return coupon
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to update coupon: {str(e)}", original_exception=e)

    def increment_used_count(self, db: Session, coupon_id: int) -> None:
        try:
            db.query(Coupon).filter(Coupon.id == coupon_id).update({Coupon.used_count: Coupon.used_count + 1})
            db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to update coupon count: {str(e)}", original_exception=e)

    def delete(self, db: Session, coupon: Coupon) -> None:
        try:
            coupon.soft_delete()
            db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to delete coupon: {str(e)}", original_exception=e)
