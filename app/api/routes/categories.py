from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.category import (
    CategoryResponse,
    CategoryCreate,
    CategoryUpdate,
    CategoryReorder,
)
from app.services.category_service import CategoryService

router = APIRouter(tags=["Categories"])
service = CategoryService()


# Public Routes
@router.get(
    "/categories",
    response_model=StandardResponse[List[CategoryResponse]],
    status_code=status.HTTP_200_OK,
    summary="List active categories",
)
def list_categories(db: Session = Depends(get_db)):
    categories = service.get_categories(db, active_only=True)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Categories retrieved successfully",
        "data": categories,
    }


@router.get(
    "/categories/{slug}",
    response_model=StandardResponse[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Get single category by slug",
)
def get_category_by_slug(slug: str, db: Session = Depends(get_db)):
    category = service.get_by_slug(db, slug)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Category retrieved successfully",
        "data": category,
    }


# Admin Routes
@router.get(
    "/admin/categories",
    response_model=StandardResponse[List[CategoryResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all categories for admin",
)
def admin_list_categories(
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    categories = service.get_categories(db, active_only=False)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "All categories retrieved successfully",
        "data": categories,
    }


@router.post(
    "/admin/categories",
    response_model=StandardResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
)
def create_category(
    body: CategoryCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    category = service.create_category(db, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Category created successfully",
        "data": category,
    }


@router.put(
    "/admin/categories/{category_id}",
    response_model=StandardResponse[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Update category",
)
def update_category(
    category_id: int,
    body: CategoryUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    category = service.update_category(db, category_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Category updated successfully",
        "data": category,
    }


@router.patch(
    "/admin/categories/{category_id}/reorder",
    response_model=StandardResponse[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="Reorder category display index",
)
def reorder_category(
    category_id: int,
    body: CategoryReorder,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    category = service.reorder_category(db, category_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Category order updated successfully",
        "data": category,
    }


@router.delete(
    "/admin/categories/{category_id}",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete category",
)
def delete_category(
    category_id: int,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    service.delete_category(db, category_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Category deleted successfully",
        "data": {"id": category_id},
    }
