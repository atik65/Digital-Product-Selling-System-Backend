from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.payment_method import PaymentMethodResponse


class PaymentSubmitRequest(BaseModel):
    order_id: int
    payment_method_id: int
    amount: float
    transaction_id: str
    sender_number: str


class PaymentVerifyRequest(BaseModel):
    admin_note: Optional[str] = "Payment verified and approved"


class PaymentRejectRequest(BaseModel):
    admin_note: str = "Invalid or unverified transaction ID"


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    payment_method_id: int
    amount: float
    transaction_id: str
    sender_number: str
    status: str
    verified_by: Optional[int] = None
    verified_at: Optional[datetime] = None
    admin_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    payment_method: Optional[PaymentMethodResponse] = None

    model_config = ConfigDict(from_attributes=True)
