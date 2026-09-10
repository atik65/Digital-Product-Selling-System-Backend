from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.pagination import PaginationParams, PaginatedData
from app.schemas.order import (
    CheckoutPreviewRequest,
    CheckoutPreviewResponse,
    DirectOrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderNoteUpdate,
)
from app.services.order_service import OrderService

router = APIRouter(tags=["Orders & Checkout"])
order_service = OrderService()


# ==========================================
# 1. Customer Checkout & Orders
# ==========================================

@router.post(
    "/checkout/preview",
    response_model=StandardResponse[CheckoutPreviewResponse],
    status_code=status.HTTP_200_OK,
    summary="Preview direct checkout calculation and validation",
)
def preview_checkout(
    body: CheckoutPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preview = order_service.preview_checkout(db, body, user_id=current_user.id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Checkout preview calculated successfully",
        "data": preview,
    }


@router.post(
    "/orders",
    response_model=StandardResponse[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Place direct order with dynamic inputs and coupon",
)
def place_order(
    body: DirectOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = order_service.create_direct_order(db, current_user.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Order created successfully. Please complete payment.",
        "data": order,
    }


@router.get(
    "/orders/my-orders",
    response_model=StandardResponse[PaginatedData[OrderResponse]],
    status_code=status.HTTP_200_OK,
    summary="List customer's orders",
)
def get_my_orders(
    status_filter: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orders = order_service.get_user_orders(db, current_user.id, pagination, status=status_filter)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Orders retrieved successfully",
        "data": orders,
    }


@router.get(
    "/orders/{order_number}",
    response_model=StandardResponse[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get single order details by order number",
)
def get_order_by_number(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Admins can view any order; customers can only view their own
    user_id = None if current_user.role == "admin" else current_user.id
    order = order_service.get_order_by_number(db, order_number, user_id=user_id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Order retrieved successfully",
        "data": order,
    }


@router.post(
    "/orders/{order_number}/cancel",
    response_model=StandardResponse[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Cancel unpaid pending order",
)
def cancel_order(
    order_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = order_service.cancel_order(db, order_number, current_user.id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Order cancelled successfully",
        "data": order,
    }


# ==========================================
# 2. Admin Order Management
# ==========================================

@router.get(
    "/admin/orders",
    response_model=StandardResponse[PaginatedData[OrderResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all orders for admin",
)
def admin_list_orders(
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    orders = order_service.get_all_orders(db, pagination, status=status_filter, search=search)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Admin orders retrieved successfully",
        "data": orders,
    }


@router.patch(
    "/admin/orders/{order_id}/status",
    response_model=StandardResponse[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Update order processing status",
)
def admin_update_order_status(
    order_id: int,
    body: OrderStatusUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    order = order_service.update_order_status(db, order_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": f"Order status updated to '{body.status}'",
        "data": order,
    }


@router.patch(
    "/admin/orders/{order_id}/note",
    response_model=StandardResponse[OrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Update admin internal note or fulfillment details",
)
def admin_update_order_note(
    order_id: int,
    body: OrderNoteUpdate,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    order = order_service.update_admin_note(db, order_id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Order admin note updated successfully",
        "data": order,
    }
