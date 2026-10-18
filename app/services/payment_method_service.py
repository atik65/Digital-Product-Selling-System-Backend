from typing import List
from sqlalchemy.orm import Session
from app.repositories.payment_method_repository import PaymentMethodRepository
from app.models.payment_method import PaymentMethod
from app.schemas.payment_method import (
    PaymentMethodAdminResponse,
    PaymentMethodCreate,
    PaymentMethodUpdate,
)
from app.services.payment_transaction_service import PaymentTransactionService
from app.core.exceptions import NotFoundException


class PaymentMethodService:
    def __init__(self):
        self.repo = PaymentMethodRepository()
        self.transaction_service = PaymentTransactionService()

    def with_usage(
        self, db: Session, methods: List[PaymentMethod]
    ) -> List[PaymentMethodAdminResponse]:
        """Admin view of payment methods with daily / monthly transaction counts."""
        return self.transaction_service.attach_usage(db, methods)

    def with_usage_single(
        self, db: Session, method: PaymentMethod
    ) -> PaymentMethodAdminResponse:
        return self.with_usage(db, [method])[0]

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
