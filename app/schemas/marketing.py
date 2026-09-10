from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BannerBase(BaseModel):
    image: str
    mobile_image: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class BannerCreate(BannerBase):
    pass


class BannerUpdate(BaseModel):
    image: Optional[str] = None
    mobile_image: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class BannerResponse(BannerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PopupBase(BaseModel):
    title: str
    content: Optional[str] = None
    image: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None
    display_type: str = (
        "ON_FIRST_VISIT"  # ON_FIRST_VISIT, ONCE_PER_USER, AFTER_X_SECONDS
    )
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: bool = True


class PopupCreate(PopupBase):
    pass


class PopupUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    image: Optional[str] = None
    button_text: Optional[str] = None
    button_url: Optional[str] = None
    display_type: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None


class PopupResponse(PopupBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
