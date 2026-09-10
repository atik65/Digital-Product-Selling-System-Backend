from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductStatusUpdate,
    ProductFilters,
)
from app.schemas.pagination import PaginationParams
from app.core.exceptions import NotFoundException, ConflictException


class ProductService:
    def __init__(self):
        self.repo = ProductRepository()

    def get_products(
        self, db: Session, pagination: PaginationParams, filters: ProductFilters
    ):
        return self.repo.get_products(db, pagination, filters)

    def get_product_by_slug(self, db: Session, slug: str) -> Product:
        product = self.repo.get_by_slug(db, slug)
        if not product:
            raise NotFoundException(f"Product with slug '{slug}' not found")
        return product

    def get_product_by_id(self, db: Session, product_id: int) -> Product:
        product = self.repo.get_by_id(db, product_id)
        if not product:
            raise NotFoundException(f"Product with id {product_id} not found")
        return product

    def create_product(self, db: Session, data: ProductCreate) -> Product:
        existing = self.repo.get_by_slug(db, data.slug)
        if existing:
            raise ConflictException(f"Product with slug '{data.slug}' already exists")
        return self.repo.create(db, data.model_dump())

    def update_product(
        self, db: Session, product_id: int, data: ProductUpdate
    ) -> Product:
        product = self.get_product_by_id(db, product_id)
        update_dict = data.model_dump(exclude_unset=True)
        if "slug" in update_dict and update_dict["slug"] != product.slug:
            existing = self.repo.get_by_slug(db, update_dict["slug"])
            if existing:
                raise ConflictException(
                    f"Product with slug '{update_dict['slug']}' already exists"
                )
        return self.repo.update(db, product, update_dict)

    def update_status(
        self, db: Session, product_id: int, data: ProductStatusUpdate
    ) -> Product:
        product = self.get_product_by_id(db, product_id)
        return self.repo.update(db, product, {"is_active": data.is_active})

    def delete_product(self, db: Session, product_id: int) -> None:
        product = self.get_product_by_id(db, product_id)
        self.repo.delete(db, product)
