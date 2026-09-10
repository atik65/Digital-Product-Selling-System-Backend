from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class Lottery(BaseAuditModel):
    __tablename__ = "lotteries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    prizes = relationship(
        "LotteryPrize", back_populates="lottery", cascade="all, delete-orphan"
    )
    entries = relationship(
        "LotteryEntry", back_populates="lottery", cascade="all, delete-orphan"
    )


class LotteryPrize(BaseAuditModel):
    __tablename__ = "lottery_prizes"

    id = Column(Integer, primary_key=True, index=True)
    lottery_id = Column(
        Integer,
        ForeignKey("lotteries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )
    package_id = Column(
        Integer, ForeignKey("packages.id", ondelete="SET NULL"), nullable=True
    )

    discount_type = Column(
        String, default="PERCENTAGE", nullable=False
    )  # PERCENTAGE, FIXED, FREE
    discount_value = Column(Float, default=0.0, nullable=False)
    probability = Column(
        Float, default=0.0, nullable=False
    )  # Weight / Probability e.g. 0.05
    quantity = Column(Integer, default=0, nullable=False)  # Available inventory

    # Relationships
    lottery = relationship("Lottery", back_populates="prizes")
    product = relationship("Product")
    package = relationship("Package")


class LotteryEntry(BaseAuditModel):
    __tablename__ = "lottery_entries"

    id = Column(Integer, primary_key=True, index=True)
    lottery_id = Column(
        Integer,
        ForeignKey("lotteries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lottery_prize_id = Column(
        Integer, ForeignKey("lottery_prizes.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    lottery = relationship("Lottery", back_populates="entries")
    user = relationship("User", back_populates="lottery_entries")
    prize = relationship("LotteryPrize")
