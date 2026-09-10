from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from fastapi import Query


class ProductBase(BaseModel):
    name: str = Field(
        min_length=1,
        title="Product name",
        description="Enter product name",
        examples=["Laptop", "Mouse", "Keyboard", "Monitor"],
    )
    description: str = Field(
        min_length=1,
        title="Product description",
        description="Enter product description",
        examples=["Product description", "Product description"],
    )
    price: float = Field(
        gt=0,
        title="Product price",
        description="Enter product price",
        examples=[1000, 2000, 3000, 4000],
    )
    stock_quantity: int = Field(
        ge=0,
        title="Product stock quantity",
        description="Enter product stock quantity",
        examples=[10, 20, 30, 40],
    )
    image_url: str | None = Field(
        default=None,
        title="Product image URL",
        description="Public URL of the product image",
        examples=["/media/products/3a4b5c6d.jpg"],
    )


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductUpdate(ProductBase):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    stock_quantity: int | None = None
    image_url: str | None = None


class ProductFilters:
    def __init__(
        self,
        name: str | None = Query(
            None, description="Filter products by name (case-insensitive contains)"
        ),
        min_price: float | None = Query(
            None, description="Minimum price filter", alias="min-price"
        ),
        max_price: float | None = Query(
            None, description="Maximum price filter", alias="max-price"
        ),
    ):
        self.name = name
        self.min_price = min_price
        self.max_price = max_price
