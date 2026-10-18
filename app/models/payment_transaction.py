from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class PaymentTransaction(BaseAuditModel):
    """
    Ledger of successful transactions received on a payment method.

    One row is written when an order payment is VERIFIED or a wallet top-up is
    APPROVED (manually by an admin or automatically through the SMS webhook).
    Daily / monthly usage counters for each payment method are derived from it.
    A row is soft-deleted if the underlying payment is later rejected, so it no
    longer counts.
    """

    __tablename__ = "payment_transactions"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", name="uq_payment_tx_source"),
        Index("ix_payment_tx_method_time", "payment_method_id", "transaction_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    payment_method_id = Column(
        Integer,
        ForeignKey("payment_methods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_type = Column(
        String, nullable=False, index=True
    )  # ORDER_PAYMENT, WALLET_TOPUP
    source_id = Column(Integer, nullable=False)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    transaction_id = Column(String, nullable=False, index=True)
    sender_number = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    transaction_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    payment_method = relationship("PaymentMethod")
    user = relationship("User", foreign_keys=[user_id])
