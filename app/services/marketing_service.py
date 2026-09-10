from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.marketing_repository import MarketingRepository
from app.models.marketing import Banner, Popup
from app.schemas.marketing import BannerCreate, BannerUpdate, PopupCreate, PopupUpdate
from app.core.exceptions import NotFoundException


class MarketingService:
    def __init__(self):
        self.repo = MarketingRepository()

    # Banners
    def get_banners(self, db: Session, active_only: bool = True) -> List[Banner]:
        return self.repo.get_banners(db, active_only=active_only)

    def get_banner(self, db: Session, banner_id: int) -> Banner:
        banner = self.repo.get_banner_by_id(db, banner_id)
        if not banner:
            raise NotFoundException(f"Banner with id {banner_id} not found")
        return banner

    def create_banner(self, db: Session, data: BannerCreate) -> Banner:
        return self.repo.create_banner(db, data.model_dump())

    def update_banner(self, db: Session, banner_id: int, data: BannerUpdate) -> Banner:
        banner = self.get_banner(db, banner_id)
        return self.repo.update_banner(db, banner, data.model_dump(exclude_unset=True))

    def delete_banner(self, db: Session, banner_id: int) -> None:
        banner = self.get_banner(db, banner_id)
        self.repo.delete_banner(db, banner)

    # Popups
    def get_active_popup(self, db: Session) -> Optional[Popup]:
        return self.repo.get_active_popup(db)

    def get_all_popups(self, db: Session) -> List[Popup]:
        return self.repo.get_all_popups(db)

    def create_popup(self, db: Session, data: PopupCreate) -> Popup:
        return self.repo.create_popup(db, data.model_dump())

    def update_popup(self, db: Session, popup_id: int, data: PopupUpdate) -> Popup:
        popup = self.repo.get_popup_by_id(db, popup_id)
        if not popup:
            raise NotFoundException(f"Popup with id {popup_id} not found")
        return self.repo.update_popup(db, popup, data.model_dump(exclude_unset=True))
