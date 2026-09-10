from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class LotteryPrizeBase(BaseModel):
    product_id: Optional[int] = None
    package_id: Optional[int] = None
    discount_type: str = "PERCENTAGE"  # PERCENTAGE, FIXED, FREE
    discount_value: float = 0.0
    probability: float = 0.0
    quantity: int = 0


class LotteryPrizeCreate(LotteryPrizeBase):
    pass


class LotteryPrizeResponse(LotteryPrizeBase):
    id: int
    lottery_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LotteryBase(BaseModel):
    name: str
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: bool = True


class LotteryCreate(LotteryBase):
    pass


class LotteryResponse(LotteryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    prizes: List[LotteryPrizeResponse] = []

    model_config = ConfigDict(from_attributes=True)


class LotteryEligibilityResponse(BaseModel):
    eligible: bool
    remaining_attempts: int
    message: str


class LotterySpinResponse(BaseModel):
    success: bool
    won: bool
    message: str
    prize: Optional[LotteryPrizeResponse] = None


class LotteryEntryResponse(BaseModel):
    id: int
    lottery_id: int
    user_id: int
    lottery_prize_id: Optional[int] = None
    created_at: datetime
    prize: Optional[LotteryPrizeResponse] = None

    model_config = ConfigDict(from_attributes=True)
