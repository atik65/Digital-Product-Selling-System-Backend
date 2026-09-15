import re
from sqlalchemy.orm import Session
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.core.config import settings
from app.core.exceptions import (
    ValidationException,
    UnauthorizedException,
    ForbiddenException,
)
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.wallet_repository import WalletRepository
from app.schemas.user import (
    UserUpdate,
    AdminLoginRequest,
    GoogleLoginRequest,
    RefreshTokenRequest,
    SignupRequest,
)


class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.wallet_repo = WalletRepository()

    def _ensure_user_wallet(self, db: Session, user_id: int):
        wallet = self.wallet_repo.get_by_user_id(db, user_id)
        if not wallet:
            self.wallet_repo.create_wallet(db, user_id)

    def login_with_google(self, db: Session, req: GoogleLoginRequest) -> dict:
        """Verifies Google ID Token, registers or syncs customer, and issues tokens."""
        try:
            # If GOOGLE_CLIENT_ID is configured, verify against it; otherwise verify signature
            client_id = settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None
            id_info = google_id_token.verify_oauth2_token(
                req.id_token, google_requests.Request(), client_id
            )
        except Exception as e:
            raise UnauthorizedException(f"Invalid Google token: {str(e)}")

        google_id = id_info.get("sub")
        email = id_info.get("email")
        name = id_info.get("name")
        image = id_info.get("picture")

        if not email:
            raise ValidationException("Google account has no associated email address")

        user = self.user_repo.get_by_google_id(db, google_id)
        if not user:
            user = self.user_repo.get_by_email(db, email)
            if user:
                # Link existing email account to google_id
                self.user_repo.update(
                    db,
                    user,
                    {
                        "google_id": google_id,
                        "image": image or user.image,
                        "name": name or user.name,
                    },
                )
            else:
                # Generate unique username from email
                base_username = re.sub(r"[^a-zA-Z0-9]", "", email.split("@")[0]).lower()
                username = base_username
                counter = 1
                while self.user_repo.get_by_username(db, username):
                    username = f"{base_username}{counter}"
                    counter += 1

                user_data = {
                    "google_id": google_id,
                    "email": email,
                    "username": username,
                    "name": name,
                    "image": image,
                    "role": "customer",
                    "is_active": True,
                }
                user = self.user_repo.create(db, user_data)

        if not user.is_active:
            raise ForbiddenException("Account has been suspended")

        self._ensure_user_wallet(db, user.id)

        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    def admin_login(self, db: Session, req: AdminLoginRequest) -> dict:
        """Authenticates administrative staff via email and password."""
        user = self.user_repo.get_by_email(db, req.email)
        if not user or not user.hashed_password:
            raise UnauthorizedException("Invalid email or password")

        if not verify_password(req.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        if user.role != "admin":
            raise ForbiddenException("Access restricted to administrators")

        if not user.is_active:
            raise ForbiddenException("Account has been suspended")

        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }

    def refresh_token(self, db: Session, req: RefreshTokenRequest) -> dict:
        payload = decode_token(req.refresh_token, expected_type="refresh")
        user_id = int(payload.get("sub"))
        user = self.user_repo.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive")

        new_access_token = create_access_token(user.id, user.role)
        return {"access_token": new_access_token, "token_type": "bearer"}

    def get_me(self, db: Session, current_user: User) -> User:
        self._ensure_user_wallet(db, current_user.id)
        return current_user

    def update_me(self, db: Session, current_user: User, data: UserUpdate) -> User:
        return self.user_repo.update(
            db, current_user, data.model_dump(exclude_unset=True)
        )

    def signup(self, db: Session, req: SignupRequest) -> dict:
        """Registers a new user with default role 'user', initializes wallet, and issues tokens."""
        existing_user = self.user_repo.get_by_email(db, req.email)
        if existing_user:
            raise ValidationException("Email is already registered")

        if req.username:
            if self.user_repo.get_by_username(db, req.username):
                raise ValidationException("Username is already taken")
            username = req.username
        else:
            base_username = re.sub(r"[^a-zA-Z0-9]", "", req.email.split("@")[0]).lower()
            if not base_username:
                base_username = "user"
            username = base_username
            counter = 1
            while self.user_repo.get_by_username(db, username):
                username = f"{base_username}{counter}"
                counter += 1

        hashed = hash_password(req.password)
        user = self.user_repo.create_user(
            db=db,
            email=req.email,
            hashed_password=hashed,
            username=username,
            role="user",
            name=req.name,
        )

        self._ensure_user_wallet(db, user.id)

        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user,
        }
