from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PaymentMethodBase(BaseModel):
    name: str
    account_number: str
    instructions: Optional[str] = None
    logo: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class PaymentMethodCreate(PaymentMethodBase):
    daily_transaction_limit: Optional[int] = Field(None, ge=1)
    monthly_transaction_limit: Optional[int] = Field(None, ge=1)


class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = None
    account_number: Optional[str] = None
    instructions: Optional[str] = None
    logo: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    # Send null explicitly to remove a limit.
    daily_transaction_limit: Optional[int] = Field(None, ge=1)
    monthly_transaction_limit: Optional[int] = Field(None, ge=1)


class PaymentMethodResponse(PaymentMethodBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentMethodAdminResponse(PaymentMethodResponse):
    """Admin view: includes transaction limits and current usage counters."""

    daily_transaction_limit: Optional[int] = None
    monthly_transaction_limit: Optional[int] = None
    # Successful transactions today / since the 1st of this month (Bangladesh time)
    daily_transaction_count: int = 0
    monthly_transaction_count: int = 0
    # limit - count (never below 0); None when no limit is set
    daily_remaining: Optional[int] = None
    monthly_remaining: Optional[int] = None
