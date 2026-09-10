from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from app.models.base import BaseAuditModel


class Banner(BaseAuditModel):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, index=True)
    image = Column(String, nullable=False)
    mobile_image = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    button_text = Column(String, nullable=True)
    button_url = Column(String, nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class Popup(BaseAuditModel):
    __tablename__ = "popups"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    image = Column(String, nullable=True)
    button_text = Column(String, nullable=True)
    button_url = Column(String, nullable=True)
    display_type = Column(String, default="ON_FIRST_VISIT", nullable=False)  # ON_FIRST_VISIT, ONCE_PER_USER, AFTER_X_SECONDS
    starts_at = Column(DateTime(timezone=True), nullable=True)
    ends_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
