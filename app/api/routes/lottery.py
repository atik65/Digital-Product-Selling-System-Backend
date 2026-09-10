from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.pagination import PaginationParams, PaginatedData
from app.schemas.lottery import (
    LotteryResponse,
    LotteryCreate,
    LotteryPrizeCreate,
    LotteryPrizeResponse,
    LotteryEligibilityResponse,
    LotterySpinResponse,
    LotteryEntryResponse,
)
from app.services.lottery_service import LotteryService

router = APIRouter(tags=["Lottery & Lucky Spin"])
service = LotteryService()


@router.get(
    "/lottery/active",
    response_model=StandardResponse[Optional[LotteryResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get active lottery campaign and prize pool",
)
def get_active_lottery(db: Session = Depends(get_db)):
    lottery = service.get_active_lottery(db)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Active lottery retrieved successfully",
        "data": lottery,
    }


@router.get(
    "/lottery/my-eligibility",
    response_model=StandardResponse[LotteryEligibilityResponse],
    status_code=status.HTTP_200_OK,
    summary="Check remaining lottery spin attempts for customer",
)
def check_eligibility(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    eligibility = service.check_user_eligibility(db, current_user.id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Eligibility checked",
        "data": eligibility,
    }


@router.post(
    "/lottery/{lottery_id}/spin",
    response_model=StandardResponse[LotterySpinResponse],
    status_code=status.HTTP_200_OK,
    summary="Spin lottery wheel to win rewards",
)
def spin_lottery(
    lottery_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = service.spin_lottery(db, current_user.id, lottery_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": result.message,
        "data": result,
    }


@router.get(
    "/lottery/my-history",
    response_model=StandardResponse[List[LotteryEntryResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get customer's past spin attempts and won prizes",
)
def get_my_lottery_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = service.get_user_entries(db, current_user.id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "History retrieved successfully",
        "data": entries,
    }


# Admin Routes
@router.get(
    "/admin/lotteries",
    response_model=StandardResponse[List[LotteryResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all lottery campaigns for admin",
)
def admin_list_lotteries(
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    lotteries = service.get_all_lotteries(db)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Lotteries retrieved successfully",
        "data": lotteries,
    }


@router.post(
    "/admin/lotteries",
    response_model=StandardResponse[LotteryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create lottery campaign",
)
def admin_create_lottery(
    body: LotteryCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    lottery = service.create_lottery(db, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Lottery campaign created successfully",
        "data": lottery,
    }


@router.post(
    "/admin/lotteries/{lottery_id}/prizes",
    response_model=StandardResponse[LotteryPrizeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add prize to lottery campaign",
)
def admin_add_prize(
    lottery_id: int,
    body: LotteryPrizeCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    prize = service.add_prize_to_lottery(db, lottery_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Prize added to lottery successfully",
        "data": prize,
    }


@router.get(
    "/admin/lotteries/{lottery_id}/entries",
    response_model=StandardResponse[PaginatedData[LotteryEntryResponse]],
    status_code=status.HTTP_200_OK,
    summary="View customer entry audit logs for a lottery campaign",
)
def admin_get_lottery_entries(
    lottery_id: int,
    pagination: PaginationParams = Depends(),
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    entries = service.get_all_entries(db, lottery_id, pagination)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Entries retrieved successfully",
        "data": entries,
    }
