from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SiteSettingBase(BaseModel):
    site_name: str = "Digital Product Platform"
    site_title: str = "Buy Digital Products & Subscriptions"
    logo: Optional[str] = None
    favicon: Optional[str] = None
    telegram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    support_phone: Optional[str] = None
    support_email: Optional[str] = None


class SiteSettingUpdate(BaseModel):
    site_name: Optional[str] = None
    site_title: Optional[str] = None
    logo: Optional[str] = None
    favicon: Optional[str] = None
    telegram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    support_phone: Optional[str] = None
    support_email: Optional[str] = None


class SiteSettingResponse(SiteSettingBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
