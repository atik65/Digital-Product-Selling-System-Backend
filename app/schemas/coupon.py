from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CouponBase(BaseModel):
    code: str
    type: str = "FIXED"  # FIXED, PERCENTAGE
    value: float
    max_discount: Optional[float] = None
    minimum_order_amount: float = 0.0
    usage_limit: Optional[int] = None
    per_user_limit: int = 1
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    code: Optional[str] = None
    type: Optional[str] = None
    value: Optional[float] = None
    max_discount: Optional[float] = None
    minimum_order_amount: Optional[float] = None
    usage_limit: Optional[int] = None
    per_user_limit: Optional[int] = None
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class CouponValidateRequest(BaseModel):
    code: str
    package_id: int
    quantity: int = 1


class CouponValidateResponse(BaseModel):
    valid: bool
    code: str
    discount_type: str
    discount_amount: float
    message: str = "Coupon is valid"


class CouponResponse(CouponBase):
    id: int
    used_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
