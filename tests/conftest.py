import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app as fastapi_app
import app.models  # noqa: F401 - registers all entities onto Base.metadata
from app.models.user import User
from app.models.wallet import Wallet

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

    fastapi_app.dependency_overrides[get_db] = override_get_db

    # Disable rate limiter during tests to avoid accidental 429 errors
    fastapi_app.state.limiter.enabled = False

    with TestClient(fastapi_app) as test_client:
        yield test_client

    # Cleanup overrides and re-enable rate limiter
    fastapi_app.dependency_overrides.clear()
    fastapi_app.state.limiter.enabled = True


@pytest.fixture(scope="function")
def test_user(db) -> User:
    """Fixture to create and return a regular test customer with an initialized wallet."""
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password=hash_password("password123"),
        role="customer",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    wallet = Wallet(user_id=user.id, balance=1000.0)
    db.add(wallet)
    db.commit()

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
