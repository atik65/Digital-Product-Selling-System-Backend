from sqlalchemy import Column, Integer, String, Float
from app.models.base import BaseAuditModel


class Product(BaseAuditModel):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, default="")
    description = Column(String, nullable=False, default="")
    price = Column(Float, nullable=False, default=0.0)
    stock_quantity = Column(Integer, nullable=False, default=0)
    image_url = Column(String, nullable=True)
