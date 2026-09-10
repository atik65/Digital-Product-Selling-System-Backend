from sqlalchemy.orm import Session
from app.repositories.setting_repository import SettingRepository
from app.models.setting import SiteSetting
from app.schemas.setting import SiteSettingUpdate


class SettingService:
    def __init__(self):
        self.repo = SettingRepository()

    def get_settings(self, db: Session) -> SiteSetting:
        return self.repo.get_or_create(db)

    def update_settings(self, db: Session, data: SiteSettingUpdate) -> SiteSetting:
        setting = self.get_settings(db)
        return self.repo.update(db, setting, data.model_dump(exclude_unset=True))
