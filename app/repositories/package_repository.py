from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.package import Package
from app.core.exceptions import DatabaseException


class PackageRepository:
    def get_by_product_id(
        self, db: Session, product_id: int, active_only: bool = True
    ) -> List[Package]:
        query = db.query(Package).filter(
            Package.product_id == product_id, Package.is_deleted.is_(False)
        )
        if active_only:
            query = query.filter(Package.is_active.is_(True))
        return query.order_by(Package.sort_order.asc(), Package.price.asc()).all()

    def get_by_id(self, db: Session, package_id: int) -> Optional[Package]:
        return (
            db.query(Package)
            .filter(Package.id == package_id, Package.is_deleted.is_(False))
            .first()
        )

    def create(self, db: Session, data: dict) -> Package:
        package = Package(**data)
        try:
            db.add(package)
            db.commit()
            db.refresh(package)
            return package
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create package: {str(e)}", original_exception=e
            )

    def update(self, db: Session, package: Package, data: dict) -> Package:
        try:
            for key, val in data.items():
                if val is not None and hasattr(package, key):
                    setattr(package, key, val)
            db.commit()
            db.refresh(package)
            return package
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update package: {str(e)}", original_exception=e
            )

    def delete(self, db: Session, package: Package) -> None:
        try:
            package.soft_delete()
            db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to delete package: {str(e)}", original_exception=e
            )
