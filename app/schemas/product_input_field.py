from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class InputFieldBase(BaseModel):
    name: str
    label: str
    type: str = "text"  # text, email, number, url, textarea
    placeholder: Optional[str] = None
    is_required: bool = True
    sort_order: int = 0


class InputFieldCreate(InputFieldBase):
    pass


class InputFieldUpdate(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    type: Optional[str] = None
    placeholder: Optional[str] = None
    is_required: Optional[bool] = None
    sort_order: Optional[int] = None


class InputFieldResponse(InputFieldBase):
    id: int
    product_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
