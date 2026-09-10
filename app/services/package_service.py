from typing import List
from sqlalchemy.orm import Session
from app.repositories.package_repository import PackageRepository
from app.models.package import Package
from app.schemas.package import PackageCreate, PackageUpdate, PackageStatusUpdate
from app.core.exceptions import NotFoundException


class PackageService:
    def __init__(self):
        self.repo = PackageRepository()

    def get_packages_for_product(self, db: Session, product_id: int, active_only: bool = True) -> List[Package]:
        return self.repo.get_by_product_id(db, product_id, active_only=active_only)

    def get_by_id(self, db: Session, package_id: int) -> Package:
        package = self.repo.get_by_id(db, package_id)
        if not package:
            raise NotFoundException(f"Package with id {package_id} not found")
        return package

    def create_package(self, db: Session, product_id: int, data: PackageCreate) -> Package:
        pkg_dict = data.model_dump()
        pkg_dict["product_id"] = product_id
        return self.repo.create(db, pkg_dict)

    def update_package(self, db: Session, package_id: int, data: PackageUpdate) -> Package:
        package = self.get_by_id(db, package_id)
        return self.repo.update(db, package, data.model_dump(exclude_unset=True))

    def update_status(self, db: Session, package_id: int, data: PackageStatusUpdate) -> Package:
        package = self.get_by_id(db, package_id)
        return self.repo.update(db, package, {"is_active": data.is_active})

    def delete_package(self, db: Session, package_id: int) -> None:
        package = self.get_by_id(db, package_id)
        self.repo.delete(db, package)
