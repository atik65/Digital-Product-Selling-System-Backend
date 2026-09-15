from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime
from app.models.base import BaseAuditModel


class IncomingSms(BaseAuditModel):
    __tablename__ = "incoming_sms"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, nullable=False, index=True)  # bKash, Nagad, 16216
    raw_message = Column(Text, nullable=False)
    provider = Column(
        String, nullable=False, index=True
    )  # BKASH, NAGAD, ROCKET, UNKNOWN
    transaction_id = Column(
        String, nullable=True, index=True
    )  # Extracted TrxID e.g. 9K48X78L9
    amount = Column(Float, nullable=True)  # Extracted amount e.g. 500.0
    sender_phone = Column(String, nullable=True, index=True)  # Extracted sender number
    balance = Column(Float, nullable=True)  # Extracted account balance
    sim_slot = Column(Integer, nullable=True)  # SIM 1 or 2
    device_id = Column(String, nullable=True)  # Identifier of forwarding device
    is_matched = Column(Boolean, default=False, nullable=False, index=True)
    matched_entity_type = Column(String, nullable=True)  # ORDER_PAYMENT, WALLET_TOPUP
    matched_entity_id = Column(Integer, nullable=True)
    matched_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        String, default="PENDING", nullable=False, index=True
    )  # PENDING, PROCESSED, MISMATCH, IGNORED
