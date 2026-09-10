from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class Wallet(BaseAuditModel):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    balance = Column(Float, default=0.0, nullable=False)

    # Relationships
    user = relationship("User", back_populates="wallet")
    transactions = relationship(
        "WalletTransaction",
        back_populates="wallet",
        cascade="all, delete-orphan",
        order_by="desc(WalletTransaction.created_at)",
    )
