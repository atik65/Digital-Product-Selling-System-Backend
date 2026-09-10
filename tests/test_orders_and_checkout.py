def setup_test_catalog(client, admin_auth_headers):
    # Create product
    p_res = client.post(
        "/api/v1/admin/products",
        json={
            "name": "Netflix Direct",
            "slug": "netflix-direct",
            "is_active": True,
        },
        headers=admin_auth_headers,
    )
    product_id = p_res.json()["data"]["id"]

    # Add required input field
    client.post(
        f"/api/v1/admin/products/{product_id}/fields",
        json={
            "name": "profile_email",
            "label": "Profile Email",
            "type": "email",
            "is_required": True,
            "sort_order": 1,
        },
        headers=admin_auth_headers,
    )

    # Add package
    pkg_res = client.post(
        f"/api/v1/admin/products/{product_id}/packages",
        json={
            "name": "1 Screen Ultra",
            "price": 300.0,
            "is_active": True,
        },
        headers=admin_auth_headers,
    )
    package_id = pkg_res.json()["data"]["id"]

    # Add coupon
    client.post(
        "/api/v1/admin/coupons",
        json={
            "code": "DISCOUNT50",
            "type": "FIXED",
            "value": 50.0,
            "minimum_order_amount": 200.0,
            "is_active": True,
        },
        headers=admin_auth_headers,
    )

    return product_id, package_id


def test_checkout_preview_and_direct_order(client, admin_auth_headers, auth_headers):
    product_id, package_id = setup_test_catalog(client, admin_auth_headers)

    # 1. Preview checkout
    preview_res = client.post(
        "/api/v1/checkout/preview",
        json={
            "package_id": package_id,
            "quantity": 2,
            "coupon_code": "DISCOUNT50",
            "input_values": {"profile_email": "streamer@gmail.com"},
        },
        headers=auth_headers,
    )
    assert preview_res.status_code == 200
    prev_data = preview_res.json()["data"]
    assert prev_data["subtotal"] == 600.0
    assert prev_data["discount"] == 50.0
    assert prev_data["total"] == 550.0

    # 2. Place order with missing required input field -> 400 error
    bad_order_res = client.post(
        "/api/v1/orders",
        json={
            "package_id": package_id,
            "quantity": 1,
            "input_values": {},
        },
        headers=auth_headers,
    )
    assert bad_order_res.status_code == 400

    # 3. Place order successfully
    order_res = client.post(
        "/api/v1/orders",
        json={
            "package_id": package_id,
            "quantity": 1,
            "coupon_code": "DISCOUNT50",
            "input_values": {"profile_email": "valid_user@example.com"},
            "customer_note": "Please deliver quickly",
        },
        headers=auth_headers,
    )
    assert order_res.status_code == 201
    order_data = order_res.json()["data"]
    order_number = order_data["order_number"]
    assert order_data["subtotal"] == 300.0
    assert order_data["discount"] == 50.0
    assert order_data["total_amount"] == 250.0
    assert order_data["status"] in ["PENDING", "PAYMENT_PENDING"]

    # 4. View in my-orders
    my_res = client.get("/api/v1/orders/my-orders", headers=auth_headers)
    assert my_res.status_code == 200
    assert len(my_res.json()["data"]["items"]) >= 1
    assert my_res.json()["data"]["pagination"]["total"] >= 1

    # 5. View single order
    single_res = client.get(f"/api/v1/orders/{order_number}", headers=auth_headers)
    assert single_res.status_code == 200
    assert single_res.json()["data"]["order_number"] == order_number

    # 6. Admin can see order and update status
    admin_list = client.get("/api/v1/admin/orders", headers=admin_auth_headers)
    assert admin_list.status_code == 200
    order_id = order_data["id"]

    status_res = client.patch(
        f"/api/v1/admin/orders/{order_id}/status",
        json={"status": "PROCESSING"},
        headers=admin_auth_headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["data"]["status"] == "PROCESSING"

    # 7. Admin can add delivery fulfillment note
    note_res = client.patch(
        f"/api/v1/admin/orders/{order_id}/note",
        json={"admin_note": "Delivered Pin: 4920"},
        headers=admin_auth_headers,
    )
    assert note_res.status_code == 200
    assert note_res.json()["data"]["admin_note"] == "Delivered Pin: 4920"


def test_cancel_pending_order(client, admin_auth_headers, auth_headers):
    product_id, package_id = setup_test_catalog(client, admin_auth_headers)

    order_res = client.post(
        "/api/v1/orders",
        json={
            "package_id": package_id,
            "quantity": 1,
            "input_values": {"profile_email": "cancelme@example.com"},
        },
        headers=auth_headers,
    )
    order_number = order_res.json()["data"]["order_number"]

    # Customer cancels order
    cancel_res = client.post(f"/api/v1/orders/{order_number}/cancel", headers=auth_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"
