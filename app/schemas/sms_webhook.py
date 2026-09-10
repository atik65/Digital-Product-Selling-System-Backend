from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SmsWebhookPayload(BaseModel):
    sender: str
    message: str
    sim_slot: Optional[int] = None
    device_id: Optional[str] = None
    timestamp: Optional[int] = None


class SmsWebhookResponse(BaseModel):
    received: bool
    matched: bool
    provider: str
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    sender_phone: Optional[str] = None
    matched_entity_type: Optional[str] = None
    matched_entity_id: Optional[int] = None
    message: str


class IncomingSmsResponse(BaseModel):
    id: int
    sender: str
    raw_message: str
    provider: str
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    sender_phone: Optional[str] = None
    balance: Optional[float] = None
    sim_slot: Optional[int] = None
    device_id: Optional[str] = None
    is_matched: bool
    matched_entity_type: Optional[str] = None
    matched_entity_id: Optional[int] = None
    matched_at: Optional[datetime] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
