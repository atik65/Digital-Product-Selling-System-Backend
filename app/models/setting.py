from sqlalchemy import Column, Integer, String
from app.models.base import BaseAuditModel


class SiteSetting(BaseAuditModel):
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, index=True)
    site_name = Column(String, default="Digital Product Platform", nullable=False)
    site_title = Column(
        String, default="Buy Digital Products & Subscriptions", nullable=False
    )
    logo = Column(String, nullable=True)
    favicon = Column(String, nullable=True)
    telegram_url = Column(String, nullable=True)
    facebook_url = Column(String, nullable=True)
    support_phone = Column(String, nullable=True)
    support_email = Column(String, nullable=True)
