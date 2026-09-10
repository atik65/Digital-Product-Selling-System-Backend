from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class Payment(BaseAuditModel):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    payment_method_id = Column(
        Integer,
        ForeignKey("payment_methods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    amount = Column(Float, nullable=False)
    transaction_id = Column(String, nullable=False, index=True)
    sender_number = Column(String, nullable=False)
    status = Column(
        String, default="VERIFYING", nullable=False, index=True
    )  # PENDING, VERIFYING, VERIFIED, REJECTED, EXPIRED

    verified_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at = Column(DateTime(timezone=True), nullable=True)
    admin_note = Column(String, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="payments")
    user = relationship("User", foreign_keys=[user_id], back_populates="payments")
    payment_method = relationship("PaymentMethod", back_populates="payments")
