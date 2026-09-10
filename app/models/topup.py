from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class TopUp(BaseAuditModel):
    __tablename__ = "topups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id", ondelete="RESTRICT"), nullable=False, index=True)

    amount = Column(Float, nullable=False)
    transaction_id = Column(String, nullable=False, index=True)
    sender_number = Column(String, nullable=False)
    status = Column(String, default="PENDING", nullable=False, index=True)  # PENDING, APPROVED, REJECTED

    admin_note = Column(String, nullable=True)
    verified_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="topups")
    payment_method = relationship("PaymentMethod", back_populates="topups")
