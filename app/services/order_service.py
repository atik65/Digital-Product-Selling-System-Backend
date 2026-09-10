import secrets
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.repositories.order_repository import OrderRepository
from app.repositories.package_repository import PackageRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.coupon_repository import CouponRepository
from app.models.order import Order
from app.schemas.order import (
    CheckoutPreviewRequest,
    CheckoutPreviewResponse,
    DirectOrderCreate,
    OrderStatusUpdate,
    OrderNoteUpdate,
)
from app.schemas.pagination import PaginationParams
from app.services.dynamic_input_service import DynamicInputService
from app.services.coupon_service import CouponService
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException


class OrderService:
    def __init__(self):
        self.order_repo = OrderRepository()
        self.package_repo = PackageRepository()
        self.product_repo = ProductRepository()
        self.coupon_repo = CouponRepository()
        self.coupon_service = CouponService()

    def _generate_order_number(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_hex = secrets.token_hex(3).upper()
        return f"ORD-{date_str}-{random_hex}"

    def preview_checkout(self, db: Session, req: CheckoutPreviewRequest, user_id: Optional[int] = None) -> CheckoutPreviewResponse:
        package = self.package_repo.get_by_id(db, req.package_id)
        if not package or not package.is_active:
            raise NotFoundException("Purchasable package not found or inactive")

        product = package.product
        if not product or not product.is_active:
            raise NotFoundException("Associated product is unavailable")

        # Validate inputs if provided
        validation_errors = []
        input_valid = True
        if req.input_values:
            try:
                DynamicInputService.validate_inputs(product.input_fields, req.input_values)
            except ValidationException as ve:
                input_valid = False
                validation_errors.append(str(ve))

        subtotal = round(package.price * req.quantity, 2)
        discount = 0.0
        applied_coupon_code = None

        if req.coupon_code:
            try:
                discount, coupon = self.coupon_service.validate_and_calculate_discount(
                    db, req.coupon_code, subtotal, user_id=user_id
                )
                applied_coupon_code = coupon.code
            except ValidationException as ve:
                validation_errors.append(str(ve))

        total = max(0.0, round(subtotal - discount, 2))

        return CheckoutPreviewResponse(
            package_id=package.id,
            package_name=package.name,
            product_name=product.name,
            unit_price=package.price,
            quantity=req.quantity,
            subtotal=subtotal,
            discount=discount,
            total=total,
            coupon_applied=applied_coupon_code,
            input_valid=input_valid,
            validation_errors=validation_errors if validation_errors else None,
        )

    def create_direct_order(self, db: Session, user_id: int, req: DirectOrderCreate) -> Order:
        package = self.package_repo.get_by_id(db, req.package_id)
        if not package or not package.is_active:
            raise NotFoundException("Purchasable package not found or inactive")

        product = package.product
        if not product or not product.is_active:
            raise NotFoundException("Associated product is unavailable")

        # Strict validation of dynamic product inputs
        sanitized_inputs = DynamicInputService.validate_inputs(product.input_fields, req.input_values)

        subtotal = round(package.price * req.quantity, 2)
        discount = 0.0
        coupon_id = None

        if req.coupon_code:
            discount, coupon = self.coupon_service.validate_and_calculate_discount(
                db, req.coupon_code, subtotal, user_id=user_id
            )
            coupon_id = coupon.id
            self.coupon_repo.increment_used_count(db, coupon.id)

        total_amount = max(0.0, round(subtotal - discount, 2))
        order_number = self._generate_order_number()

        order_data = {
            "user_id": user_id,
            "order_number": order_number,
            "subtotal": subtotal,
            "discount": discount,
            "total_amount": total_amount,
            "coupon_id": coupon_id,
            "status": "PAYMENT_PENDING",
            "customer_note": req.customer_note,
        }

        item_data = {
            "product_id": product.id,
            "package_id": package.id,
            "product_name": product.name,
            "package_name": package.name,
            "unit_price": package.price,
            "quantity": req.quantity,
            "total_price": subtotal,
            "input_values": sanitized_inputs,
        }

        return self.order_repo.create_order(db, order_data, item_data)

    def get_order_by_number(self, db: Session, order_number: str, user_id: Optional[int] = None) -> Order:
        order = self.order_repo.get_by_order_number(db, order_number)
        if not order:
            raise NotFoundException(f"Order '{order_number}' not found")
        if user_id and order.user_id != user_id:
            raise ForbiddenException("You do not have permission to view this order")
        return order

    def get_user_orders(self, db: Session, user_id: int, pagination: PaginationParams, status: Optional[str] = None):
        return self.order_repo.get_user_orders(db, user_id, pagination, status)

    def get_all_orders(self, db: Session, pagination: PaginationParams, status: Optional[str] = None, search: Optional[str] = None):
        return self.order_repo.get_all_orders(db, pagination, status, search)

    def update_order_status(self, db: Session, order_id: int, data: OrderStatusUpdate) -> Order:
        order = self.order_repo.get_by_id(db, order_id)
        if not order:
            raise NotFoundException(f"Order with id {order_id} not found")
        return self.order_repo.update_status(db, order, data.status)

    def update_admin_note(self, db: Session, order_id: int, data: OrderNoteUpdate) -> Order:
        order = self.order_repo.get_by_id(db, order_id)
        if not order:
            raise NotFoundException(f"Order with id {order_id} not found")
        return self.order_repo.update_admin_note(db, order, data.admin_note)

    def cancel_order(self, db: Session, order_number: str, user_id: int) -> Order:
        order = self.get_order_by_number(db, order_number, user_id=user_id)
        if order.status not in ["PENDING", "PAYMENT_PENDING"]:
            raise ValidationException(f"Cannot cancel order in status '{order.status}'")
        return self.order_repo.update_status(db, order, "CANCELLED")
