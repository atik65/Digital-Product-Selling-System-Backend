def test_create_product_authenticated(client, auth_headers):
    """Test creating a product with valid credentials succeeds."""
    payload = {
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse",
        "price": 29.99,
        "stock_quantity": 50,
    }
    response = client.post("/products/", json=payload, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == payload["name"]
    assert data["data"]["price"] == payload["price"]
    assert "id" in data["data"]


def test_create_product_unauthorized(client):
    """Test creating a product without auth returns 401 Unauthorized."""
    payload = {
        "name": "Keyboard",
        "description": "Mechanical keyboard",
        "price": 79.99,
        "stock_quantity": 20,
    }
    response = client.post("/products/", json=payload)
    assert response.status_code == 401


def test_list_products(client, auth_headers):
    """Test listing products returns paginated result."""
    # Create a product first
    client.post(
        "/products/",
        json={
            "name": "Monitor",
            "description": "4K Ultra HD",
            "price": 299.99,
            "stock_quantity": 10,
        },
        headers=auth_headers,
    )

    response = client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "items" in data["data"]
    assert len(data["data"]["items"]) >= 1


def test_get_product_by_id(client, auth_headers):
    """Test retrieving a single product by its ID."""
    create_res = client.post(
        "/products/",
        json={
            "name": "Desk Mat",
            "description": "Large mouse pad",
            "price": 19.99,
            "stock_quantity": 100,
        },
        headers=auth_headers,
    )
    product_id = create_res.json()["data"]["id"]

    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == product_id


def test_get_product_not_found(client):
    """Test retrieving a non-existent product returns 404 Not Found."""
    response = client.get("/products/99999")
    assert response.status_code == 404
    assert response.json()["success"] is False


def test_update_product(client, auth_headers):
    """Test updating a product's fields."""
    create_res = client.post(
        "/products/",
        json={
            "name": "Old Name",
            "description": "Old desc",
            "price": 15.0,
            "stock_quantity": 5,
        },
        headers=auth_headers,
    )
    product_id = create_res.json()["data"]["id"]

    update_payload = {
        "name": "New Name",
        "description": "Updated desc",
        "price": 25.0,
        "stock_quantity": 10,
    }
    response = client.put(f"/products/{product_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "New Name"
    assert response.json()["data"]["price"] == 25.0


def test_delete_product_admin_success(client, auth_headers, admin_auth_headers):
    """Test that an admin user can delete a product."""
    create_res = client.post(
        "/products/",
        json={
            "name": "Item To Delete",
            "description": "Temporary",
            "price": 10.0,
            "stock_quantity": 1,
        },
        headers=auth_headers,
    )
    product_id = create_res.json()["data"]["id"]

    # Delete with admin headers
    delete_res = client.delete(f"/products/{product_id}", headers=admin_auth_headers)
    assert delete_res.status_code == 200
    assert delete_res.json()["success"] is True

    # Verify it is gone
    get_res = client.get(f"/products/{product_id}")
    assert get_res.status_code == 404


def test_delete_product_forbidden_for_regular_user(client, auth_headers):
    """Test that a non-admin user cannot delete a product (403 Forbidden)."""
    create_res = client.post(
        "/products/",
        json={
            "name": "Protected Item",
            "description": "Cannot delete",
            "price": 50.0,
            "stock_quantity": 5,
        },
        headers=auth_headers,
    )
    product_id = create_res.json()["data"]["id"]

    # Delete with regular user headers (should fail with 403)
    delete_res = client.delete(f"/products/{product_id}", headers=auth_headers)
    assert delete_res.status_code == 403
    assert delete_res.json()["success"] is False
