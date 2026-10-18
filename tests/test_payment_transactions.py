from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.models.payment_transaction import PaymentTransaction
from app.utils.period import day_range_utc, month_range_utc


def _create_method(client, admin_headers, name="bKash Personal", **extra):
    res = client.post(
        "/api/v1/admin/payment-methods",
        json={"name": name, "account_number": "01700000000", **extra},
        headers=admin_headers,
    )
    assert res.status_code == 201
    return res.json()["data"]


def _get_method(client, admin_headers, method_id):
    res = client.get("/api/v1/admin/payment-methods", headers=admin_headers)
    return next(m for m in res.json()["data"] if m["id"] == method_id)


def _create_order(client, admin_headers, user_headers, method_id, slug="netflix"):
    product_id = client.post(
        "/api/v1/admin/products",
        json={"name": slug.title(), "slug": slug},
        headers=admin_headers,
    ).json()["data"]["id"]
    package_id = client.post(
        f"/api/v1/admin/products/{product_id}/packages",
        json={"name": "1 Month", "price": 400.0, "is_active": True},
        headers=admin_headers,
    ).json()["data"]["id"]
    order = client.post(
        "/api/v1/orders",
        json={
            "package_id": package_id,
            "quantity": 1,
            "input_values": {"mobile": "01799999999"},
            "payment_method_id": method_id,
        },
        headers=user_headers,
    )
    assert order.status_code == 201
    return order.json()["data"]["id"]


def _submit_payment(
    client, user_headers, order_id, method_id, trx, sender="01711223344"
):
    res = client.post(
        "/api/v1/payments/submit",
        json={
            "order_id": order_id,
            "payment_method_id": method_id,
            "amount": 400.0,
            "transaction_id": trx,
            "sender_number": sender,
        },
        headers=user_headers,
    )
    assert res.status_code == 201
    return res.json()["data"]["id"]


def _history(client, admin_headers, **params):
    res = client.get(
        "/api/v1/admin/payment-transactions", params=params, headers=admin_headers
    )
    assert res.status_code == 200
    return res.json()["data"]["items"]


# ---------------------------------------------------------------- limits


def test_set_update_and_clear_transaction_limits(client, admin_auth_headers):
    method = _create_method(
        client,
        admin_auth_headers,
        daily_transaction_limit=20,
        monthly_transaction_limit=300,
    )
    assert method["daily_transaction_limit"] == 20
    assert method["monthly_transaction_limit"] == 300
    assert method["daily_transaction_count"] == 0
    assert method["monthly_transaction_count"] == 0
    assert method["monthly_remaining"] == 300

    # Partial update keeps the other limit untouched
    res = client.put(
        f"/api/v1/admin/payment-methods/{method['id']}",
        json={"monthly_transaction_limit": 500},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["monthly_transaction_limit"] == 500
    assert res.json()["data"]["daily_transaction_limit"] == 20

    # Explicit null removes a limit
    res = client.put(
        f"/api/v1/admin/payment-methods/{method['id']}",
        json={"daily_transaction_limit": None},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["daily_transaction_limit"] is None
    assert res.json()["data"]["daily_remaining"] is None
    assert res.json()["data"]["monthly_transaction_limit"] == 500

    # Unrelated update does not wipe the limits
    res = client.put(
        f"/api/v1/admin/payment-methods/{method['id']}",
        json={"account_number": "01811111111"},
        headers=admin_auth_headers,
    )
    assert res.json()["data"]["monthly_transaction_limit"] == 500


def test_limits_must_be_positive(client, admin_auth_headers):
    res = client.post(
        "/api/v1/admin/payment-methods",
        json={
            "name": "Bad",
            "account_number": "0170",
            "monthly_transaction_limit": 0,
        },
        headers=admin_auth_headers,
    )
    assert res.status_code == 422


def test_public_payment_methods_do_not_expose_limits(client, admin_auth_headers):
    _create_method(client, admin_auth_headers, monthly_transaction_limit=300)
    res = client.get("/api/v1/payment-methods")
    assert res.status_code == 200
    method = res.json()["data"][0]
    assert "monthly_transaction_limit" not in method
    assert "monthly_transaction_count" not in method


# --------------------------------------------------------- counting flow


def test_verified_payment_is_counted_and_listed(
    client, admin_auth_headers, auth_headers
):
    method = _create_method(
        client,
        admin_auth_headers,
        monthly_transaction_limit=300,
        daily_transaction_limit=10,
    )
    order_id = _create_order(client, admin_auth_headers, auth_headers, method["id"])
    payment_id = _submit_payment(
        client, auth_headers, order_id, method["id"], "TRX-COUNT-1"
    )

    # Submitted but not yet verified -> not a successful transaction
    assert (
        _get_method(client, admin_auth_headers, method["id"])[
            "monthly_transaction_count"
        ]
        == 0
    )
    assert _history(client, admin_auth_headers) == []

    res = client.post(
        f"/api/v1/admin/payments/{payment_id}/verify",
        json={"admin_note": "ok"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200

    stats = _get_method(client, admin_auth_headers, method["id"])
    assert stats["daily_transaction_count"] == 1
    assert stats["monthly_transaction_count"] == 1
    assert stats["daily_remaining"] == 9
    assert stats["monthly_remaining"] == 299

    items = _history(client, admin_auth_headers)
    assert len(items) == 1
    tx = items[0]
    assert tx["transaction_id"] == "TRX-COUNT-1"
    assert tx["sender_number"] == "01711223344"
    assert tx["amount"] == 400.0
    assert tx["source_type"] == "ORDER_PAYMENT"
    assert tx["source_id"] == payment_id
    assert tx["payment_method"]["name"] == "bKash Personal"
    assert tx["user"]["email"] == "testuser@example.com"
    assert tx["transaction_at"]

    # Verifying again must not double count
    client.post(
        f"/api/v1/admin/payments/{payment_id}/verify",
        json={"admin_note": "again"},
        headers=admin_auth_headers,
    )
    assert (
        _get_method(client, admin_auth_headers, method["id"])[
            "monthly_transaction_count"
        ]
        == 1
    )


def test_rejecting_verified_payment_revokes_the_count(
    client, admin_auth_headers, auth_headers
):
    method = _create_method(client, admin_auth_headers)
    order_id = _create_order(client, admin_auth_headers, auth_headers, method["id"])
    payment_id = _submit_payment(
        client, auth_headers, order_id, method["id"], "TRX-REVOKE-1"
    )
    client.post(
        f"/api/v1/admin/payments/{payment_id}/verify",
        json={},
        headers=admin_auth_headers,
    )
    assert (
        _get_method(client, admin_auth_headers, method["id"])[
            "monthly_transaction_count"
        ]
        == 1
    )

    client.post(
        f"/api/v1/admin/payments/{payment_id}/reject",
        json={"admin_note": "Mistake"},
        headers=admin_auth_headers,
    )
    assert (
        _get_method(client, admin_auth_headers, method["id"])[
            "monthly_transaction_count"
        ]
        == 0
    )
    assert _history(client, admin_auth_headers) == []

    # Re-verifying brings it back exactly once
    client.post(
        f"/api/v1/admin/payments/{payment_id}/verify",
        json={},
        headers=admin_auth_headers,
    )
    assert (
        _get_method(client, admin_auth_headers, method["id"])[
            "monthly_transaction_count"
        ]
        == 1
    )
    assert len(_history(client, admin_auth_headers)) == 1


def test_rejected_payment_is_never_counted(client, admin_auth_headers, auth_headers):
    method = _create_method(client, admin_auth_headers)
    order_id = _create_order(client, admin_auth_headers, auth_headers, method["id"])
    payment_id = _submit_payment(
        client, auth_headers, order_id, method["id"], "TRX-REJ-1"
    )
    client.post(
        f"/api/v1/admin/payments/{payment_id}/reject",
        json={"admin_note": "fake"},
        headers=admin_auth_headers,
    )
    assert (
        _get_method(client, admin_auth_headers, method["id"])[
            "monthly_transaction_count"
        ]
        == 0
    )
    assert _history(client, admin_auth_headers) == []


def test_approved_topup_is_counted_and_pending_is_not(
    client, admin_auth_headers, auth_headers
):
    method = _create_method(client, admin_auth_headers, name="Nagad")
    topup_id = client.post(
        "/api/v1/wallet/topup",
        json={
            "payment_method_id": method["id"],
            "amount": 250.0,
            "transaction_id": "TOPUP-LEDGER-1",
        },
        headers=auth_headers,
    ).json()["data"]["id"]
    assert _history(client, admin_auth_headers) == []

    res = client.post(
        f"/api/v1/admin/topups/{topup_id}/approve",
        json={"admin_note": "ok"},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200

    stats = _get_method(client, admin_auth_headers, method["id"])
    assert stats["monthly_transaction_count"] == 1
    tx = _history(client, admin_auth_headers)[0]
    assert tx["source_type"] == "WALLET_TOPUP"
    assert tx["amount"] == 250.0
    assert tx["sender_number"] is None  # optional and not provided


def test_rejected_topup_is_not_counted(client, admin_auth_headers, auth_headers):
    method = _create_method(client, admin_auth_headers)
    topup_id = client.post(
        "/api/v1/wallet/topup",
        json={
            "payment_method_id": method["id"],
            "amount": 100.0,
            "transaction_id": "TOPUP-REJ-1",
        },
        headers=auth_headers,
    ).json()["data"]["id"]
    client.post(
        f"/api/v1/admin/topups/{topup_id}/reject",
        json={"admin_note": "no"},
        headers=admin_auth_headers,
    )
    assert (
        _get_method(client, admin_auth_headers, method["id"])[
            "monthly_transaction_count"
        ]
        == 0
    )


def test_sms_auto_verification_records_transaction_with_sender_from_sms(
    client, admin_auth_headers, auth_headers
):
    method = _create_method(client, admin_auth_headers)
    order_id = _create_order(client, admin_auth_headers, auth_headers, method["id"])
    # Customer leaves the sender number out
    payment_res = client.post(
        "/api/v1/payments/submit",
        json={
            "order_id": order_id,
            "payment_method_id": method["id"],
            "amount": 400.0,
            "transaction_id": "9K48X78L9",
        },
        headers=auth_headers,
    )
    assert payment_res.status_code == 201

    sms = client.post(
        "/api/v1/payments/webhook/sms",
        json={
            "sender": "bKash",
            "message": (
                "You have received Tk 400.00 from 01655443322. "
                "Fee Tk 0.00. Balance Tk 1,234.50. TrxID 9K48X78L9 at 11/09/2026 02:05"
            ),
        },
        headers={"X-Device-Secret": settings.SMS_WEBHOOK_SECRET},
    )
    assert sms.status_code == 200
    assert sms.json()["data"]["matched"] is True

    assert (
        _get_method(client, admin_auth_headers, method["id"])[
            "monthly_transaction_count"
        ]
        == 1
    )
    tx = _history(client, admin_auth_headers)[0]
    assert tx["transaction_id"] == "9K48X78L9"
    assert tx["sender_number"] == "01655443322"
    assert tx["amount"] == 400.0


def test_sms_arriving_before_submission_records_transaction(
    client, admin_auth_headers, auth_headers
):
    method = _create_method(client, admin_auth_headers)
    client.post(
        "/api/v1/payments/webhook/sms",
        json={
            "sender": "bKash",
            "message": (
                "You have received Tk 300.00 from 01655443322. "
                "Fee Tk 0.00. Balance Tk 1,234.50. TrxID 7Z11Q22W3 at 11/09/2026 02:05"
            ),
        },
        headers={"X-Device-Secret": settings.SMS_WEBHOOK_SECRET},
    )
    topup = client.post(
        "/api/v1/wallet/topup",
        json={
            "payment_method_id": method["id"],
            "amount": 300.0,
            "transaction_id": "7Z11Q22W3",
        },
        headers=auth_headers,
    )
    assert topup.status_code == 201
    assert topup.json()["data"]["status"] == "APPROVED"

    assert (
        _get_method(client, admin_auth_headers, method["id"])[
            "monthly_transaction_count"
        ]
        == 1
    )
    tx = _history(client, admin_auth_headers)[0]
    assert tx["source_type"] == "WALLET_TOPUP"
    assert tx["sender_number"] == "01655443322"


# --------------------------------------------------------- period logic


def test_counts_cover_only_current_day_and_month(client, admin_auth_headers, db):
    method = _create_method(client, admin_auth_headers)
    day_start, _ = day_range_utc()
    month_start, month_end = month_range_utc()

    def add(source_id, at):
        db.add(
            PaymentTransaction(
                payment_method_id=method["id"],
                source_type="ORDER_PAYMENT",
                source_id=source_id,
                transaction_id=f"T{source_id}",
                amount=10.0,
                transaction_at=at,
            )
        )

    add(1, datetime.now(timezone.utc))  # now: in both windows
    add(2, month_start)  # first instant of the month: in the month window
    add(3, month_start - timedelta(seconds=1))  # last second of previous month
    add(4, month_end)  # first instant of next month
    db.commit()

    stats = _get_method(client, admin_auth_headers, method["id"])
    assert stats["monthly_transaction_count"] == 2
    # Row 2 is also "today" only when today is the 1st
    assert stats["daily_transaction_count"] == (2 if day_start == month_start else 1)


def test_month_starts_on_the_first_in_bangladesh_time():
    # 2026-09-30 18:30 UTC is already 1 Oct 00:30 in Dhaka (UTC+6)
    start, end = month_range_utc(datetime(2026, 9, 30, 18, 30, tzinfo=timezone.utc))
    assert start == datetime(2026, 9, 30, 18, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 10, 31, 18, 0, tzinfo=timezone.utc)

    # 2026-09-30 17:30 UTC is still 30 Sep 23:30 in Dhaka
    start, end = month_range_utc(datetime(2026, 9, 30, 17, 30, tzinfo=timezone.utc))
    assert start == datetime(2026, 8, 31, 18, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 9, 30, 18, 0, tzinfo=timezone.utc)

    # December rolls into January
    start, end = month_range_utc(datetime(2026, 12, 15, 6, 0, tzinfo=timezone.utc))
    assert end == datetime(2026, 12, 31, 18, 0, tzinfo=timezone.utc)

    day_start, day_end = day_range_utc(
        datetime(2026, 10, 18, 20, 0, tzinfo=timezone.utc)
    )
    assert day_start == datetime(2026, 10, 18, 18, 0, tzinfo=timezone.utc)
    assert day_end == datetime(2026, 10, 19, 18, 0, tzinfo=timezone.utc)


# ------------------------------------------------------------- history


def test_history_filters(client, admin_auth_headers, db):
    bkash = _create_method(client, admin_auth_headers, name="bKash")
    nagad = _create_method(client, admin_auth_headers, name="Nagad")

    rows = [
        (
            1,
            bkash["id"],
            "ORDER_PAYMENT",
            "BK1",
            "01711111111",
            datetime(2026, 10, 2, 5, 0, tzinfo=timezone.utc),
        ),
        (
            2,
            bkash["id"],
            "WALLET_TOPUP",
            "BK2",
            "01722222222",
            datetime(2026, 10, 10, 5, 0, tzinfo=timezone.utc),
        ),
        (
            3,
            nagad["id"],
            "ORDER_PAYMENT",
            "NG1",
            "01833333333",
            datetime(2026, 10, 12, 5, 0, tzinfo=timezone.utc),
        ),
    ]
    for source_id, method_id, source_type, trx, sender, at in rows:
        db.add(
            PaymentTransaction(
                payment_method_id=method_id,
                source_type=source_type,
                source_id=source_id,
                transaction_id=trx,
                sender_number=sender,
                amount=100.0 * source_id,
                transaction_at=at,
            )
        )
    db.commit()

    # Newest first
    assert [t["transaction_id"] for t in _history(client, admin_auth_headers)] == [
        "NG1",
        "BK2",
        "BK1",
    ]
    assert {
        t["transaction_id"]
        for t in _history(client, admin_auth_headers, payment_method_id=bkash["id"])
    } == {"BK1", "BK2"}
    assert [
        t["transaction_id"]
        for t in _history(client, admin_auth_headers, source_type="WALLET_TOPUP")
    ] == ["BK2"]
    assert [
        t["transaction_id"] for t in _history(client, admin_auth_headers, search="0183")
    ] == ["NG1"]
    assert [
        t["transaction_id"] for t in _history(client, admin_auth_headers, search="bk1")
    ] == ["BK1"]
    # Inclusive date range
    assert {
        t["transaction_id"]
        for t in _history(
            client, admin_auth_headers, date_from="2026-10-10", date_to="2026-10-12"
        )
    } == {"BK2", "NG1"}
    assert [
        t["transaction_id"]
        for t in _history(client, admin_auth_headers, date_to="2026-10-02")
    ] == ["BK1"]

    res = client.get(
        "/api/v1/admin/payment-transactions",
        params={"size": 2, "page": 2},
        headers=admin_auth_headers,
    )
    body = res.json()["data"]
    assert body["pagination"]["total"] == 3
    assert len(body["items"]) == 1

    bad = client.get(
        "/api/v1/admin/payment-transactions",
        params={"source_type": "NOPE"},
        headers=admin_auth_headers,
    )
    assert bad.status_code == 422


def test_history_requires_admin(client, auth_headers):
    assert client.get("/api/v1/admin/payment-transactions").status_code == 401
    res = client.get("/api/v1/admin/payment-transactions", headers=auth_headers)
    assert res.status_code == 403
