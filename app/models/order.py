from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class Order(BaseAuditModel):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    order_number = Column(String, unique=True, index=True, nullable=False)
    subtotal = Column(Float, nullable=False)
    discount = Column(Float, default=0.0, nullable=False)
    total_amount = Column(Float, nullable=False)
    coupon_id = Column(
        Integer,
        ForeignKey("coupons.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(String, default="PAYMENT_PENDING", nullable=False, index=True)
    # Statuses: PENDING, PAYMENT_PENDING, PAID, PROCESSING, COMPLETED, CANCELLED, FAILED, REFUNDED
    customer_note = Column(String, nullable=True)
    admin_note = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="orders")
    coupon = relationship("Coupon", back_populates="orders")
    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    payments = relationship(
        "Payment", back_populates="order", cascade="all, delete-orphan"
    )
