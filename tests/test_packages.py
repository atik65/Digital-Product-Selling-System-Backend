def test_package_crud_and_status(client, admin_auth_headers):
    # 1. Create product first
    p_res = client.post(
        "/api/v1/admin/products",
        json={"name": "Spotify Family", "slug": "spotify-family"},
        headers=admin_auth_headers,
    )
    product_id = p_res.json()["data"]["id"]

    # 2. Add package
    pkg_res = client.post(
        f"/api/v1/admin/products/{product_id}/packages",
        json={
            "name": "1 Month Plan",
            "price": 199.0,
            "compare_price": 250.0,
            "duration": "30 Days",
            "sort_order": 1,
            "is_active": True,
        },
        headers=admin_auth_headers,
    )
    assert pkg_res.status_code == 201
    pkg_data = pkg_res.json()["data"]
    package_id = pkg_data["id"]
    assert pkg_data["name"] == "1 Month Plan"
    assert pkg_data["price"] == 199.0

    # 3. Public list packages
    list_res = client.get(f"/api/v1/products/{product_id}/packages")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) == 1

    # 4. Update package details
    upd_res = client.put(
        f"/api/v1/admin/packages/{package_id}",
        json={"name": "1 Month Ultra", "price": 220.0},
        headers=admin_auth_headers,
    )
    assert upd_res.status_code == 200
    assert upd_res.json()["data"]["name"] == "1 Month Ultra"
    assert upd_res.json()["data"]["price"] == 220.0

    # 5. Toggle status
    status_res = client.patch(
        f"/api/v1/admin/packages/{package_id}/status",
        json={"is_active": False},
        headers=admin_auth_headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["data"]["is_active"] is False

    # Should no longer be visible in public active packages
    list_after_deactivate = client.get(f"/api/v1/products/{product_id}/packages")
    assert len(list_after_deactivate.json()["data"]) == 0

    # 6. Delete package
    del_res = client.delete(
        f"/api/v1/admin/packages/{package_id}", headers=admin_auth_headers
    )
    assert del_res.status_code == 200
