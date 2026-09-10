def test_site_settings_flow(client, admin_auth_headers, auth_headers):
    # 1. Public get site settings
    res = client.get("/settings")
    assert res.status_code == 200
    assert "site_name" in res.json()["data"]

    # 2. Customer cannot update settings (403 Forbidden)
    cust_res = client.put(
        "/admin/settings",
        json={"site_name": "Hacked Name"},
        headers=auth_headers,
    )
    assert cust_res.status_code == 403

    # 3. Admin updates site settings
    admin_res = client.put(
        "/admin/settings",
        json={
            "site_name": "BoostGhor Elite",
            "support_phone": "+8801999888777",
            "telegram_url": "https://t.me/boostghorelite",
        },
        headers=admin_auth_headers,
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["data"]["site_name"] == "BoostGhor Elite"
    assert admin_res.json()["data"]["support_phone"] == "+8801999888777"


def test_banners_and_popups(client, admin_auth_headers):
    # 1. Create banner
    b_res = client.post(
        "/admin/banners",
        json={
            "image": "https://example.com/banner.png",
            "title": "Summer Super Sale",
            "description": "50% off all streaming passes",
            "button_text": "Shop Now",
            "button_url": "/products",
            "is_active": True,
            "sort_order": 1,
        },
        headers=admin_auth_headers,
    )
    assert b_res.status_code == 201
    banner_id = b_res.json()["data"]["id"]

    # 2. Public view banners
    pub_b = client.get("/banners")
    assert pub_b.status_code == 200
    assert any(b["id"] == banner_id for b in pub_b.json()["data"])

    # 3. Update banner
    upd_b = client.put(
        f"/admin/banners/{banner_id}",
        json={"title": "Monsoon Super Sale"},
        headers=admin_auth_headers,
    )
    assert upd_b.status_code == 200
    assert upd_b.json()["data"]["title"] == "Monsoon Super Sale"

    # 4. Delete banner
    del_b = client.delete(f"/admin/banners/{banner_id}", headers=admin_auth_headers)
    assert del_b.status_code == 200

    # 5. Create popup
    pop_res = client.post(
        "/admin/popups",
        json={
            "title": "Special Flash Discount!",
            "content": "Use coupon FLASH20 for 20 BDT discount today only!",
            "is_active": True,
        },
        headers=admin_auth_headers,
    )
    assert pop_res.status_code == 201
    popup_id = pop_res.json()["data"]["id"]

    # 6. Public view active popup
    active_pop = client.get("/popups/active")
    assert active_pop.status_code == 200
    assert active_pop.json()["data"]["id"] == popup_id
