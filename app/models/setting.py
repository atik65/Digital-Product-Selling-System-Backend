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
    telegram_channel_url = Column(String, nullable=True)
    telegram_support_url = Column(String, nullable=True)
    youtube_channel_url = Column(String, nullable=True)
    facebook_url = Column(String, nullable=True)
    support_phone = Column(String, nullable=True)
    support_email = Column(String, nullable=True)

    @property
    def telegram_url(self) -> str | None:
        """Backward-compatible alias for telegram_channel_url."""
        return self.telegram_channel_url

    @telegram_url.setter
    def telegram_url(self, value: str | None) -> None:
        self.telegram_channel_url = value
