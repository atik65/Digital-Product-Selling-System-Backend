from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class PackageBase(BaseModel):
    name: str
    price: float
    compare_price: Optional[float] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class PackageCreate(PackageBase):
    product_id: Optional[int] = None


class PackageUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    compare_price: Optional[float] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PackageStatusUpdate(BaseModel):
    is_active: bool


class PackageResponse(PackageBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
