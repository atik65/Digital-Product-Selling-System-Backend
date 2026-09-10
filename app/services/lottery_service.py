import random
from typing import Optional, List
from sqlalchemy.orm import Session

from app.repositories.lottery_repository import LotteryRepository
from app.repositories.order_repository import OrderRepository
from app.models.lottery import Lottery, LotteryPrize, LotteryEntry
from app.schemas.lottery import (
    LotteryCreate,
    LotteryPrizeCreate,
    LotteryEligibilityResponse,
    LotterySpinResponse,
    LotteryPrizeResponse,
)
from app.schemas.pagination import PaginationParams
from app.core.exceptions import NotFoundException, ValidationException


class LotteryService:
    def __init__(self):
        self.lottery_repo = LotteryRepository()
        self.order_repo = OrderRepository()

    def get_active_lottery(self, db: Session) -> Optional[Lottery]:
        return self.lottery_repo.get_active_lottery(db)

    def check_user_eligibility(self, db: Session, user_id: int) -> LotteryEligibilityResponse:
        lottery = self.get_active_lottery(db)
        if not lottery:
            return LotteryEligibilityResponse(
                eligible=False, remaining_attempts=0, message="No active lottery campaign right now"
            )

        paid_orders = self.order_repo.count_user_completed_orders(db, user_id)
        used_spins = self.lottery_repo.count_user_entries(db, user_id, lottery.id)
        remaining = max(0, paid_orders - used_spins)

        return LotteryEligibilityResponse(
            eligible=remaining > 0,
            remaining_attempts=remaining,
            message=f"You have {remaining} spin attempt(s) remaining." if remaining > 0 else "Complete an order to earn lottery spin attempts!",
        )

    def spin_lottery(self, db: Session, user_id: int, lottery_id: int) -> LotterySpinResponse:
        lottery = self.lottery_repo.get_by_id(db, lottery_id)
        if not lottery or not lottery.is_active:
            raise NotFoundException("Lottery campaign not found or inactive")

        # Check eligibility: 1 paid order = 1 spin
        paid_orders = self.order_repo.count_user_completed_orders(db, user_id)
        used_spins = self.lottery_repo.count_user_entries(db, user_id, lottery.id)
        if paid_orders <= used_spins:
            raise ValidationException("You have no remaining lottery attempts. Complete an order to earn spins!")

        # Available prizes with stock
        available_prizes: List[LotteryPrize] = [p for p in lottery.prizes if p.quantity > 0 and p.probability > 0]

        selected_prize: Optional[LotteryPrize] = None
        if available_prizes:
            # Weighted random selection based on probability
            roll = random.random()  # 0.0 to 1.0
            cumulative = 0.0
            for prize in available_prizes:
                cumulative += prize.probability
                if roll <= cumulative:
                    # Attempt atomic inventory decrement
                    if self.lottery_repo.decrement_prize_quantity(db, prize.id):
                        selected_prize = prize
                    break

        # Record entry
        self.lottery_repo.create_entry(db, lottery.id, user_id, selected_prize.id if selected_prize else None)

        if selected_prize:
            prize_dto = LotteryPrizeResponse.model_validate(selected_prize)
            return LotterySpinResponse(
                success=True,
                won=True,
                message=f"Congratulations! You won {prize_dto.discount_value}% discount on selected reward!",
                prize=prize_dto,
            )
        else:
            return LotterySpinResponse(
                success=True,
                won=False,
                message="Better luck next time!",
                prize=None,
            )

    def get_user_entries(self, db: Session, user_id: int) -> List[LotteryEntry]:
        return self.lottery_repo.get_user_entries(db, user_id)

    def get_all_lotteries(self, db: Session) -> List[Lottery]:
        return self.lottery_repo.get_all(db)

    def create_lottery(self, db: Session, data: LotteryCreate) -> Lottery:
        return self.lottery_repo.create(db, data.model_dump())

    def add_prize_to_lottery(self, db: Session, lottery_id: int, data: LotteryPrizeCreate) -> LotteryPrize:
        lottery = self.lottery_repo.get_by_id(db, lottery_id)
        if not lottery:
            raise NotFoundException(f"Lottery with id {lottery_id} not found")

        prize_dict = data.model_dump()
        prize_dict["lottery_id"] = lottery_id
        return self.lottery_repo.add_prize(db, prize_dict)

    def get_all_entries(self, db: Session, lottery_id: int, pagination: PaginationParams):
        return self.lottery_repo.get_all_entries(db, lottery_id, pagination)
