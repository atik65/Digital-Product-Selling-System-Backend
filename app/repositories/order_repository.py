from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.pagination import PaginationParams
from app.utils.pagination import get_paginated_response
from app.core.exceptions import DatabaseException


class OrderRepository:
    def create_order(self, db: Session, order_data: dict, item_data: dict) -> Order:
        try:
            order = Order(**order_data)
            db.add(order)
            db.flush()  # Generate order.id

            item_data["order_id"] = order.id
            item = OrderItem(**item_data)
            db.add(item)

            db.commit()
            db.refresh(order)
            return order
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to create order: {str(e)}", original_exception=e
            )

    def get_by_id(self, db: Session, order_id: int) -> Optional[Order]:
        return (
            db.query(Order)
            .options(joinedload(Order.items), joinedload(Order.payments))
            .filter(Order.id == order_id, Order.is_deleted.is_(False))
            .first()
        )

    def get_by_order_number(self, db: Session, order_number: str) -> Optional[Order]:
        return (
            db.query(Order)
            .options(joinedload(Order.items), joinedload(Order.payments))
            .filter(Order.order_number == order_number, Order.is_deleted.is_(False))
            .first()
        )

    def get_user_orders(
        self,
        db: Session,
        user_id: int,
        pagination: PaginationParams,
        status: Optional[str] = None,
    ):
        try:
            query = (
                db.query(Order)
                .options(joinedload(Order.items))
                .filter(Order.user_id == user_id, Order.is_deleted.is_(False))
            )
            if status:
                query = query.filter(Order.status == status)

            total = query.count()
            items = (
                query.order_by(Order.id.desc())
                .offset(pagination.offset)
                .limit(pagination.size)
                .all()
            )
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(
                f"Failed to fetch customer orders: {str(e)}", original_exception=e
            )

    def get_all_orders(
        self,
        db: Session,
        pagination: PaginationParams,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ):
        try:
            query = (
                db.query(Order)
                .options(joinedload(Order.items), joinedload(Order.user))
                .filter(Order.is_deleted.is_(False))
            )
            if status:
                query = query.filter(Order.status == status)
            if search:
                query = query.filter(Order.order_number.ilike(f"%{search}%"))

            total = query.count()
            items = (
                query.order_by(Order.id.desc())
                .offset(pagination.offset)
                .limit(pagination.size)
                .all()
            )
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(
                f"Failed to fetch orders: {str(e)}", original_exception=e
            )

    def update_status(self, db: Session, order: Order, new_status: str) -> Order:
        try:
            order.status = new_status
            db.commit()
            db.refresh(order)
            return order
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update order status: {str(e)}", original_exception=e
            )

    def update_admin_note(self, db: Session, order: Order, note: str) -> Order:
        try:
            order.admin_note = note
            db.commit()
            db.refresh(order)
            return order
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Failed to update order note: {str(e)}", original_exception=e
            )

    def count_user_coupon_uses(self, db: Session, user_id: int, coupon_id: int) -> int:
        return (
            db.query(Order)
            .filter(
                Order.user_id == user_id,
                Order.coupon_id == coupon_id,
                Order.status.notin_(["CANCELLED", "FAILED"]),
                Order.is_deleted.is_(False),
            )
            .count()
        )

    def count_user_completed_orders(self, db: Session, user_id: int) -> int:
        return (
            db.query(Order)
            .filter(
                Order.user_id == user_id,
                Order.status.in_(["PAID", "PROCESSING", "COMPLETED"]),
                Order.is_deleted.is_(False),
            )
            .count()
        )
