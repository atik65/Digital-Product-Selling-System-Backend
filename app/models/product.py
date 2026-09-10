from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class Product(BaseAuditModel):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    image = Column(String, nullable=True)
    description = Column(String, nullable=True)
    instructions = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # Relationships
    category = relationship("Category", back_populates="products")
    packages = relationship(
        "Package", back_populates="product", cascade="all, delete-orphan"
    )
    input_fields = relationship(
        "ProductInputField", back_populates="product", cascade="all, delete-orphan"
    )
    order_items = relationship("OrderItem", back_populates="product")
