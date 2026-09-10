from typing import List
from sqlalchemy.orm import Session
from app.repositories.payment_method_repository import PaymentMethodRepository
from app.models.payment_method import PaymentMethod
from app.schemas.payment_method import PaymentMethodCreate, PaymentMethodUpdate
from app.core.exceptions import NotFoundException


class PaymentMethodService:
    def __init__(self):
        self.repo = PaymentMethodRepository()

    def get_payment_methods(
        self, db: Session, active_only: bool = True
    ) -> List[PaymentMethod]:
        return self.repo.get_all(db, active_only=active_only)

    def get_by_id(self, db: Session, method_id: int) -> PaymentMethod:
        method = self.repo.get_by_id(db, method_id)
        if not method:
            raise NotFoundException(f"Payment method with id {method_id} not found")
        return method

    def create_payment_method(
        self, db: Session, data: PaymentMethodCreate
    ) -> PaymentMethod:
        return self.repo.create(db, data.model_dump())

    def update_payment_method(
        self, db: Session, method_id: int, data: PaymentMethodUpdate
    ) -> PaymentMethod:
        method = self.get_by_id(db, method_id)
        return self.repo.update(db, method, data.model_dump(exclude_unset=True))

    def delete_payment_method(self, db: Session, method_id: int) -> None:
        method = self.get_by_id(db, method_id)
        self.repo.delete(db, method)
