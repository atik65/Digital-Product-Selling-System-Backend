from datetime import datetime, timedelta, timezone
from typing import Optional, List, Union
import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.models.user import User

# Standard HTTP Bearer scheme
security = HTTPBearer(auto_error=False)


# ==========================================
# 1. Password Hashing (Bcrypt)
# ==========================================


def hash_password(plain_password: str) -> str:
    """Hashes a password using bcrypt with automatic salting."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies that a plain password matches a bcrypt hashed password."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


# ==========================================
# 2. JWT Token Management (PyJWT)
# ==========================================


def create_access_token(user_id: int, role: str) -> str:
    """Generates a short-lived access token (default: 30 minutes)."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(user_id: int) -> str:
    """Generates a long-lived refresh token (default: 7 days)."""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str, expected_type: str = "access") -> dict:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedException("Token has expired. Please login again.")
    except jwt.InvalidTokenError:
        raise UnauthorizedException("Invalid authentication token.")

    token_type = payload.get("type")
    if token_type != expected_type:
        raise UnauthorizedException(
            f"Invalid token type. Expected '{expected_type}' token."
        )

    return payload


# ==========================================
# 3. Authentication & RBAC Dependencies
# ==========================================


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that extracts the Bearer token, validates it,
    and returns the current active User model instance.
    """
    if not auth or not auth.credentials:
        raise UnauthorizedException("Authentication credentials were not provided.")

    payload = decode_token(auth.credentials, expected_type="access")
    user_id_str = payload.get("sub")

    if not user_id_str:
        raise UnauthorizedException("Malformed token: missing subject identifier.")

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise UnauthorizedException("Malformed token: invalid subject identifier.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.is_deleted:
        raise UnauthorizedException("User associated with this token no longer exists.")

    if not user.is_active:
        raise ForbiddenException("User account is inactive.")

    return user


def require_role(allowed_roles: Union[str, List[str]]):
    """
    Role-Based Access Control (RBAC) dependency factory.
    Supports both a single role string (e.g. "admin") or a list of roles (e.g. ["admin", "superadmin"]).
    Usage:
        @router.delete('/products/{id}')
        def delete(admin: User = Depends(require_role('admin'))):
            ...
    """
    if isinstance(allowed_roles, str):
        roles_list = [allowed_roles]
    else:
        roles_list = allowed_roles

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles_list:
            roles_str = ", ".join(roles_list)
            raise ForbiddenException(
                f"Access denied: this action requires one of '{roles_str}' roles."
            )
        return current_user

    return role_checker
