from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.models.product import Product
from app.models.category import Category
from app.schemas.product import ProductFilters
from app.schemas.pagination import PaginationParams
from app.utils.pagination import get_paginated_response
from app.core.exceptions import DatabaseException


class ProductRepository:
    def create(self, db: Session, data: dict) -> Product:
        product = Product(**data)
        try:
            db.add(product)
            db.commit()
            db.refresh(product)
            return product
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to create product: {str(e)}", original_exception=e)

    def get_products(self, db: Session, pagination: PaginationParams, filters: ProductFilters):
        try:
            query = db.query(Product).filter(Product.is_deleted.is_(False))

            if filters.is_active is not None:
                query = query.filter(Product.is_active == filters.is_active)
            if filters.name:
                query = query.filter(Product.name.ilike(f"%{filters.name}%"))
            if filters.category_id:
                query = query.filter(Product.category_id == filters.category_id)
            if filters.category_slug:
                query = query.join(Product.category).filter(Category.slug == filters.category_slug)

            total = query.count()
            items = (
                query.options(joinedload(Product.category), joinedload(Product.packages))
                .order_by(Product.sort_order.asc(), Product.id.desc())
                .offset(pagination.offset)
                .limit(pagination.size)
                .all()
            )
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(f"Failed to fetch products: {str(e)}", original_exception=e)

    def get_by_id(self, db: Session, product_id: int, include_deleted: bool = False) -> Optional[Product]:
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.packages),
            joinedload(Product.input_fields),
        ).filter(Product.id == product_id)
        if not include_deleted:
            query = query.filter(Product.is_deleted.is_(False))
        return query.first()

    def get_by_slug(self, db: Session, slug: str, include_deleted: bool = False) -> Optional[Product]:
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.packages),
            joinedload(Product.input_fields),
        ).filter(Product.slug == slug)
        if not include_deleted:
            query = query.filter(Product.is_deleted.is_(False))
        return query.first()

    def update(self, db: Session, product: Product, data: dict) -> Product:
        try:
            for key, val in data.items():
                if val is not None and hasattr(product, key):
                    setattr(product, key, val)
            db.commit()
            db.refresh(product)
            return product
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to update product: {str(e)}", original_exception=e)

    def delete(self, db: Session, product_or_id) -> Optional[Product]:
        try:
            if isinstance(product_or_id, int):
                product = self.get_by_id(db, product_or_id)
            else:
                product = product_or_id
            if not product:
                return None
            product.soft_delete()
            db.commit()
            db.refresh(product)
            return product
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to delete product: {str(e)}", original_exception=e)

    def restore(self, db: Session, product_id: int) -> Optional[Product]:
        try:
            product = self.get_by_id(db, product_id, include_deleted=True)
            if not product:
                return None
            product.restore()
            db.commit()
            db.refresh(product)
            return product
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to restore product: {str(e)}", original_exception=e)
