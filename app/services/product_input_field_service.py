from typing import List
from sqlalchemy.orm import Session
from app.repositories.product_input_field_repository import ProductInputFieldRepository
from app.models.product_input_field import ProductInputField
from app.schemas.product_input_field import InputFieldCreate, InputFieldUpdate
from app.core.exceptions import NotFoundException


class ProductInputFieldService:
    def __init__(self):
        self.repo = ProductInputFieldRepository()

    def get_fields(self, db: Session, product_id: int) -> List[ProductInputField]:
        return self.repo.get_by_product_id(db, product_id)

    def get_by_id(self, db: Session, field_id: int) -> ProductInputField:
        field = self.repo.get_by_id(db, field_id)
        if not field:
            raise NotFoundException(f"Input field with id {field_id} not found")
        return field

    def create_field(self, db: Session, product_id: int, data: InputFieldCreate) -> ProductInputField:
        f_dict = data.model_dump()
        f_dict["product_id"] = product_id
        return self.repo.create(db, f_dict)

    def update_field(self, db: Session, field_id: int, data: InputFieldUpdate) -> ProductInputField:
        field = self.get_by_id(db, field_id)
        return self.repo.update(db, field, data.model_dump(exclude_unset=True))

    def delete_field(self, db: Session, field_id: int) -> None:
        field = self.get_by_id(db, field_id)
        self.repo.delete(db, field)
