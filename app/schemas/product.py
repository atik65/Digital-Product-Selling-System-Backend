from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.package import PackageResponse
from app.schemas.product_input_field import InputFieldResponse
from app.schemas.category import CategoryResponse


class ProductBase(BaseModel):
    name: str
    slug: str
    category_id: Optional[int] = None
    image: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    category_id: Optional[int] = None
    image: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class ProductStatusUpdate(BaseModel):
    is_active: bool


class ProductCardResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None
    packages: List[PackageResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductDetailResponse(ProductCardResponse):
    input_fields: List[InputFieldResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductFilters(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    category_slug: Optional[str] = None
    is_active: Optional[bool] = None
