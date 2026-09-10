from sqlalchemy.orm import Session
from app.repositories.wallet_repository import WalletRepository
from app.repositories.order_repository import OrderRepository
from app.models.wallet import Wallet
from app.schemas.wallet import WalletAdjustRequest
from app.schemas.pagination import PaginationParams
from app.core.exceptions import NotFoundException, ValidationException, ForbiddenException


class WalletService:
    def __init__(self):
        self.wallet_repo = WalletRepository()
        self.order_repo = OrderRepository()

    def get_user_wallet(self, db: Session, user_id: int) -> Wallet:
        wallet = self.wallet_repo.get_by_user_id(db, user_id)
        if not wallet:
            wallet = self.wallet_repo.create_wallet(db, user_id)
        return wallet

    def get_transactions(self, db: Session, user_id: int, pagination: PaginationParams):
        wallet = self.get_user_wallet(db, user_id)
        return self.wallet_repo.get_transactions(db, wallet.id, pagination)

    def pay_order_with_wallet(self, db: Session, user_id: int, order_number: str) -> dict:
        """Atomically pays for an order using customer wallet balance."""
        order = self.order_repo.get_by_order_number(db, order_number)
        if not order:
            raise NotFoundException(f"Order '{order_number}' not found")
        if order.user_id != user_id:
            raise ForbiddenException("You cannot pay for an order that is not yours")
        if order.status not in ["PENDING", "PAYMENT_PENDING"]:
            raise ValidationException(f"Order is already '{order.status}'")

        # Row-level lock to prevent concurrent double-spend
        wallet = self.wallet_repo.get_by_user_id(db, user_id, for_update=True)
        if not wallet or wallet.balance < order.total_amount:
            raise ValidationException(
                f"Insufficient wallet balance. Required: {order.total_amount}, Available: {wallet.balance if wallet else 0}"
            )

        # Atomic debit and ledger record
        self.wallet_repo.update_balance_with_transaction(
            db,
            wallet=wallet,
            amount=-order.total_amount,
            tx_type="PURCHASE",
            reference_type="order",
            reference_id=order.order_number,
            description=f"Payment for Order #{order.order_number}",
        )

        # Mark order as PAID
        self.order_repo.update_status(db, order, "PAID")

        return {
            "success": True,
            "order_number": order.order_number,
            "amount_paid": order.total_amount,
            "remaining_balance": wallet.balance,
        }

    def admin_adjust_balance(self, db: Session, user_id: int, req: WalletAdjustRequest) -> Wallet:
        wallet = self.wallet_repo.get_by_user_id(db, user_id, for_update=True)
        if not wallet:
            wallet = self.wallet_repo.create_wallet(db, user_id)

        new_balance = wallet.balance + req.amount
        if new_balance < 0:
            raise ValidationException(f"Adjustment cannot result in negative balance: {new_balance}")

        return self.wallet_repo.update_balance_with_transaction(
            db,
            wallet=wallet,
            amount=req.amount,
            tx_type=req.type,
            reference_type="admin_adjustment",
            description=req.description,
        )
