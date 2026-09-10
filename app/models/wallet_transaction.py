from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class WalletTransaction(BaseAuditModel):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)  # TOPUP, PURCHASE, REFUND, ADJUSTMENT, BONUS
    amount = Column(Float, nullable=False)
    balance_before = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    reference_type = Column(String, nullable=True)  # order, topup, admin_adjustment
    reference_id = Column(String, nullable=True)
    description = Column(String, nullable=True)

    # Relationship
    wallet = relationship("Wallet", back_populates="transactions")
