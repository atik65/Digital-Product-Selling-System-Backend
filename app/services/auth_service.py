from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRegister, UserLogin
from app.core.exceptions import (
    ConflictException,
    UnauthorizedException,
    ForbiddenException,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings


class AuthService:
    """Service handling user registration, authentication, and token management."""

    def __init__(self):
        self.user_repo = UserRepository()

    def register_user(self, db: Session, user_data: UserRegister):
        # 1. Check for duplicate email
        if self.user_repo.get_by_email(db, user_data.email):
            raise ConflictException(
                f"A user with email '{user_data.email}' already exists."
            )

        # 2. Check for duplicate username
        if self.user_repo.get_by_username(db, user_data.username):
            raise ConflictException(
                f"Username '{user_data.username}' is already taken."
            )

        # 3. Hash the plain password using bcrypt
        hashed = hash_password(user_data.password)

        # 4. Prepare data dictionary for database insertion
        user_dict = {
            "email": user_data.email,
            "username": user_data.username,
            "hashed_password": hashed,
            "role": user_data.role.lower(),
            "is_active": True,
        }

        return self.user_repo.create(db, user_dict)

    def authenticate_user(self, db: Session, login_data: UserLogin) -> dict:
        # 1. Fetch user by email or username
        user = self.user_repo.get_by_email_or_username(db, login_data.email_or_username)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException(
                "Invalid credentials: incorrect username/email or password."
            )

        # 2. Check active status
        if not user.is_active:
            raise ForbiddenException("Account is deactivated. Please contact support.")

        # 3. Generate dual JWT tokens
        access_token = create_access_token(user_id=user.id, role=user.role)
        refresh_token = create_refresh_token(user_id=user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        }

    def refresh_access_token(self, db: Session, refresh_token: str) -> dict:
        # 1. Validate and decode the refresh token
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = int(payload.get("sub"))

        # 2. Fetch and check user status
        user = self.user_repo.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User no longer exists or is inactive.")

        # 3. Issue a fresh access token
        new_access_token = create_access_token(user_id=user.id, role=user.role)

        return {
            "access_token": new_access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        }
