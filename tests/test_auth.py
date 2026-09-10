def test_register_user_success(client):
    """Test registering a new user succeeds with 201 Created."""
    payload = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "securepassword123",
        "role": "user",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == payload["email"]
    assert data["data"]["username"] == payload["username"]
    assert "id" in data["data"]
    assert "hashed_password" not in data["data"]


def test_register_user_duplicate_email(client, test_user):
    """Test registering with an existing email returns 409 Conflict."""
    payload = {
        "email": test_user.email,
        "username": "uniqueusername",
        "password": "password123",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False


def test_register_user_validation_error(client):
    """Test registering with a short password fails validation."""
    payload = {
        "email": "invalid@example.com",
        "username": "invalid",
        "password": "123",  # min_length is 6
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422


def test_login_success(client, test_user):
    """Test logging in with valid credentials returns JWT tokens."""
    payload = {
        "email_or_username": test_user.email,
        "password": "password123",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


def test_login_invalid_password(client, test_user):
    """Test logging in with an incorrect password returns 401 Unauthorized."""
    payload = {
        "email_or_username": test_user.email,
        "password": "wrongpassword",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_login_user_not_found(client):
    """Test logging in with a non-existent user returns 401 Unauthorized."""
    payload = {
        "email_or_username": "nonexistent@example.com",
        "password": "somepassword",
    }
    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_get_current_user_profile_authenticated(client, auth_headers, test_user):
    """Test GET /auth/me with valid Bearer token returns user profile."""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == test_user.email
    assert data["data"]["username"] == test_user.username


def test_get_current_user_profile_unauthorized(client):
    """Test GET /auth/me without token returns 401 Unauthorized."""
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_refresh_token_success(client, test_user):
    """Test refreshing access token using a valid refresh token."""
    login_res = client.post(
        "/auth/login",
        json={"email_or_username": test_user.email, "password": "password123"},
    )
    refresh_token = login_res.json()["data"]["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
