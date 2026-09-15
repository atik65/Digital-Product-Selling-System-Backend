from app.services.sms_parser_service import SmsParserService
from app.core.config import settings


def test_sms_parser_bkash():
    msg = (
        "You have received Tk 500.00 from 01711223344. "
        "Fee Tk 0.00. Balance Tk 1,234.50. TrxID 9K48X78L9 at 11/09/2026 02:05"
    )
    parsed = SmsParserService.parse("bKash", msg)
    assert parsed.provider == "BKASH"
    assert parsed.transaction_id == "9K48X78L9"
    assert parsed.amount == 500.0
    assert parsed.sender_phone == "01711223344"
    assert parsed.balance == 1234.50
    assert parsed.is_received_money is True


def test_sms_parser_nagad():
    msg = (
        "Customer: 01822334455\n"
        "Amount: Tk 1,250.00\n"
        "TxnID: 71KJ892K\n"
        "Balance: Tk 3,500.00\n"
        "Time: 11/09/2026 02:10"
    )
    parsed = SmsParserService.parse("Nagad", msg)
    assert parsed.provider == "NAGAD"
    assert parsed.transaction_id == "71KJ892K"
    assert parsed.amount == 1250.0
    assert parsed.sender_phone == "01822334455"
    assert parsed.balance == 3500.0
    assert parsed.is_received_money is True


def test_sms_parser_rocket():
    msg = "Received Tk 300.00 from 01933445566, TxnId: 88776655, Comm: 0.00, Balance: Tk 800.00"
    parsed = SmsParserService.parse("16216", msg)
    assert parsed.provider == "ROCKET"
    assert parsed.transaction_id == "88776655"
    assert parsed.amount == 300.0
    assert parsed.sender_phone == "01933445566"
    assert parsed.is_received_money is True


def test_webhook_device_secret_auth(client):
    # Missing header -> 401
    res = client.post(
        "/api/v1/payments/webhook/sms",
        json={"sender": "bKash", "message": "hello"},
    )
    assert res.status_code == 401

    # Wrong header -> 401
    res = client.post(
        "/api/v1/payments/webhook/sms",
        json={"sender": "bKash", "message": "hello"},
        headers={"X-Device-Secret": "invalid-secret"},
    )
    assert res.status_code == 401


def test_scenario_a_payment_first_sms_second(client, admin_auth_headers, auth_headers):
    """Customer submits order payment first, SMS arrives second -> Auto-verifies to PAID."""
    # 1. Setup Product, Package, Payment Method
    prod = client.post(
        "/api/v1/admin/products",
        json={"name": "Steam Wallet 500", "slug": "steam-wallet-500"},
        headers=admin_auth_headers,
    ).json()["data"]
    pkg = client.post(
        f"/api/v1/admin/products/{prod['id']}/packages",
        json={"name": "500 BDT Code", "price": 500.0, "is_active": True},
        headers=admin_auth_headers,
    ).json()["data"]
    method = client.post(
        "/api/v1/admin/payment-methods",
        json={
            "name": "bKash Auto",
            "type": "MANUAL",
            "account_number": "01711000000",
            "is_active": True,
        },
        headers=admin_auth_headers,
    ).json()["data"]

    # 2. Customer checks out via /orders
    order_res = client.post(
        "/api/v1/orders",
        json={"package_id": pkg["id"], "quantity": 1, "input_values": {}},
        headers=auth_headers,
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["data"]["id"]
    order_number = order_res.json()["data"]["order_number"]

    # 3. Customer submits manual payment details (status: VERIFYING)
    trx = "BKASH_TRX_SCENARIO_A"
    pay_res = client.post(
        "/api/v1/payments/submit",
        json={
            "order_id": order_id,
            "payment_method_id": method["id"],
            "amount": 500.0,
            "transaction_id": trx,
            "sender_number": "01711223344",
        },
        headers=auth_headers,
    )
    assert pay_res.status_code == 201
    assert pay_res.json()["data"]["status"] == "VERIFYING"

    # Verify order is PAYMENT_PENDING / PENDING
    order_check = client.get(f"/api/v1/orders/{order_number}", headers=auth_headers)
    assert order_check.json()["data"]["status"] in [
        "PENDING",
        "PAYMENT_PENDING",
    ]

    # 4. Device sends SMS Webhook
    sms_msg = (
        f"You have received Tk 500.00 from 01711223344. "
        f"Fee Tk 0.00. Balance Tk 2,500.00. TrxID {trx} at 11/09/2026 02:20"
    )
    webhook_res = client.post(
        "/api/v1/payments/webhook/sms",
        json={"sender": "bKash", "message": sms_msg},
        headers={"X-Device-Secret": settings.SMS_WEBHOOK_SECRET},
    )
    assert webhook_res.status_code == 200
    w_data = webhook_res.json()["data"]
    assert w_data["matched"] is True
    assert w_data["matched_entity_type"] == "ORDER_PAYMENT"

    # 5. Order is now auto-verified to PAID!
    order_after = client.get(f"/api/v1/orders/{order_number}", headers=auth_headers)
    assert order_after.json()["data"]["status"] == "PAID"


def test_scenario_b_sms_first_payment_second(client, admin_auth_headers, auth_headers):
    """SMS arrives on phone first, Customer submits payment second -> Instantly verified to PAID."""
    # 1. Setup Product, Package, Payment Method
    prod = client.post(
        "/api/v1/admin/products",
        json={"name": "Netflix Pass", "slug": "netflix-pass-b"},
        headers=admin_auth_headers,
    ).json()["data"]
    pkg = client.post(
        f"/api/v1/admin/products/{prod['id']}/packages",
        json={"name": "1 Month Ultra", "price": 400.0, "is_active": True},
        headers=admin_auth_headers,
    ).json()["data"]
    method = client.post(
        "/api/v1/admin/payment-methods",
        json={
            "name": "Nagad Auto",
            "type": "MANUAL",
            "account_number": "01811000000",
            "is_active": True,
        },
        headers=admin_auth_headers,
    ).json()["data"]

    # 2. Phone sends SMS Webhook BEFORE customer submits on site
    trx_b = "NAGAD_TRX_SCENARIO_B"
    sms_b = (
        f"Customer: 01822334455\n"
        f"Amount: Tk 400.00\n"
        f"TxnID: {trx_b}\n"
        f"Balance: Tk 5,000.00\n"
        f"Time: 11/09/2026 02:25"
    )
    w_res = client.post(
        "/api/v1/payments/webhook/sms",
        json={"sender": "Nagad", "message": sms_b},
        headers={"X-Device-Secret": settings.SMS_WEBHOOK_SECRET},
    )
    assert w_res.status_code == 200
    assert w_res.json()["data"]["matched"] is False  # Awaiting customer

    # 3. Customer checks out order via /orders
    order_res = client.post(
        "/api/v1/orders",
        json={"package_id": pkg["id"], "quantity": 1, "input_values": {}},
        headers=auth_headers,
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["data"]["id"]
    order_number = order_res.json()["data"]["order_number"]

    # 4. Customer submits TrxID -> instantly matches and marks VERIFIED!
    pay_res = client.post(
        "/api/v1/payments/submit",
        json={
            "order_id": order_id,
            "payment_method_id": method["id"],
            "amount": 400.0,
            "transaction_id": trx_b,
            "sender_number": "01822334455",
        },
        headers=auth_headers,
    )
    assert pay_res.status_code == 201
    # Status is immediately VERIFIED without admin!
    assert pay_res.json()["data"]["status"] == "VERIFIED"

    # 5. Order is immediately PAID
    order_check = client.get(f"/api/v1/orders/{order_number}", headers=auth_headers)
    assert order_check.json()["data"]["status"] == "PAID"


def test_sms_topup_auto_approval(client, admin_auth_headers, auth_headers):
    """Wallet top-up auto-approval and balance credit via SMS."""
    # 1. Setup payment method
    method = client.post(
        "/api/v1/admin/payment-methods",
        json={
            "name": "bKash Wallet Topup",
            "type": "MANUAL",
            "account_number": "01911000000",
            "is_active": True,
        },
        headers=admin_auth_headers,
    ).json()["data"]

    # 2. Get initial wallet balance
    init_wallet = client.get("/api/v1/wallet/me", headers=auth_headers).json()["data"][
        "balance"
    ]

    # 3. Customer submits wallet topup
    topup_trx = "TOPUP_TRX_7788"
    topup_res = client.post(
        "/api/v1/wallet/topup",
        json={
            "payment_method_id": method["id"],
            "amount": 350.0,
            "transaction_id": topup_trx,
            "sender_number": "01711889900",
        },
        headers=auth_headers,
    )
    assert topup_res.status_code == 201
    assert topup_res.json()["data"]["status"] == "PENDING"

    # 4. SMS arrives from device
    sms_topup = (
        f"You have received Tk 350.00 from 01711889900. "
        f"Fee Tk 0.00. Balance Tk 4,200.00. TrxID {topup_trx} at 11/09/2026 02:30"
    )
    w_res = client.post(
        "/api/v1/payments/webhook/sms",
        json={"sender": "bKash", "message": sms_topup},
        headers={"X-Device-Secret": settings.SMS_WEBHOOK_SECRET},
    )
    assert w_res.status_code == 200
    assert w_res.json()["data"]["matched"] is True
    assert w_res.json()["data"]["matched_entity_type"] == "WALLET_TOPUP"

    # 5. Customer wallet balance increased by 350 BDT!
    new_wallet = client.get("/api/v1/wallet/me", headers=auth_headers).json()["data"][
        "balance"
    ]
    assert new_wallet == init_wallet + 350.0


def test_sms_amount_mismatch(client, admin_auth_headers, auth_headers):
    """When SMS amount is less than order required amount, it does not auto-verify."""
    prod = client.post(
        "/api/v1/admin/products",
        json={"name": "Spotify Premium", "slug": "spotify-mismatch"},
        headers=admin_auth_headers,
    ).json()["data"]
    pkg = client.post(
        f"/api/v1/admin/products/{prod['id']}/packages",
        json={"name": "1 Year", "price": 1000.0, "is_active": True},
        headers=admin_auth_headers,
    ).json()["data"]
    method = client.post(
        "/api/v1/admin/payment-methods",
        json={
            "name": "bKash Pay",
            "account_number": "01700000000",
            "type": "MANUAL",
            "is_active": True,
        },
        headers=admin_auth_headers,
    ).json()["data"]

    order_data = client.post(
        "/api/v1/orders",
        json={"package_id": pkg["id"], "quantity": 1, "input_values": {}},
        headers=auth_headers,
    ).json()["data"]
    order_id = order_data["id"]
    order_number = order_data["order_number"]

    trx_mis = "MISMATCH_TRX_999"
    client.post(
        "/api/v1/payments/submit",
        json={
            "order_id": order_id,
            "payment_method_id": method["id"],
            "amount": 1000.0,
            "transaction_id": trx_mis,
            "sender_number": "01711223344",
        },
        headers=auth_headers,
    )

    # Customer only sent 100 BDT instead of 1000 BDT
    sms_mis = f"You have received Tk 100.00 from 01711223344. TrxID {trx_mis}"
    w_res = client.post(
        "/api/v1/payments/webhook/sms",
        json={"sender": "bKash", "message": sms_mis},
        headers={"X-Device-Secret": settings.SMS_WEBHOOK_SECRET},
    )
    assert w_res.status_code == 200
    assert w_res.json()["data"]["matched"] is False

    # Order stays unpaid
    order_check = client.get(f"/api/v1/orders/{order_number}", headers=auth_headers)
    assert order_check.json()["data"]["status"] != "PAID"


def test_admin_sms_logs(client, admin_auth_headers, auth_headers):
    # Customer forbidden
    forb = client.get("/api/v1/admin/payments/sms-logs", headers=auth_headers)
    assert forb.status_code == 403

    # Admin access
    admin_res = client.get(
        "/api/v1/admin/payments/sms-logs", headers=admin_auth_headers
    )
    assert admin_res.status_code == 200
    assert "items" in admin_res.json()["data"]
    assert "pagination" in admin_res.json()["data"]
