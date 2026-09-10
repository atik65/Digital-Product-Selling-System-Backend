from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PaymentMethodBase(BaseModel):
    name: str
    account_number: str
    instructions: Optional[str] = None
    logo: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodUpdate(BaseModel):
    name: Optional[str] = None
    account_number: Optional[str] = None
    instructions: Optional[str] = None
    logo: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PaymentMethodResponse(PaymentMethodBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
