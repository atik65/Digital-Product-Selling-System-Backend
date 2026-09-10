def test_payment_submission_and_admin_verification(client, admin_auth_headers, auth_headers):
    # 1. Product & Package
    p_res = client.post(
        "/api/v1/admin/products",
        json={"name": "Disney+ Hotstar", "slug": "disney-hotstar"},
        headers=admin_auth_headers,
    )
    product_id = p_res.json()["data"]["id"]

    pkg_res = client.post(
        f"/api/v1/admin/products/{product_id}/packages",
        json={"name": "Super 1 Year", "price": 400.0, "is_active": True},
        headers=admin_auth_headers,
    )
    package_id = pkg_res.json()["data"]["id"]

    # 2. Payment Method
    pm_res = client.post(
        "/api/v1/admin/payment-methods",
        json={"name": "Nagad Personal", "account_number": "01700000000"},
        headers=admin_auth_headers,
    )
    pm_id = pm_res.json()["data"]["id"]

    # 3. Direct Order
    order_res = client.post(
        "/api/v1/orders",
        json={
            "package_id": package_id,
            "quantity": 1,
            "input_values": {"mobile": "01799999999"},
            "payment_method_id": pm_id,
        },
        headers=auth_headers,
    )
    order_data = order_res.json()["data"]
    order_id = order_data["id"]
    order_number = order_data["order_number"]

    # 4. Submit Payment
    pay_res = client.post(
        "/api/v1/payments/submit",
        json={
            "order_id": order_id,
            "payment_method_id": pm_id,
            "amount": 400.0,
            "transaction_id": "TRX987654321",
            "sender_number": "01711223344",
        },
        headers=auth_headers,
    )
    assert pay_res.status_code == 201
    pay_data = pay_res.json()["data"]
    payment_id = pay_data["id"]
    assert pay_data["status"] == "VERIFYING"
    assert pay_data["transaction_id"] == "TRX987654321"

    # 5. Admin lists payments
    admin_list = client.get("/api/v1/admin/payments", headers=admin_auth_headers)
    assert admin_list.status_code == 200
    assert any(p["id"] == payment_id for p in admin_list.json()["data"]["items"])

    # 6. Admin verifies payment
    verify_res = client.post(
        f"/api/v1/admin/payments/{payment_id}/verify",
        json={"admin_note": "TRX matched on Nagad statement"},
        headers=admin_auth_headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["status"] == "VERIFIED"

    # 7. Check Order is now PAID
    ord_check = client.get(f"/api/v1/orders/{order_number}", headers=auth_headers)
    assert ord_check.status_code == 200
    assert ord_check.json()["data"]["status"] == "PAID"


def test_payment_rejection(client, admin_auth_headers, auth_headers):
    # Setup order
    p_res = client.post(
        "/api/v1/admin/products",
        json={"name": "Duolingo Plus", "slug": "duolingo-plus"},
        headers=admin_auth_headers,
    )
    pkg_res = client.post(
        f"/api/v1/admin/products/{p_res.json()['data']['id']}/packages",
        json={"name": "Monthly", "price": 150.0},
        headers=admin_auth_headers,
    )
    pm_res = client.post(
        "/api/v1/admin/payment-methods",
        json={"name": "bKash Personal", "account_number": "01822222222"},
        headers=admin_auth_headers,
    )
    pm_id = pm_res.json()["data"]["id"]

    order_res = client.post(
        "/api/v1/orders",
        json={
            "package_id": pkg_res.json()["data"]["id"],
            "quantity": 1,
            "input_values": {"duo_email": "learn@gmail.com"},
            "payment_method_id": pm_id,
        },
        headers=auth_headers,
    )
    order_id = order_res.json()["data"]["id"]

    # Submit fake payment
    pay_res = client.post(
        "/api/v1/payments/submit",
        json={
            "order_id": order_id,
            "payment_method_id": pm_id,
            "amount": 150.0,
            "transaction_id": "FAKE_TRX",
            "sender_number": "01800000000",
        },
        headers=auth_headers,
    )
    payment_id = pay_res.json()["data"]["id"]

    # Admin rejects
    rej_res = client.post(
        f"/api/v1/admin/payments/{payment_id}/reject",
        json={"reason": "Transaction ID not found in statement"},
        headers=admin_auth_headers,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["data"]["status"] == "REJECTED"
