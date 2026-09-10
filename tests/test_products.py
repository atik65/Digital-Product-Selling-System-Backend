def test_admin_create_product_success(client, admin_auth_headers):
    """Test admin can successfully create a new digital product."""
    payload = {
        "name": "Discord Nitro",
        "slug": "discord-nitro",
        "description": "Unlock premium Discord perks",
        "instructions": "Enter your Discord tag or claimed gift email.",
        "is_active": True,
        "sort_order": 1,
    }
    response = client.post(
        "/api/v1/admin/products", json=payload, headers=admin_auth_headers
    )
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Discord Nitro"
    assert data["data"]["slug"] == "discord-nitro"
    assert "id" in data["data"]


def test_customer_cannot_create_product(client, auth_headers):
    """Test regular customer cannot create product (403 Forbidden)."""
    payload = {
        "name": "Spotify Premium",
        "slug": "spotify-premium",
    }
    response = client.post("/api/v1/admin/products", json=payload, headers=auth_headers)
    assert response.status_code == 403


def test_list_products_public(client, admin_auth_headers):
    """Test public can browse active products."""
    # Seed a product via admin
    client.post(
        "/api/v1/admin/products",
        json={"name": "Steam Wallet", "slug": "steam-wallet", "is_active": True},
        headers=admin_auth_headers,
    )

    response = client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert any(p["slug"] == "steam-wallet" for p in data["data"]["items"])


def test_get_product_by_slug(client, admin_auth_headers):
    """Test retrieving product detail by slug with packages and input fields."""
    client.post(
        "/api/v1/admin/products",
        json={
            "name": "Telegram Premium",
            "slug": "telegram-premium",
            "is_active": True,
        },
        headers=admin_auth_headers,
    )

    response = client.get("/api/v1/products/telegram-premium")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["slug"] == "telegram-premium"
    assert "packages" in data["data"]
    assert "input_fields" in data["data"]


def test_get_product_not_found(client):
    """Test querying nonexistent product slug returns 404."""
    response = client.get("/api/v1/products/nonexistent-product")
    assert response.status_code == 404
    assert response.json()["success"] is False


def test_admin_update_product(client, admin_auth_headers):
    """Test admin can update product metadata."""
    create_res = client.post(
        "/api/v1/admin/products",
        json={"name": "Old App", "slug": "old-app", "is_active": True},
        headers=admin_auth_headers,
    )
    product_id = create_res.json()["data"]["id"]

    update_payload = {"name": "New App Name", "description": "Fresh description"}
    response = client.put(
        f"/api/v1/admin/products/{product_id}",
        json=update_payload,
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New App Name"


def test_admin_update_product_status(client, admin_auth_headers):
    """Test admin can toggle product active status."""
    create_res = client.post(
        "/api/v1/admin/products",
        json={"name": "Draft Product", "slug": "draft-product", "is_active": True},
        headers=admin_auth_headers,
    )
    product_id = create_res.json()["data"]["id"]

    response = client.patch(
        f"/api/v1/admin/products/{product_id}/status",
        json={"is_active": False},
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_active"] is False


def test_admin_delete_product(client, admin_auth_headers):
    """Test admin can soft delete product."""
    create_res = client.post(
        "/api/v1/admin/products",
        json={"name": "To Delete", "slug": "to-delete", "is_active": True},
        headers=admin_auth_headers,
    )
    product_id = create_res.json()["data"]["id"]

    delete_res = client.delete(
        f"/api/v1/admin/products/{product_id}", headers=admin_auth_headers
    )
    assert delete_res.status_code == 200

    # Verify not found in public query
    get_res = client.get("/api/v1/products/to-delete")
    assert get_res.status_code == 404
