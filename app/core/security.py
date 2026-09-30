from datetime import datetime, timedelta, timezone
from typing import Optional, List, Union
import bcrypt
import jwt
from fastapi import Depends, Request, Response
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
# 3. HTTP Cookie Management
# ==========================================


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: Optional[str] = None,
) -> None:
    """
    Sets HTTP-Only authentication cookies (access_token, refresh_token)
    and a client-readable status cookie (signedIn=true) on the HTTP Response.
    """
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    now = datetime.now(timezone.utc)
    access_expires = now + timedelta(seconds=access_max_age)
    refresh_expires = now + timedelta(seconds=refresh_max_age)

    # 1. HttpOnly access_token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=access_max_age,
        expires=access_expires,
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
    )

    # 2. HttpOnly refresh_token cookie (if provided)
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=refresh_max_age,
            expires=refresh_expires,
            path="/",
            domain=settings.COOKIE_DOMAIN,
            secure=settings.COOKIE_SECURE,
            httponly=True,
            samesite=settings.COOKIE_SAMESITE,
        )

    # 3. Client-accessible signedIn indicator cookie
    response.set_cookie(
        key="signedIn",
        value="true",
        max_age=refresh_max_age,
        expires=refresh_expires,
        path="/",
        domain=settings.COOKIE_DOMAIN,
        secure=settings.COOKIE_SECURE,
        httponly=False,
        samesite=settings.COOKIE_SAMESITE,
    )


def clear_auth_cookies(response: Response) -> None:
    """
    Deletes all authentication cookies from the client browser.
    """
    for key in ("access_token", "refresh_token", "signedIn"):
        response.delete_cookie(
            key=key,
            path="/",
            domain=settings.COOKIE_DOMAIN,
            secure=settings.COOKIE_SECURE,
            httponly=True if key != "signedIn" else False,
            samesite=settings.COOKIE_SAMESITE,
        )


# ==========================================
# 4. Authentication & RBAC Dependencies
# ==========================================


def get_current_user(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that extracts the Bearer token from Authorization header OR
    HttpOnly access_token cookie, validates it, and returns the current active User model instance.
    """
    candidates = []
    if auth and auth.credentials:
        candidates.append(auth.credentials)
    if request and request.cookies.get("access_token"):
        cookie_tok = request.cookies.get("access_token")
        if cookie_tok not in candidates:
            candidates.append(cookie_tok)

    if not candidates:
        raise UnauthorizedException("Authentication credentials were not provided.")

    last_error = None
    for token in candidates:
        try:
            payload = decode_token(token, expected_type="access")
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
        except UnauthorizedException as e:
            last_error = e
            continue

    raise last_error or UnauthorizedException("Authentication credentials were not provided.")


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
