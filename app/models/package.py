from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class Package(BaseAuditModel):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    compare_price = Column(Float, nullable=True)
    duration = Column(String, nullable=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="packages")
    order_items = relationship("OrderItem", back_populates="package")
