from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.product_input_field import ProductInputField
from app.core.exceptions import DatabaseException


class ProductInputFieldRepository:
    def get_by_product_id(
        self, db: Session, product_id: int
    ) -> List[ProductInputField]:
        return (
            db.query(ProductInputField)
            .filter(
                ProductInputField.product_id == product_id,
                ProductInputField.is_deleted.is_(False),
            )
            .order_by(ProductInputField.sort_order.asc())
            .all()
        )

    def get_by_id(self, db: Session, field_id: int) -> Optional[ProductInputField]:
        return (
            db.query(ProductInputField)
            .filter(
                ProductInputField.id == field_id,
                ProductInputField.is_deleted.is_(False),
            )
            .first()
        )

    def create(self, db: Session, data: dict) -> ProductInputField:
        field = ProductInputField(**data)
        try:
            db.add(field)
            db.commit()
            db.refresh(field)
            return field
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create input field: {str(e)}", original_exception=e
            )

    def update(
        self, db: Session, field: ProductInputField, data: dict
    ) -> ProductInputField:
        try:
            for key, val in data.items():
                if val is not None and hasattr(field, key):
                    setattr(field, key, val)
            db.commit()
            db.refresh(field)
            return field
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update input field: {str(e)}", original_exception=e
            )

    def delete(self, db: Session, field: ProductInputField) -> None:
        try:
            field.soft_delete()
            db.commit()
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to delete input field: {str(e)}", original_exception=e
            )
