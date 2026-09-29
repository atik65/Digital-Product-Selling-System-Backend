from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, model_validator


class SiteSettingBase(BaseModel):
    site_name: str = "Digital Product Platform"
    site_title: str = "Buy Digital Products & Subscriptions"
    logo: Optional[str] = None
    favicon: Optional[str] = None
    telegram_channel_url: Optional[str] = None
    telegram_support_url: Optional[str] = None
    youtube_channel_url: Optional[str] = None
    facebook_url: Optional[str] = None
    support_phone: Optional[str] = None
    support_email: Optional[str] = None
    telegram_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def populate_telegram_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get("telegram_channel_url") and not data.get("telegram_url"):
                data["telegram_url"] = data.get("telegram_channel_url")
            elif data.get("telegram_url") and not data.get("telegram_channel_url"):
                data["telegram_channel_url"] = data.get("telegram_url")
        return data


class SiteSettingUpdate(BaseModel):
    site_name: Optional[str] = None
    site_title: Optional[str] = None
    logo: Optional[str] = None
    favicon: Optional[str] = None
    telegram_channel_url: Optional[str] = None
    telegram_support_url: Optional[str] = None
    youtube_channel_url: Optional[str] = None
    facebook_url: Optional[str] = None
    support_phone: Optional[str] = None
    support_email: Optional[str] = None
    telegram_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def populate_telegram_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "telegram_url" in data and "telegram_channel_url" not in data:
                data["telegram_channel_url"] = data["telegram_url"]
            elif "telegram_channel_url" in data and "telegram_url" not in data:
                data["telegram_url"] = data["telegram_channel_url"]
        return data


class SiteSettingResponse(SiteSettingBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
