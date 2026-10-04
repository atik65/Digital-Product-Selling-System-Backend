def test_admin_get_user_details_and_list(client, admin_auth_headers, auth_headers, test_user):
    # 1. Non-admin cannot access admin users endpoint
    forbidden_res = client.get("/api/v1/admin/users", headers=auth_headers)
    assert forbidden_res.status_code == 403

    # 2. Admin retrieves user details by ID
    res = client.get(f"/api/v1/admin/users/{test_user.id}", headers=admin_auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    # Basic info
    assert data["id"] == test_user.id
    assert data["email"] == "testuser@example.com"
    assert data["username"] == "testuser"
    assert data["role"] == "customer"
    assert data["is_active"] is True

    # Wallet details & balance
    assert data["wallet_balance"] == 1000.0
    assert data["wallet"] is not None
    assert data["wallet"]["balance"] == 1000.0

    # Orders and topups history (initially empty)
    assert isinstance(data["orders"], list)
    assert len(data["orders"]) == 0
    assert isinstance(data["topups"], list)
    assert len(data["topups"]) == 0
    assert data["total_orders"] == 0
    assert data["total_spent"] == 0.0

    # 3. Customer submits a top-up
    pm_res = client.post(
        "/api/v1/admin/payment-methods",
        json={"name": "Nagad User Test", "account_number": "01799999999"},
        headers=admin_auth_headers,
    )
    pm_id = pm_res.json()["data"]["id"]

    topup_res = client.post(
        "/api/v1/wallet/topup",
        json={
            "payment_method_id": pm_id,
            "amount": 250.0,
            "transaction_id": "TEST_USER_TRX_99",
        },
        headers=auth_headers,
    )
    assert topup_res.status_code == 201

    # 4. Now admin retrieves user details again
    res_updated = client.get(f"/api/v1/admin/users/{test_user.id}", headers=admin_auth_headers)
    assert res_updated.status_code == 200
    u_data = res_updated.json()["data"]
    assert len(u_data["topups"]) == 1
    assert u_data["topups"][0]["transaction_id"] == "TEST_USER_TRX_99"
    assert u_data["topups"][0]["amount"] == 250.0
    assert u_data["topups"][0]["payment_method"]["name"] == "Nagad User Test"

    # 5. Admin lists all users
    list_res = client.get("/api/v1/admin/users", headers=admin_auth_headers)
    assert list_res.status_code == 200
    items = list_res.json()["data"]["items"]
    target_user = next((u for u in items if u["id"] == test_user.id), None)
    assert target_user is not None
    assert target_user["wallet_balance"] == 1000.0
    assert len(target_user["topups"]) == 1
    assert target_user["topups"][0]["transaction_id"] == "TEST_USER_TRX_99"
