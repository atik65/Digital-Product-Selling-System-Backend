from typing import List
from sqlalchemy.orm import Session
from app.repositories.category_repository import CategoryRepository
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryReorder
from app.core.exceptions import NotFoundException, ConflictException


class CategoryService:
    def __init__(self):
        self.repo = CategoryRepository()

    def get_categories(self, db: Session, active_only: bool = True) -> List[Category]:
        return self.repo.get_all(db, active_only=active_only)

    def get_by_slug(self, db: Session, slug: str) -> Category:
        category = self.repo.get_by_slug(db, slug)
        if not category:
            raise NotFoundException(f"Category with slug '{slug}' not found")
        return category

    def get_by_id(self, db: Session, category_id: int) -> Category:
        category = self.repo.get_by_id(db, category_id)
        if not category:
            raise NotFoundException(f"Category with id {category_id} not found")
        return category

    def create_category(self, db: Session, data: CategoryCreate) -> Category:
        existing = self.repo.get_by_slug(db, data.slug)
        if existing:
            raise ConflictException(f"Category with slug '{data.slug}' already exists")
        return self.repo.create(db, data.model_dump())

    def update_category(
        self, db: Session, category_id: int, data: CategoryUpdate
    ) -> Category:
        category = self.get_by_id(db, category_id)
        update_dict = data.model_dump(exclude_unset=True)
        if "slug" in update_dict and update_dict["slug"] != category.slug:
            existing = self.repo.get_by_slug(db, update_dict["slug"])
            if existing:
                raise ConflictException(
                    f"Category with slug '{update_dict['slug']}' already exists"
                )
        return self.repo.update(db, category, update_dict)

    def reorder_category(
        self, db: Session, category_id: int, data: CategoryReorder
    ) -> Category:
        category = self.get_by_id(db, category_id)
        return self.repo.update(db, category, {"sort_order": data.sort_order})

    def delete_category(self, db: Session, category_id: int) -> None:
        category = self.get_by_id(db, category_id)
        self.repo.delete(db, category)
