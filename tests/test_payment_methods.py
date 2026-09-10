def test_payment_methods_flow(client, admin_auth_headers, auth_headers):
    # 1. Admin creates payment method (e.g. bKash)
    create_res = client.post(
        "/admin/payment-methods",
        json={
            "name": "bKash Merchant",
            "account_number": "01800000000",
            "instructions": "Make Payment to merchant number",
            "is_active": True,
            "sort_order": 1,
        },
        headers=admin_auth_headers,
    )
    assert create_res.status_code == 201
    method_data = create_res.json()["data"]
    method_id = method_data["id"]
    assert method_data["name"] == "bKash Merchant"

    # 2. Public can view active methods
    public_res = client.get("/payment-methods")
    assert public_res.status_code == 200
    assert any(m["id"] == method_id for m in public_res.json()["data"])

    # 3. Customer cannot create payment method
    cust_res = client.post(
        "/admin/payment-methods",
        json={"name": "Fake Pay", "account_number": "0000"},
        headers=auth_headers,
    )
    assert cust_res.status_code == 403

    # 4. Admin updates payment method
    upd_res = client.put(
        f"/admin/payment-methods/{method_id}",
        json={"account_number": "01811111111", "instructions": "Updated instructions"},
        headers=admin_auth_headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["data"]["account_number"] == "01811111111"

    # 5. Admin deletes payment method
    del_res = client.delete(f"/admin/payment-methods/{method_id}", headers=admin_auth_headers)
    assert del_res.status_code == 200

    # Verify not in public active methods
    after_del = client.get("/payment-methods")
    assert not any(m["id"] == method_id for m in after_del.json()["data"])
