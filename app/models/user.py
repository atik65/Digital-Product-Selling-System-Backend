from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class User(BaseAuditModel):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    image = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    role = Column(String, default="customer", nullable=False)  # "customer", "admin"
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    wallet = relationship(
        "Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    topups = relationship(
        "TopUp",
        foreign_keys="TopUp.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    payments = relationship(
        "Payment",
        foreign_keys="Payment.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    lottery_entries = relationship(
        "LotteryEntry", back_populates="user", cascade="all, delete-orphan"
    )
