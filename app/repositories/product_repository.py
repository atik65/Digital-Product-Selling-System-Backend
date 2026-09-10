from sqlalchemy.orm import Session
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductFilters
from app.schemas.pagination import PaginationParams
from app.core.exceptions import DatabaseException
from app.utils.pagination import get_paginated_response
from app.enums.product import Specification


class ProductRepository:
    # product Create
    def create(self, db: Session, product: ProductCreate):
        db_product = Product(**product)
        try:
            db.add(db_product)
            db.commit()
            db.refresh(db_product)
            return db_product
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Database error during product creation: {str(e)}",
                original_exception=e,
            )

    # get all products
    def get_products(
        self, db: Session, pagination: PaginationParams, filters: ProductFilters
    ):
        try:
            # Exclude soft-deleted products by default
            query = db.query(Product).filter(Product.is_deleted.is_(False))

            if filters.name:
                query = query.filter(Product.name.ilike(f"%{filters.name}%"))
            if filters.min_price is not None:
                query = query.filter(Product.price >= filters.min_price)
            if filters.max_price is not None:
                query = query.filter(Product.price <= filters.max_price)
        except Exception as e:
            raise DatabaseException(
                f"Database error during product retrieval: {str(e)}",
                original_exception=e,
            )

        total = query.count()
        items = query.offset(pagination.offset).limit(pagination.size).all()

        return get_paginated_response(items, total, pagination)

    # get product details
    def get_by_id(self, db: Session, product_id: int, include_deleted: bool = False):
        query = db.query(Product).filter(Product.id == product_id)
        if not include_deleted:
            query = query.filter(Product.is_deleted.is_(False))
        return query.first()

    # product Update
    def update(self, db: Session, product_id: int, data: ProductUpdate):
        product = self.get_by_id(db, product_id)
        if product:
            product_body = data.model_dump(exclude_unset=True)
            for key, value in product_body.items():
                setattr(product, key, value)
            try:
                db.commit()
                db.refresh(product)
            except Exception as e:
                db.rollback()
                raise DatabaseException(
                    f"Database error during product update: {str(e)}",
                    original_exception=e,
                )
        return product

    # get_products_by_spec
    def get_products_by_spec(
        self, db: Session, spec: Specification, pagination: PaginationParams
    ):
        try:
            query = db.query(Product).filter(
                Product.price == spec, Product.is_deleted.is_(False)
            )
        except Exception as e:
            raise DatabaseException(
                f"Database error during product retrieval: {str(e)}",
                original_exception=e,
            )

        total = query.count()
        items = query.offset(pagination.offset).limit(pagination.size).all()

        return get_paginated_response(items, total, pagination)

    # product Delete (Soft Delete by default)
    def delete(self, db: Session, product_id: int, hard_delete: bool = False):
        product = self.get_by_id(db, product_id)
        if product:
            try:
                if hard_delete:
                    db.delete(product)
                else:
                    product.soft_delete()
                db.commit()
            except Exception as e:
                db.rollback()
                raise DatabaseException(
                    f"Database error during product deletion: {str(e)}",
                    original_exception=e,
                )
        return product

    # product Restore
    def restore(self, db: Session, product_id: int):
        product = self.get_by_id(db, product_id, include_deleted=True)
        if product and product.is_deleted:
            try:
                product.restore()
                db.commit()
                db.refresh(product)
            except Exception as e:
                db.rollback()
                raise DatabaseException(
                    f"Database error during product restoration: {str(e)}",
                    original_exception=e,
                )
        return product
