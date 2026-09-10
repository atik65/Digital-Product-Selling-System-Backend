from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.category import Category
from app.core.exceptions import DatabaseException


class CategoryRepository:
    def get_all(self, db: Session, active_only: bool = True) -> List[Category]:
        try:
            query = db.query(Category).filter(Category.is_deleted.is_(False))
            if active_only:
                query = query.filter(Category.is_active.is_(True))
            return query.order_by(Category.sort_order.asc(), Category.id.desc()).all()
        except Exception as e:
            raise DatabaseException(
                f"Failed to fetch categories: {str(e)}", original_exception=e
            )

    def get_by_id(self, db: Session, category_id: int) -> Optional[Category]:
        return (
            db.query(Category)
            .filter(Category.id == category_id, Category.is_deleted.is_(False))
            .first()
        )

    def get_by_slug(self, db: Session, slug: str) -> Optional[Category]:
        return (
            db.query(Category)
            .filter(Category.slug == slug, Category.is_deleted.is_(False))
            .first()
        )

    def create(self, db: Session, data: dict) -> Category:
        category = Category(**data)
        try:
            db.add(category)
            db.commit()
            db.refresh(category)
            return category
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create category: {str(e)}", original_exception=e
            )

    def update(self, db: Session, category: Category, data: dict) -> Category:
        try:
            for key, val in data.items():
                if val is not None and hasattr(category, key):
                    setattr(category, key, val)
            db.commit()
            db.refresh(category)
            return category
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update category: {str(e)}", original_exception=e
            )

    def delete(self, db: Session, category: Category) -> None:
        try:
            category.soft_delete()
            db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to delete category: {str(e)}", original_exception=e
            )
