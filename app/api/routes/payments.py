import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException, ValidationException
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.pagination import PaginationParams, PaginatedData
from app.schemas.payment import (
    PaymentResponse,
    PaymentSubmitRequest,
    PaymentVerifyRequest,
    PaymentRejectRequest,
)
from app.schemas.sms_webhook import (
    SmsWebhookPayload,
    SmsWebhookResponse,
    IncomingSmsResponse,
)
from app.services.payment_service import PaymentService
from app.services.sms_reconciliation_service import SmsReconciliationService
from app.repositories.incoming_sms_repository import IncomingSmsRepository

router = APIRouter(tags=["Payments"])
service = PaymentService()
sms_service = SmsReconciliationService()
sms_repo = IncomingSmsRepository()


@router.post(
    "/payments/submit",
    response_model=StandardResponse[PaymentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit manual payment transaction details",
)
def submit_payment(
    body: PaymentSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = service.submit_payment(db, current_user.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "Payment submitted successfully. Awaiting admin verification.",
        "data": payment,
    }


@router.get(
    "/payments/order/{order_id}",
    response_model=StandardResponse[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get payment details for an order",
)
def get_order_payment(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = service.get_order_payment(db, order_id, current_user.id)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment details retrieved successfully",
        "data": payment,
    }


@router.get(
    "/admin/payments",
    response_model=StandardResponse[PaginatedData[PaymentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List payments for verification",
)
def admin_list_payments(
    status_filter: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    payments = service.get_all_payments(db, pagination, status=status_filter)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payments retrieved successfully",
        "data": payments,
    }


@router.post(
    "/admin/payments/{payment_id}/verify",
    response_model=StandardResponse[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve payment (marks Payment VERIFIED & Order PAID)",
)
def admin_verify_payment(
    payment_id: int,
    body: PaymentVerifyRequest,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    payment = service.verify_payment(db, payment_id, current_admin.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment verified successfully. Order marked as PAID.",
        "data": payment,
    }


@router.post(
    "/admin/payments/{payment_id}/reject",
    response_model=StandardResponse[PaymentResponse],
    status_code=status.HTTP_200_OK,
    summary="Reject payment (reverts Order to PAYMENT_PENDING)",
)
def admin_reject_payment(
    payment_id: int,
    body: PaymentRejectRequest,
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    payment = service.reject_payment(db, payment_id, current_admin.id, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Payment rejected.",
        "data": payment,
    }


@router.post(
    "/payments/webhook/sms",
    response_model=StandardResponse[SmsWebhookResponse],
    status_code=status.HTTP_200_OK,
    summary="Receive incoming SMS from Android listener for automatic payment verification",
)
async def receive_sms_webhook(
    request: Request,
    x_device_secret: Optional[str] = Header(None, alias="X-Device-Secret"),
    secret: Optional[str] = Query(
        None,
        description="Optional secret via query param (e.g. ?secret=...) for apps like SmsForwarder",
    ),
    db: Session = Depends(get_db),
):
    auth_secret = x_device_secret or secret
    if not auth_secret or auth_secret != settings.SMS_WEBHOOK_SECRET:
        raise UnauthorizedException(
            "Invalid or missing secret (pass 'X-Device-Secret' header or '?secret=...' query parameter)"
        )

    # Resolve payload flexibly across JSON, Form-data, and raw text
    content_type = request.headers.get("content-type", "").lower()
    raw_data = None

    if "application/json" in content_type:
        try:
            raw_data = await request.json()
        except Exception:
            pass

    if raw_data is None and ("form" in content_type or "urlencoded" in content_type):
        try:
            form_data = await request.form()
            if form_data:
                raw_data = dict(form_data)
        except Exception:
            pass

    if raw_data is None:
        try:
            body_bytes = await request.body()
            if body_bytes:
                text = body_bytes.decode("utf-8", errors="ignore").strip()
                if text.startswith("{") and text.endswith("}"):
                    raw_data = json.loads(text)
                elif "=" in text:
                    from urllib.parse import parse_qs

                    parsed = parse_qs(text)
                    if parsed:
                        raw_data = {
                            k: v[0] if len(v) == 1 else v for k, v in parsed.items()
                        }
        except Exception:
            pass

    if raw_data is None and (
        request.query_params.get("from") or request.query_params.get("sender")
    ):
        raw_data = dict(request.query_params)

    if not raw_data:
        raise ValidationException(
            "Missing SMS payload. Please send valid JSON or Form-data with sender and message."
        )

    try:
        payload = SmsWebhookPayload.model_validate(raw_data)
    except Exception as e:
        raise ValidationException(f"Invalid SMS payload: {str(e)}")

    result = sms_service.process_incoming_sms(db, payload)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": result.message,
        "data": result,
    }


@router.get(
    "/admin/payments/sms-logs",
    response_model=StandardResponse[PaginatedData[IncomingSmsResponse]],
    status_code=status.HTTP_200_OK,
    summary="List all received SMS logs from forwarding devices",
)
def admin_list_sms_logs(
    is_matched: Optional[bool] = None,
    provider: Optional[str] = None,
    search: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    current_admin: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    logs = sms_repo.get_all(
        db,
        pagination,
        is_matched=is_matched,
        provider=provider,
        search=search,
    )
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "SMS logs retrieved successfully",
        "data": logs,
    }
