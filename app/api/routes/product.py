from app.core.exceptions import NotFoundException
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session

from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    ProductFilters,
)
from app.schemas.pagination import PaginationParams, PaginatedData
from app.schemas.response import StandardResponse
from app.services.product_service import ProductService
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.enums.product import Specification

router = APIRouter(prefix="/products", tags=["Products"])
service = ProductService()


@router.post(
    "/",
    response_model=StandardResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    db_product = service.create_product(db, product)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Product created successfully",
        "data": db_product,
    }


# path parameters with enum
@router.get(
    "/spec/{spec}", response_model=StandardResponse[PaginatedData[ProductResponse]]
)
def get_product_by_specification(
    spec: Specification,
    response: Response,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
):
    products = service.get_products_by_spec(db, spec, pagination, response)

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Products retrieved successfully",
        "data": products,
    }


@router.get("/", response_model=StandardResponse[PaginatedData[ProductResponse]])
def get_products(
    response: Response,
    pagination: PaginationParams = Depends(),
    filters: ProductFilters = Depends(),
    db: Session = Depends(get_db),
):
    paginated_result = service.get_products(db, pagination, filters)

    # custom headers
    response.headers["X-Custom-header-by-Atik"] = "Hello from Atik"

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Products retrieved successfully",
        "data": paginated_result,
    }


@router.get("/{product_id}", response_model=StandardResponse[ProductResponse])
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = service.get_product(db, product_id)
    if not product:
        raise NotFoundException(f"Product with id {product_id} not found")
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Product retrieved successfully",
        "data": product,
    }


@router.put("/{product_id}", response_model=StandardResponse[ProductResponse])
def update_product(
    product_id: int, product: ProductUpdate, db: Session = Depends(get_db)
):

    updated_product = service.update_product(db, product_id, product)
    if not updated_product:
        raise NotFoundException(f"Product with id {product_id} not found")

    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Product updated successfully",
        "data": updated_product,
    }


@router.delete("/{product_id}", response_model=StandardResponse[ProductResponse])
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(["admin"])),
):
    deleted_product = service.delete_product(db, product_id)

    if not deleted_product:
        raise NotFoundException(f"Product with id {product_id} not found")
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Product deleted successfully",
        "data": deleted_product,
    }
