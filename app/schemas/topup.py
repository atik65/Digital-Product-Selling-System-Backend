from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.payment_method import PaymentMethodResponse


class TopUpCreateRequest(BaseModel):
    payment_method_id: int
    amount: float
    transaction_id: str
    sender_number: str


class TopUpReviewRequest(BaseModel):
    admin_note: Optional[str] = None


class TopUpResponse(BaseModel):
    id: int
    user_id: int
    payment_method_id: int
    amount: float
    transaction_id: str
    sender_number: str
    status: str
    admin_note: Optional[str] = None
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    payment_method: Optional[PaymentMethodResponse] = None

    model_config = ConfigDict(from_attributes=True)
