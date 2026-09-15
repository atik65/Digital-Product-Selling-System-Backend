from unittest.mock import patch


def test_admin_login_success(client, admin_user):
    """Test logging in as admin with valid credentials returns JWT tokens."""
    payload = {
        "email": admin_user.email,
        "password": "adminpass123",
    }
    response = client.post("/api/v1/auth/admin/login", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["user"]["role"] == "admin"


def test_admin_login_invalid_password(client, admin_user):
    """Test admin login with wrong password fails with 401."""
    payload = {
        "email": admin_user.email,
        "password": "wrongadminpass",
    }
    response = client.post("/api/v1/auth/admin/login", json=payload)
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_admin_login_non_admin_forbidden(client, test_user):
    """Test customer user attempting admin login gets 403 Forbidden."""
    payload = {
        "email": test_user.email,
        "password": "password123",
    }
    response = client.post("/api/v1/auth/admin/login", json=payload)
    assert response.status_code == 403
    assert response.json()["success"] is False


@patch("app.services.auth_service.google_id_token.verify_oauth2_token")
def test_google_login_new_user_and_existing(mock_verify, client):
    """Test Google OAuth2 login creates new user and subsequent login finds existing."""
    mock_verify.return_value = {
        "sub": "google-uid-12345",
        "email": "googler@example.com",
        "name": "Google User",
        "picture": "https://example.com/avatar.jpg",
    }

    # 1. First login creates user & wallet
    payload = {"id_token": "fake-google-jwt-token"}
    res1 = client.post("/api/v1/auth/google", json=payload)
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert data1["user"]["email"] == "googler@example.com"
    assert data1["user"]["role"] == "customer"
    assert "access_token" in data1

    # 2. Second login retrieves same user
    res2 = client.post("/api/v1/auth/google", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert data2["user"]["id"] == data1["user"]["id"]


def test_get_current_user_profile_authenticated(client, auth_headers, test_user):
    """Test GET /api/v1/auth/me with valid Bearer token returns customer profile."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == test_user.email
    assert data["data"]["username"] == test_user.username


def test_get_current_user_profile_unauthorized(client):
    """Test GET /api/v1/auth/me without token returns 401 Unauthorized."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_update_current_user_profile(client, auth_headers):
    """Test PATCH /api/v1/auth/me updates customer name and phone."""
    payload = {"name": "Updated Customer Name", "phone": "+8801700000000"}
    response = client.patch("/api/v1/auth/me", headers=auth_headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Updated Customer Name"
    assert data["data"]["phone"] == "+8801700000000"


def test_refresh_token_success(client, admin_user):
    """Test refreshing access token using a valid refresh token."""
    login_res = client.post(
        "/api/v1/auth/admin/login",
        json={"email": admin_user.email, "password": "adminpass123"},
    )
    refresh_token = login_res.json()["data"]["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_signup_success_default_role_user(client, db):
    """Test user signup with required email and password assigns default role 'user' and creates wallet."""
    from app.models.wallet import Wallet
    from app.models.user import User

    payload = {
        "email": "newuser@example.com",
        "password": "strongpassword123",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["message"] == "User registered successfully"
    user_info = data["data"]["user"]
    assert user_info["email"] == "newuser@example.com"
    assert user_info["role"] == "user"
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"

    # Verify user in database
    created_user = db.query(User).filter(User.email == "newuser@example.com").first()
    assert created_user is not None
    assert created_user.role == "user"

    # Verify wallet was initialized
    wallet = db.query(Wallet).filter(Wallet.user_id == created_user.id).first()
    assert wallet is not None
    assert wallet.balance == 0.0


def test_signup_with_custom_username_and_name(client):
    """Test user signup with custom username and name."""
    payload = {
        "email": "customname@example.com",
        "password": "strongpassword123",
        "name": "Custom Full Name",
        "username": "custom_handle",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201

    data = response.json()["data"]
    assert data["user"]["username"] == "custom_handle"
    assert data["user"]["name"] == "Custom Full Name"
    assert data["user"]["role"] == "user"


def test_signup_duplicate_email(client, test_user):
    """Test signup with already registered email fails with 400."""
    payload = {
        "email": test_user.email,
        "password": "anypassword123",
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["message"].lower()


def test_signup_duplicate_username(client, test_user):
    """Test signup with already taken username fails with 400."""
    payload = {
        "email": "unregistered@example.com",
        "password": "anypassword123",
        "username": test_user.username,
    }
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 400
    assert "already taken" in response.json()["message"].lower()


def test_signup_missing_required_fields(client):
    """Test signup without password or email returns 422 validation error."""
    res_no_password = client.post(
        "/api/v1/auth/signup", json={"email": "nopass@example.com"}
    )
    assert res_no_password.status_code == 422

    res_no_email = client.post("/api/v1/auth/signup", json={"password": "noemailpass"})
    assert res_no_email.status_code == 422
