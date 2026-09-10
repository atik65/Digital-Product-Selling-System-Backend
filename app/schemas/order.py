from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    package_id: int
    product_name: str
    package_name: str
    unit_price: float
    quantity: int
    total_price: float
    input_values: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class CheckoutPreviewRequest(BaseModel):
    package_id: int
    quantity: int = 1
    coupon_code: Optional[str] = None
    input_values: Optional[Dict[str, Any]] = None


class CheckoutPreviewResponse(BaseModel):
    package_id: int
    package_name: str
    product_name: str
    unit_price: float
    quantity: int
    subtotal: float
    discount: float
    total: float
    coupon_applied: Optional[str] = None
    input_valid: bool = True
    validation_errors: Optional[List[str]] = None


class DirectOrderCreate(BaseModel):
    package_id: int
    quantity: int = 1
    coupon_code: Optional[str] = None
    input_values: Dict[str, Any]
    customer_note: Optional[str] = None
    payment_method_id: Optional[int] = None  # None if paying with wallet later


class OrderStatusUpdate(BaseModel):
    status: str  # PENDING, PAYMENT_PENDING, PAID, PROCESSING, COMPLETED, CANCELLED, FAILED, REFUNDED


class OrderNoteUpdate(BaseModel):
    admin_note: str


class OrderResponse(BaseModel):
    id: int
    user_id: int
    order_number: str
    subtotal: float
    discount: float
    total_amount: float
    coupon_id: Optional[int] = None
    status: str
    customer_note: Optional[str] = None
    admin_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
