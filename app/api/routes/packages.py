from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.package import (
    PackageResponse,
    PackageCreate,
    PackageUpdate,
    PackageStatusUpdate,
)
from app.services.package_service import PackageService

router = APIRouter(tags=["Packages"])
service = PackageService()


@router.get(
    "/products/{product_id}/packages",
    response_model=StandardResponse[List[PackageResponse]],
    status_code=status.HTTP_200_OK,
    summary="Get active packages for a product",
)
def get_packages_for_product(product_id: int, db: Session = Depends(get_db)):
    packages = service.get_packages_for_product(db, product_id, active_only=True)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Packages retrieved successfully",
        "data": packages,
    }


@router.post(
    "/admin/products/{product_id}/packages",
    response_model=StandardResponse[PackageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create package option for a product",
)
def create_package(
    product_id: int,
    body: PackageCreate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    package = service.create_package(db, product_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Package created successfully",
        "data": package,
    }


@router.put(
    "/admin/packages/{package_id}",
    response_model=StandardResponse[PackageResponse],
    status_code=status.HTTP_200_OK,
    summary="Update package details",
)
def update_package(
    package_id: int,
    body: PackageUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    package = service.update_package(db, package_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Package updated successfully",
        "data": package,
    }


@router.patch(
    "/admin/packages/{package_id}/status",
    response_model=StandardResponse[PackageResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle package active status",
)
def update_package_status(
    package_id: int,
    body: PackageStatusUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    package = service.update_status(db, package_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Package status updated successfully",
        "data": package,
    }


@router.delete(
    "/admin/packages/{package_id}",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Delete package",
)
def delete_package(
    package_id: int,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    service.delete_package(db, package_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Package deleted successfully",
        "data": {"id": package_id},
    }
