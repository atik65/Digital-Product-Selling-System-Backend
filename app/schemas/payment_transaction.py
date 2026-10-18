from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.payment_method import PaymentMethodResponse
from app.schemas.user_brief import UserBriefResponse


class PaymentTransactionResponse(BaseModel):
    id: int
    payment_method_id: int
    source_type: str  # ORDER_PAYMENT, WALLET_TOPUP
    source_id: int
    user_id: Optional[int] = None
    transaction_id: str
    sender_number: Optional[str] = None
    amount: float
    transaction_at: datetime
    created_at: datetime
    payment_method: Optional[PaymentMethodResponse] = None
    user: Optional[UserBriefResponse] = None

    model_config = ConfigDict(from_attributes=True)
