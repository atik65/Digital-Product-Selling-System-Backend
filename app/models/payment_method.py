from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class PaymentMethod(BaseAuditModel):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    instructions = Column(String, nullable=True)
    logo = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # Relationships
    payments = relationship("Payment", back_populates="payment_method")
    topups = relationship("TopUp", back_populates="payment_method")
