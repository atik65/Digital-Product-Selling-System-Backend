from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class OrderItem(BaseAuditModel):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    package_id = Column(
        Integer,
        ForeignKey("packages.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Immutable Historical Snapshots
    product_name = Column(String, nullable=False)
    package_name = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    total_price = Column(Float, nullable=False)

    # Dynamic Customer Input Values (JSON)
    input_values = Column(JSON, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    package = relationship("Package", back_populates="order_items")
