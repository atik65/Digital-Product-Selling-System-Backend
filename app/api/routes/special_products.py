from typing import List, Optional, Union, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.response import StandardResponse
from app.schemas.special_product import SpecialCategoryResponse
from app.services.special_product_service import SpecialProductService

router = APIRouter(tags=["Special Products"])
service = SpecialProductService()


@router.get(
    "/special-products",
    response_model=Union[List[SpecialCategoryResponse], StandardResponse[List[SpecialCategoryResponse]]],
    status_code=status.HTTP_200_OK,
    summary="Landing Page: Get all categories with nested special products",
    description=(
        "Returns all categories grouped with their products for the landing page showcase. "
        "By default, returns the exact root JSON array matching the landing page frontend contract. "
        "Pass ?envelope=true if standard API envelope format is desired."
    ),
)
def get_special_products(
    active_only: bool = Query(
        True, description="Filter only active categories and products"
    ),
    category_id: Optional[int] = Query(
        None, description="Optional category ID to filter by"
    ),
    envelope: bool = Query(
        False,
        description="Set to true to wrap response in StandardResponse envelope",
    ),
    db: Session = Depends(get_db),
) -> Any:
    data = service.get_special_products_by_category(
        db, active_only=active_only, category_id=category_id
    )

    if envelope:
        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Special products retrieved successfully",
            "data": data,
        }

    return data


@router.get(
    "/products/special",
    response_model=Union[List[SpecialCategoryResponse], StandardResponse[List[SpecialCategoryResponse]]],
    status_code=status.HTTP_200_OK,
    summary="Landing Page: Get special products (alias route)",
    description="Alias route for /special-products",
)
def get_special_products_alias(
    active_only: bool = Query(True),
    category_id: Optional[int] = Query(None),
    envelope: bool = Query(False),
    db: Session = Depends(get_db),
) -> Any:
    return get_special_products(
        active_only=active_only,
        category_id=category_id,
        envelope=envelope,
        db=db,
    )
