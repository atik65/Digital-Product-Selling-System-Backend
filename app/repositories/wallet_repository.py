from typing import Optional
from sqlalchemy.orm import Session
from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.schemas.pagination import PaginationParams
from app.utils.pagination import get_paginated_response
from app.core.exceptions import DatabaseException


class WalletRepository:
    def get_by_user_id(self, db: Session, user_id: int, for_update: bool = False) -> Optional[Wallet]:
        query = db.query(Wallet).filter(Wallet.user_id == user_id, Wallet.is_deleted.is_(False))
        if for_update:
            query = query.with_for_update()
        return query.first()

    def create_wallet(self, db: Session, user_id: int) -> Wallet:
        wallet = Wallet(user_id=user_id, balance=0.0)
        try:
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
            return wallet
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Failed to create wallet: {str(e)}", original_exception=e)

    def update_balance_with_transaction(
        self,
        db: Session,
        wallet: Wallet,
        amount: float,
        tx_type: str,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Wallet:
        try:
            balance_before = wallet.balance
            balance_after = round(balance_before + amount, 2)
            wallet.balance = balance_after

            transaction = WalletTransaction(
                wallet_id=wallet.id,
                type=tx_type,
                amount=amount,
                balance_before=balance_before,
                balance_after=balance_after,
                reference_type=reference_type,
                reference_id=reference_id,
                description=description,
            )
            db.add(transaction)
            db.commit()
            db.refresh(wallet)
            return wallet
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Atomic wallet balance update failed: {str(e)}", original_exception=e)

    def get_transactions(self, db: Session, wallet_id: int, pagination: PaginationParams):
        try:
            query = db.query(WalletTransaction).filter(WalletTransaction.wallet_id == wallet_id, WalletTransaction.is_deleted.is_(False))
            total = query.count()
            items = query.order_by(WalletTransaction.id.desc()).offset(pagination.offset).limit(pagination.size).all()
            return get_paginated_response(items, total, pagination)
        except Exception as e:
            raise DatabaseException(f"Failed to fetch wallet transactions: {str(e)}", original_exception=e)
