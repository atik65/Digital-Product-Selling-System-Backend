from datetime import datetime, timezone, timedelta


def test_lottery_eligibility_and_spin(client, admin_auth_headers, auth_headers):
    # 1. Admin creates active lottery
    now = datetime.now(timezone.utc)
    lottery_res = client.post(
        "/api/v1/admin/lotteries",
        json={
            "name": "Super Spin Fiesta",
            "description": "Win coupons and discounts",
            "starts_at": (now - timedelta(days=1)).isoformat(),
            "ends_at": (now + timedelta(days=30)).isoformat(),
            "is_active": True,
        },
        headers=admin_auth_headers,
    )
    assert lottery_res.status_code == 201
    lottery_id = lottery_res.json()["data"]["id"]

    # 2. Add prize with 100% probability for predictable testing
    client.post(
        f"/api/v1/admin/lotteries/{lottery_id}/prizes",
        json={
            "discount_type": "PERCENTAGE",
            "discount_value": 25.0,
            "probability": 1.0,
            "quantity": 10,
        },
        headers=admin_auth_headers,
    )

    # 3. Check initial eligibility: 0 completed orders -> not eligible
    elig1 = client.get("/api/v1/lottery/my-eligibility", headers=auth_headers).json()[
        "data"
    ]
    assert elig1["eligible"] is False
    assert elig1["remaining_attempts"] == 0

    # 4. Attempting to spin without eligibility returns 400
    spin_fail = client.post(f"/api/v1/lottery/{lottery_id}/spin", headers=auth_headers)
    assert spin_fail.status_code == 400

    # 5. Place and pay an order with wallet to earn 1 spin attempt
    p_res = client.post(
        "/api/v1/admin/products",
        json={"name": "Sub For Spin", "slug": "sub-for-spin"},
        headers=admin_auth_headers,
    )
    pkg_res = client.post(
        f"/api/v1/admin/products/{p_res.json()['data']['id']}/packages",
        json={"name": "Basic", "price": 100.0},
        headers=admin_auth_headers,
    )
    ord_res = client.post(
        "/api/v1/orders",
        json={
            "package_id": pkg_res.json()["data"]["id"],
            "quantity": 1,
            "input_values": {"email": "spin@example.com"},
        },
        headers=auth_headers,
    )
    order_num = ord_res.json()["data"]["order_number"]
    client.post(f"/api/v1/orders/{order_num}/pay-with-wallet", headers=auth_headers)

    # 6. Check eligibility now -> 1 attempt available
    elig2 = client.get("/api/v1/lottery/my-eligibility", headers=auth_headers).json()[
        "data"
    ]
    assert elig2["eligible"] is True
    assert elig2["remaining_attempts"] == 1

    # 7. Customer spins lottery
    spin_res = client.post(f"/api/v1/lottery/{lottery_id}/spin", headers=auth_headers)
    assert spin_res.status_code == 200
    spin_data = spin_res.json()["data"]
    assert spin_data["won"] is True
    assert spin_data["prize"] is not None
    assert spin_data["prize"]["discount_value"] == 25.0

    # 8. Check my-history
    history = client.get("/api/v1/lottery/my-history", headers=auth_headers).json()[
        "data"
    ]
    assert len(history) >= 1
    assert history[0]["prize"] is not None
    assert history[0]["prize"]["discount_value"] == 25.0

    # 9. Admin checks entries
    entries = client.get(
        f"/api/v1/admin/lotteries/{lottery_id}/entries", headers=admin_auth_headers
    ).json()["data"]
    assert entries["pagination"]["total"] >= 1
