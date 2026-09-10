def test_topup_submission_and_admin_approval(client, admin_auth_headers, auth_headers):
    # 1. Create payment method for top-up
    pm_res = client.post(
        "/api/v1/admin/payment-methods",
        json={"name": "Rocket TopUp", "account_number": "01999999999"},
        headers=admin_auth_headers,
    )
    pm_id = pm_res.json()["data"]["id"]

    # Initial wallet balance
    init_w = client.get("/api/v1/wallet/me", headers=auth_headers).json()["data"][
        "balance"
    ]

    # 2. Customer submits top-up for 500 BDT
    topup_res = client.post(
        "/api/v1/wallet/topup",
        json={
            "payment_method_id": pm_id,
            "amount": 500.0,
            "transaction_id": "TOPUP_TRX_123",
            "sender_number": "01911223344",
        },
        headers=auth_headers,
    )
    assert topup_res.status_code == 201
    topup_data = topup_res.json()["data"]
    topup_id = topup_data["id"]
    assert topup_data["status"] == "PENDING"
    assert topup_data["amount"] == 500.0

    # 3. Customer checks my topups
    my_topups = client.get("/api/v1/wallet/topups/me", headers=auth_headers)
    assert my_topups.status_code == 200
    assert any(t["id"] == topup_id for t in my_topups.json()["data"])

    # 4. Admin lists topups
    admin_topups = client.get("/api/v1/admin/topups", headers=admin_auth_headers)
    assert admin_topups.status_code == 200
    assert any(t["id"] == topup_id for t in admin_topups.json()["data"]["items"])

    # 5. Admin approves top-up
    appr_res = client.post(
        f"/api/v1/admin/topups/{topup_id}/approve",
        json={"admin_note": "Verified in Rocket statement"},
        headers=admin_auth_headers,
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["data"]["status"] == "APPROVED"

    # 6. Check customer wallet was credited
    new_w = client.get("/api/v1/wallet/me", headers=auth_headers).json()["data"][
        "balance"
    ]
    assert new_w == init_w + 500.0

    # 7. Check wallet transaction ledger
    txs = client.get("/api/v1/wallet/transactions", headers=auth_headers).json()[
        "data"
    ]["items"]
    assert any(tx["type"] == "TOPUP" and tx["amount"] == 500.0 for tx in txs)


def test_topup_rejection(client, admin_auth_headers, auth_headers):
    pm_res = client.post(
        "/api/v1/admin/payment-methods",
        json={"name": "bKash TopUp", "account_number": "01888888888"},
        headers=admin_auth_headers,
    )
    pm_id = pm_res.json()["data"]["id"]

    init_w = client.get("/api/v1/wallet/me", headers=auth_headers).json()["data"][
        "balance"
    ]

    topup_res = client.post(
        "/api/v1/wallet/topup",
        json={
            "payment_method_id": pm_id,
            "amount": 250.0,
            "transaction_id": "INVALID_TRX_999",
            "sender_number": "01800000000",
        },
        headers=auth_headers,
    )
    topup_id = topup_res.json()["data"]["id"]

    # Admin rejects
    rej_res = client.post(
        f"/api/v1/admin/topups/{topup_id}/reject",
        json={"admin_note": "Invalid TRX, money not received"},
        headers=admin_auth_headers,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["data"]["status"] == "REJECTED"

    # Wallet remains unchanged
    after_w = client.get("/api/v1/wallet/me", headers=auth_headers).json()["data"][
        "balance"
    ]
    assert after_w == init_w
