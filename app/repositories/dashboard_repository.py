from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User
from app.models.topup import TopUp
from app.core.exceptions import DatabaseException


class DashboardRepository:
    def get_summary(self, db: Session) -> dict:
        try:
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

            # Today's orders count
            today_orders = (
                db.query(func.count(Order.id))
                .filter(Order.created_at >= today_start, Order.is_deleted.is_(False))
                .scalar()
                or 0
            )

            # Today's sales sum (paid orders)
            today_sales = (
                db.query(func.sum(Order.total_amount))
                .filter(
                    Order.created_at >= today_start,
                    Order.status.in_(["PAID", "PROCESSING", "COMPLETED"]),
                    Order.is_deleted.is_(False),
                )
                .scalar()
                or 0.0
            )

            # Pending payments
            pending_payments = (
                db.query(func.count(Payment.id))
                .filter(Payment.status == "VERIFYING", Payment.is_deleted.is_(False))
                .scalar()
                or 0
            )

            # Pending orders
            pending_orders = (
                db.query(func.count(Order.id))
                .filter(Order.status.in_(["PENDING", "PAYMENT_PENDING"]), Order.is_deleted.is_(False))
                .scalar()
                or 0
            )

            # Total active customers
            total_users = (
                db.query(func.count(User.id))
                .filter(User.role == "customer", User.is_deleted.is_(False))
                .scalar()
                or 0
            )

            # Pending wallet top-ups
            pending_topups = (
                db.query(func.count(TopUp.id))
                .filter(TopUp.status == "PENDING", TopUp.is_deleted.is_(False))
                .scalar()
                or 0
            )

            return {
                "today_orders": int(today_orders),
                "today_sales": round(float(today_sales), 2),
                "pending_payments": int(pending_payments),
                "pending_orders": int(pending_orders),
                "total_users": int(total_users),
                "pending_topups": int(pending_topups),
            }
        except Exception as e:
            raise DatabaseException(f"Failed to calculate dashboard summary: {str(e)}", original_exception=e)

    def get_recent_activity(self, db: Session, limit: int = 5) -> dict:
        try:
            recent_orders = (
                db.query(Order)
                .filter(Order.is_deleted.is_(False))
                .order_by(Order.id.desc())
                .limit(limit)
                .all()
            )
            recent_payments = (
                db.query(Payment)
                .filter(Payment.is_deleted.is_(False))
                .order_by(Payment.id.desc())
                .limit(limit)
                .all()
            )

            return {
                "recent_orders": [
                    {
                        "id": o.id,
                        "order_number": o.order_number,
                        "total_amount": o.total_amount,
                        "status": o.status,
                        "created_at": o.created_at.isoformat() if o.created_at else None,
                    }
                    for o in recent_orders
                ],
                "recent_payments": [
                    {
                        "id": p.id,
                        "order_id": p.order_id,
                        "amount": p.amount,
                        "transaction_id": p.transaction_id,
                        "status": p.status,
                        "created_at": p.created_at.isoformat() if p.created_at else None,
                    }
                    for p in recent_payments
                ],
            }
        except Exception as e:
            raise DatabaseException(f"Failed to fetch recent activity: {str(e)}", original_exception=e)
