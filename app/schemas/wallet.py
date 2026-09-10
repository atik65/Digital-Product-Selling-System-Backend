from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WalletTransactionResponse(BaseModel):
    id: int
    wallet_id: int
    type: str
    amount: float
    balance_before: float
    balance_after: float
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WalletResponse(BaseModel):
    id: int
    user_id: int
    balance: float
    currency: str = "BDT"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WalletAdjustRequest(BaseModel):
    amount: float
    type: str = "ADJUSTMENT"  # ADJUSTMENT, BONUS, REFUND
    description: str = "Admin manual balance adjustment"
