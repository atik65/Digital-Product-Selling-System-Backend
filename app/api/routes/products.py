from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.pagination import PaginationParams, PaginatedData
from app.schemas.product import (
    ProductCardResponse,
    ProductDetailResponse,
    ProductCreate,
    ProductUpdate,
    ProductStatusUpdate,
    ProductFilters,
)
from app.schemas.product_input_field import (
    InputFieldResponse,
    InputFieldCreate,
    InputFieldUpdate,
)
from app.services.product_service import ProductService
from app.services.product_input_field_service import ProductInputFieldService

router = APIRouter(tags=["Products"])
product_service = ProductService()
field_service = ProductInputFieldService()


# ==========================================
# 1. Public Product Catalog
# ==========================================


@router.get(
    "/products",
    response_model=StandardResponse[PaginatedData[ProductCardResponse]],
    status_code=status.HTTP_200_OK,
    summary="Browse active products catalog",
)
def list_products(
    filters: ProductFilters = Depends(),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
):
    if filters.is_active is None:
        filters.is_active = True
    products = product_service.get_products(db, pagination, filters)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Products retrieved successfully",
        "data": products,
    }


@router.get(
    "/products/{slug}",
    response_model=StandardResponse[ProductDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get product details with packages and required input fields",
)
def get_product_details(slug: str, db: Session = Depends(get_db)):
    product = product_service.get_product_by_slug(db, slug)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Product details retrieved successfully",
        "data": product,
    }


# ==========================================
# 2. Dynamic Input Fields
# ==========================================


@router.get(
    "/products/{product_id}/fields",
    response_model=StandardResponse[List[InputFieldResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get required customer input fields for a product",
)
def get_product_input_fields(product_id: int, db: Session = Depends(get_db)):
    fields = field_service.get_fields(db, product_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Product input fields retrieved successfully",
        "data": fields,
    }


@router.post(
    "/admin/products/{product_id}/fields",
    response_model=StandardResponse[InputFieldResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add dynamic input field to product",
)
def create_product_input_field(
    product_id: int,
    body: InputFieldCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    field = field_service.create_field(db, product_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Input field added successfully",
        "data": field,
    }


@router.put(
    "/admin/fields/{field_id}",
    response_model=StandardResponse[InputFieldResponse],
    status_code=status.HTTP_200_OK,
    summary="Update input field configuration",
)
def update_product_input_field(
    field_id: int,
    body: InputFieldUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    field = field_service.update_field(db, field_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Input field updated successfully",
        "data": field,
    }


@router.delete(
    "/admin/fields/{field_id}",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete input field configuration",
)
def delete_product_input_field(
    field_id: int,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    field_service.delete_field(db, field_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Input field deleted successfully",
        "data": {"id": field_id},
    }


# ==========================================
# 3. Admin Product Management
# ==========================================


@router.get(
    "/admin/products",
    response_model=StandardResponse[PaginatedData[ProductCardResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all products for admin",
)
def admin_list_products(
    filters: ProductFilters = Depends(),
    pagination: PaginationParams = Depends(),
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    products = product_service.get_products(db, pagination, filters)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Admin products retrieved successfully",
        "data": products,
    }


@router.post(
    "/admin/products",
    response_model=StandardResponse[ProductDetailResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new digital product",
)
def create_product(
    body: ProductCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    product = product_service.create_product(db, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Product created successfully",
        "data": product,
    }


@router.put(
    "/admin/products/{product_id}",
    response_model=StandardResponse[ProductDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Update product details",
)
def update_product(
    product_id: int,
    body: ProductUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    product = product_service.update_product(db, product_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Product updated successfully",
        "data": product,
    }


@router.patch(
    "/admin/products/{product_id}/status",
    response_model=StandardResponse[ProductDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle product active status",
)
def update_product_status(
    product_id: int,
    body: ProductStatusUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    product = product_service.update_status(db, product_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Product status updated successfully",
        "data": product,
    }


@router.delete(
    "/admin/products/{product_id}",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete product",
)
def delete_product(
    product_id: int,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    product_service.delete_product(db, product_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Product deleted successfully",
        "data": {"id": product_id},
    }
