from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.repositories.coupon_repository import CouponRepository
from app.repositories.order_repository import OrderRepository
from app.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponUpdate
from app.core.exceptions import NotFoundException, ValidationException, ConflictException


class CouponService:
    def __init__(self):
        self.repo = CouponRepository()
        self.order_repo = OrderRepository()

    def get_coupons(self, db: Session, is_active: Optional[bool] = None) -> List[Coupon]:
        return self.repo.get_all(db, is_active=is_active)

    def get_by_id(self, db: Session, coupon_id: int) -> Coupon:
        coupon = self.repo.get_by_id(db, coupon_id)
        if not coupon:
            raise NotFoundException(f"Coupon with id {coupon_id} not found")
        return coupon

    def create_coupon(self, db: Session, data: CouponCreate) -> Coupon:
        code_clean = data.code.strip().upper()
        existing = self.repo.get_by_code(db, code_clean)
        if existing:
            raise ConflictException(f"Coupon code '{code_clean}' already exists")

        c_dict = data.model_dump()
        c_dict["code"] = code_clean
        return self.repo.create(db, c_dict)

    def update_coupon(self, db: Session, coupon_id: int, data: CouponUpdate) -> Coupon:
        coupon = self.get_by_id(db, coupon_id)
        u_dict = data.model_dump(exclude_unset=True)
        if "code" in u_dict:
            u_dict["code"] = u_dict["code"].strip().upper()
            if u_dict["code"] != coupon.code:
                existing = self.repo.get_by_code(db, u_dict["code"])
                if existing:
                    raise ConflictException(f"Coupon code '{u_dict['code']}' already exists")
        return self.repo.update(db, coupon, u_dict)

    def delete_coupon(self, db: Session, coupon_id: int) -> None:
        coupon = self.get_by_id(db, coupon_id)
        self.repo.delete(db, coupon)

    def validate_and_calculate_discount(
        self, db: Session, code: str, subtotal: float, user_id: Optional[int] = None
    ) -> Tuple[float, Coupon]:
        code_clean = code.strip().upper()
        coupon = self.repo.get_by_code(db, code_clean)
        if not coupon or not coupon.is_active:
            raise ValidationException("Invalid or inactive coupon code")

        now = datetime.now(timezone.utc)
        if coupon.starts_at:
            starts_at = coupon.starts_at if coupon.starts_at.tzinfo else coupon.starts_at.replace(tzinfo=timezone.utc)
            if starts_at > now:
                raise ValidationException("Coupon is not active yet")

        if coupon.expires_at:
            expires_at = coupon.expires_at if coupon.expires_at.tzinfo else coupon.expires_at.replace(tzinfo=timezone.utc)
            if expires_at < now:
                raise ValidationException("Coupon has expired")

        if subtotal < coupon.minimum_order_amount:
            raise ValidationException(
                f"Order subtotal {subtotal} is less than coupon minimum {coupon.minimum_order_amount}"
            )

        if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
            raise ValidationException("Coupon total usage limit has been reached")

        if user_id is not None:
            user_uses = self.order_repo.count_user_coupon_uses(db, user_id, coupon.id)
            if user_uses >= coupon.per_user_limit:
                raise ValidationException("You have reached the maximum usage limit for this coupon")

        # Calculate discount
        if coupon.type == "PERCENTAGE":
            discount = subtotal * (coupon.value / 100.0)
            if coupon.max_discount is not None:
                discount = min(discount, coupon.max_discount)
        else:  # FIXED
            discount = min(coupon.value, subtotal)

        discount = round(discount, 2)
        return discount, coupon
