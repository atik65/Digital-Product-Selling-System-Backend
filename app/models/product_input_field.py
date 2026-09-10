from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseAuditModel


class ProductInputField(BaseAuditModel):
    __tablename__ = "product_input_fields"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    label = Column(String, nullable=False)
    type = Column(
        String, default="text", nullable=False
    )  # text, email, number, url, textarea
    placeholder = Column(String, nullable=True)
    is_required = Column(Boolean, default=True, nullable=False)
    sort_order = Column(Integer, default=0, nullable=False)

    # Relationship
    product = relationship("Product", back_populates="input_fields")
