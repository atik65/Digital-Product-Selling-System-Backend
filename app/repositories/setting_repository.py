from sqlalchemy.orm import Session
from app.models.setting import SiteSetting
from app.core.exceptions import DatabaseException


class SettingRepository:
    def get_or_create(self, db: Session) -> SiteSetting:
        try:
            setting = db.query(SiteSetting).first()
            if not setting:
                setting = SiteSetting()
                db.add(setting)
                db.commit()
                db.refresh(setting)
            return setting
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to load site settings: {str(e)}", original_exception=e
            )

    def update(self, db: Session, setting: SiteSetting, data: dict) -> SiteSetting:
        try:
            for key, val in data.items():
                if val is not None and hasattr(setting, key):
                    setattr(setting, key, val)
            db.commit()
            db.refresh(setting)
            return setting
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update site settings: {str(e)}", original_exception=e
            )
