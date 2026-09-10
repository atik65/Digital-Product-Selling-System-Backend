def test_create_and_list_categories(client, admin_auth_headers):
    # Create category as admin
    create_payload = {
        "name": "Streaming Services",
        "slug": "streaming-services",
        "description": "OTT subscriptions",
        "is_active": True,
        "sort_order": 1,
    }
    res = client.post(
        "/api/v1/admin/categories", json=create_payload, headers=admin_auth_headers
    )
    assert res.status_code == 201
    cat_id = res.json()["data"]["id"]

    # Public list active
    res = client.get("/api/v1/categories")
    assert res.status_code == 200
    cats = res.json()["data"]
    assert any(c["slug"] == "streaming-services" for c in cats)

    # Public get single
    res = client.get("/api/v1/categories/streaming-services")
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Streaming Services"

    # Reorder as admin
    res = client.patch(
        f"/api/v1/admin/categories/{cat_id}/reorder",
        json={"sort_order": 10},
        headers=admin_auth_headers,
    )
    assert res.status_code == 200
    assert res.json()["data"]["sort_order"] == 10
