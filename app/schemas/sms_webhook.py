from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SmsWebhookPayload(BaseModel):
    sender: str = Field(..., description="Sender name, title, or phone number")
    message: str = Field(..., description="Raw SMS content or message text")
    sim_slot: Optional[int] = None
    device_id: Optional[str] = None
    timestamp: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def normalize_sms_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Support SmsForwarder and generic webhook field variants
            sender = (
                data.get("sender")
                or data.get("from")
                or data.get("phone")
                or data.get("title")
            )
            message = (
                data.get("message")
                or data.get("content")
                or data.get("org_content")
                or data.get("msg")
                or data.get("text")
                or data.get("body")
            )
            sim_slot = (
                data.get("sim_slot")
                if data.get("sim_slot") is not None
                else (
                    data.get("card_slot")
                    if data.get("card_slot") is not None
                    else data.get("sim")
                )
            )

            parsed_sim_slot: Optional[int] = None
            if sim_slot is not None:
                try:
                    if isinstance(sim_slot, str) and "SIM" in sim_slot.upper():
                        digits = "".join(filter(str.isdigit, sim_slot))
                        parsed_sim_slot = int(digits) if digits else None
                    else:
                        parsed_sim_slot = int(sim_slot)
                except (ValueError, TypeError):
                    parsed_sim_slot = None

            device_id = (
                data.get("device_id")
                or data.get("device_mark")
                or data.get("deviceMark")
                or data.get("device")
            )

            raw_ts = data.get("timestamp") or data.get("time") or data.get("sent_time")
            parsed_ts: Optional[int] = None
            if raw_ts is not None:
                try:
                    parsed_ts = int(raw_ts)
                except (ValueError, TypeError):
                    parsed_ts = None

            normalized = dict(data)
            if sender is not None:
                normalized["sender"] = str(sender)
            if message is not None:
                normalized["message"] = str(message)
            normalized["sim_slot"] = parsed_sim_slot
            if device_id is not None:
                normalized["device_id"] = str(device_id)
            normalized["timestamp"] = parsed_ts
            return normalized

        return data


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
