from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.marketing import Banner, Popup
from app.core.exceptions import DatabaseException


class MarketingRepository:
    # Banners
    def get_banners(self, db: Session, active_only: bool = True) -> List[Banner]:
        query = db.query(Banner).filter(Banner.is_deleted.is_(False))
        if active_only:
            query = query.filter(Banner.is_active.is_(True))
        return query.order_by(Banner.sort_order.asc(), Banner.id.desc()).all()

    def get_banner_by_id(self, db: Session, banner_id: int) -> Optional[Banner]:
        return (
            db.query(Banner)
            .filter(Banner.id == banner_id, Banner.is_deleted.is_(False))
            .first()
        )

    def create_banner(self, db: Session, data: dict) -> Banner:
        banner = Banner(**data)
        try:
            db.add(banner)
            db.commit()
            db.refresh(banner)
            return banner
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create banner: {str(e)}", original_exception=e
            )

    def update_banner(self, db: Session, banner: Banner, data: dict) -> Banner:
        try:
            for key, val in data.items():
                if val is not None and hasattr(banner, key):
                    setattr(banner, key, val)
            db.commit()
            db.refresh(banner)
            return banner
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update banner: {str(e)}", original_exception=e
            )

    def delete_banner(self, db: Session, banner: Banner) -> None:
        try:
            banner.soft_delete()
            db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to delete banner: {str(e)}", original_exception=e
            )

    # Popups
    def get_active_popup(self, db: Session) -> Optional[Popup]:
        now = datetime.now(timezone.utc)
        return (
            db.query(Popup)
            .filter(
                Popup.is_active.is_(True),
                Popup.is_deleted.is_(False),
                (Popup.starts_at.is_(None) | (Popup.starts_at <= now)),
                (Popup.ends_at.is_(None) | (Popup.ends_at >= now)),
            )
            .order_by(Popup.id.desc())
            .first()
        )

    def get_all_popups(self, db: Session) -> List[Popup]:
        return (
            db.query(Popup)
            .filter(Popup.is_deleted.is_(False))
            .order_by(Popup.id.desc())
            .all()
        )

    def get_popup_by_id(self, db: Session, popup_id: int) -> Optional[Popup]:
        return (
            db.query(Popup)
            .filter(Popup.id == popup_id, Popup.is_deleted.is_(False))
            .first()
        )

    def create_popup(self, db: Session, data: dict) -> Popup:
        popup = Popup(**data)
        try:
            db.add(popup)
            db.commit()
            db.refresh(popup)
            return popup
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create popup: {str(e)}", original_exception=e
            )

    def update_popup(self, db: Session, popup: Popup, data: dict) -> Popup:
        try:
            for key, val in data.items():
                if val is not None and hasattr(popup, key):
                    setattr(popup, key, val)
            db.commit()
            db.refresh(popup)
            return popup
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update popup: {str(e)}", original_exception=e
            )
