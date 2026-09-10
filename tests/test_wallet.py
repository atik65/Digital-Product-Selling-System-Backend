def test_wallet_balance_and_pay_order(client, admin_auth_headers, auth_headers, test_user):
    # 1. Check initial wallet balance (1000.0 from conftest fixture)
    w_res = client.get("/api/v1/wallet/me", headers=auth_headers)
    assert w_res.status_code == 200
    assert w_res.json()["data"]["balance"] == 1000.0

    # 2. Setup product & package costing 300 BDT
    p_res = client.post(
        "/api/v1/admin/products",
        json={"name": "Spotify Solo", "slug": "spotify-solo"},
        headers=admin_auth_headers,
    )
    pkg_res = client.post(
        f"/api/v1/admin/products/{p_res.json()['data']['id']}/packages",
        json={"name": "Monthly", "price": 300.0},
        headers=admin_auth_headers,
    )
    package_id = pkg_res.json()["data"]["id"]

    # 3. Create direct order
    order_res = client.post(
        "/api/v1/orders",
        json={
            "package_id": package_id,
            "quantity": 1,
            "input_values": {"email": "user@spotify.com"},
        },
        headers=auth_headers,
    )
    order_number = order_res.json()["data"]["order_number"]

    # 4. Pay order using wallet
    pay_res = client.post(f"/api/v1/orders/{order_number}/pay-with-wallet", headers=auth_headers)
    assert pay_res.status_code == 200
    assert pay_res.json()["data"]["amount_paid"] == 300.0
    assert pay_res.json()["data"]["remaining_balance"] == 700.0

    # 5. Check order status is now PAID
    chk_order = client.get(f"/api/v1/orders/{order_number}", headers=auth_headers)
    assert chk_order.json()["data"]["status"] == "PAID"

    # 6. Verify ledger transaction recorded
    tx_res = client.get("/api/v1/wallet/transactions", headers=auth_headers)
    assert tx_res.status_code == 200
    items = tx_res.json()["data"]["items"]
    assert any(tx["type"] == "PURCHASE" and tx["amount"] == -300.0 for tx in items)


def test_wallet_insufficient_balance(client, admin_auth_headers, auth_headers, test_user):
    # Product costing 2000 BDT (balance is 1000)
    p_res = client.post(
        "/api/v1/admin/products",
        json={"name": "High End Sub", "slug": "high-end-sub"},
        headers=admin_auth_headers,
    )
    pkg_res = client.post(
        f"/api/v1/admin/products/{p_res.json()['data']['id']}/packages",
        json={"name": "Annual", "price": 2000.0},
        headers=admin_auth_headers,
    )
    order_res = client.post(
        "/api/v1/orders",
        json={
            "package_id": pkg_res.json()["data"]["id"],
            "quantity": 1,
            "input_values": {"uid": "123"},
        },
        headers=auth_headers,
    )
    order_number = order_res.json()["data"]["order_number"]

    # Payment fails due to insufficient balance
    pay_res = client.post(f"/api/v1/orders/{order_number}/pay-with-wallet", headers=auth_headers)
    assert pay_res.status_code == 400
    assert "Insufficient wallet balance" in pay_res.json()["message"]


def test_admin_wallet_adjust(client, admin_auth_headers, auth_headers, test_user):
    # Admin adds 500 bonus
    adj_res = client.post(
        f"/api/v1/admin/wallets/{test_user.id}/adjust",
        json={
            "amount": 500.0,
            "type": "BONUS",
            "reason": "Promotional campaign reward",
        },
        headers=admin_auth_headers,
    )
    assert adj_res.status_code == 200
    assert adj_res.json()["data"]["balance"] >= 1500.0
