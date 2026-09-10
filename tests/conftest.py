import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.product import Product  # noqa: F401
from app.models.user import User

# In-memory SQLite for super-fast, isolated testing with zero disk footprints
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Provides a fresh database session for each test and drops all tables afterward."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Provides a FastAPI TestClient with overridden DB dependency and disabled rate limiting."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Disable rate limiter during tests to avoid accidental 429 errors
    app.state.limiter.enabled = False

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup overrides and re-enable rate limiter
    app.dependency_overrides.clear()
    app.state.limiter.enabled = True


@pytest.fixture(scope="function")
def test_user(db) -> User:
    """Fixture to create and return a regular test user."""
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password=hash_password("password123"),
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user: User) -> dict:
    """Fixture providing Bearer authorization headers for the regular test user."""
    token = create_access_token(user_id=test_user.id, role=test_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_user(db) -> User:
    """Fixture to create and return an admin test user."""
    admin = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def admin_auth_headers(admin_user: User) -> dict:
    """Fixture providing Bearer authorization headers for the admin test user."""
    token = create_access_token(user_id=admin_user.id, role=admin_user.role)
    return {"Authorization": f"Bearer {token}"}
