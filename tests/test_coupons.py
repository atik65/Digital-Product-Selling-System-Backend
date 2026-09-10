from datetime import datetime, timezone, timedelta


def test_coupon_validation_percentage_and_fixed(client, admin_auth_headers, auth_headers):
    # 1. Create a product and package for testing
    p_res = client.post(
        "/admin/products",
        json={"name": "Canva Subscription", "slug": "canva-sub"},
        headers=admin_auth_headers,
    )
    product_id = p_res.json()["data"]["id"]

    pkg_res = client.post(
        f"/admin/products/{product_id}/packages",
        json={"name": "1 Year", "price": 500.0, "is_active": True},
        headers=admin_auth_headers,
    )
    package_id = pkg_res.json()["data"]["id"]

    # 2. Admin creates 10% coupon with 30 BDT cap and min order 400 BDT
    c1_res = client.post(
        "/admin/coupons",
        json={
            "code": "TEST10",
            "type": "PERCENTAGE",
            "value": 10.0,
            "max_discount": 30.0,
            "minimum_order_amount": 400.0,
            "usage_limit": 10,
            "per_user_limit": 1,
            "is_active": True,
        },
        headers=admin_auth_headers,
    )
    assert c1_res.status_code == 201

    # 3. Validate coupon: 10% of 500 is 50, but max discount is 30, so discount should be 30
    val_res = client.post(
        "/coupons/validate",
        json={"code": "TEST10", "package_id": package_id, "quantity": 1},
        headers=auth_headers,
    )
    assert val_res.status_code == 200
    val_data = val_res.json()["data"]
    assert val_data["valid"] is True
    assert val_data["discount_amount"] == 30.0

    # 4. Admin creates fixed 50 BDT coupon with min order 600
    client.post(
        "/admin/coupons",
        json={
            "code": "FIXED50",
            "type": "FIXED",
            "value": 50.0,
            "minimum_order_amount": 600.0,
            "is_active": True,
        },
        headers=admin_auth_headers,
    )

    # Validate against quantity 1 (subtotal 500 < min 600) -> fails with 400
    fail_res = client.post(
        "/coupons/validate",
        json={"code": "FIXED50", "package_id": package_id, "quantity": 1},
        headers=auth_headers,
    )
    assert fail_res.status_code == 400

    # Validate against quantity 2 (subtotal 1000 >= min 600) -> succeeds with discount 50
    success_res = client.post(
        "/coupons/validate",
        json={"code": "FIXED50", "package_id": package_id, "quantity": 2},
        headers=auth_headers,
    )
    assert success_res.status_code == 200
    assert success_res.json()["data"]["discount_amount"] == 50.0


def test_coupon_expired_or_invalid(client, admin_auth_headers, auth_headers):
    # Create product & package
    p_res = client.post(
        "/admin/products",
        json={"name": "Prime Video", "slug": "prime-video"},
        headers=admin_auth_headers,
    )
    pkg_res = client.post(
        f"/admin/products/{p_res.json()['data']['id']}/packages",
        json={"name": "1 Month", "price": 200.0, "is_active": True},
        headers=admin_auth_headers,
    )
    pkg_id = pkg_res.json()["data"]["id"]

    # Expired coupon
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    client.post(
        "/admin/coupons",
        json={
            "code": "EXPIRED",
            "type": "FIXED",
            "value": 20.0,
            "expires_at": yesterday,
            "is_active": True,
        },
        headers=admin_auth_headers,
    )

    exp_res = client.post(
        "/coupons/validate",
        json={"code": "EXPIRED", "package_id": pkg_id, "quantity": 1},
        headers=auth_headers,
    )
    assert exp_res.status_code == 400

    # Nonexistent coupon
    none_res = client.post(
        "/coupons/validate",
        json={"code": "NONEXISTENT", "package_id": pkg_id, "quantity": 1},
        headers=auth_headers,
    )
    assert none_res.status_code == 400
