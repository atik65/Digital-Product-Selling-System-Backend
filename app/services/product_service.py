from app.core.exceptions import ValidationException
from sqlalchemy.orm import Session
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductFilters
from app.schemas.pagination import PaginationParams
from app.enums.product import Specification
from fastapi import Response


class ProductService:
    def __init__(self):
        self.repo = ProductRepository()

    def create_product(self, db: Session, product: ProductCreate):
        product_dict = product.model_dump()
        return self.repo.create(db, product_dict)

    def get_products(
        self, db: Session, pagination: PaginationParams, filters: ProductFilters
    ):
        return self.repo.get_products(db, pagination, filters)

    def get_product(self, db: Session, product_id: int):
        return self.repo.get_by_id(db, product_id)

    def update_product(self, db: Session, product_id: int, data: ProductUpdate):
        product_body = data.model_dump(exclude_unset=True)

        if not product_body:
            raise ValidationException("No fields provided to update")

        return self.repo.update(db, product_id, data)

    def get_products_by_spec(
        self,
        db: Session,
        spec: Specification,
        pagination: PaginationParams,
        response: Response,
    ):
        products = self.repo.get_products_by_spec(db, spec, pagination)
        response.headers["X-Total-Count"] = str(len(products))
        return products

    def delete_product(self, db: Session, product_id: int):
        return self.repo.delete(db, product_id)
