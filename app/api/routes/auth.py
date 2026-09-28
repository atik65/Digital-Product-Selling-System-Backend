from typing import Optional
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.limiter import limiter
from app.core.security import get_current_user, set_auth_cookies, clear_auth_cookies
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    TokenResponse,
    LoginRequest,
    GoogleLoginRequest,
    AdminLoginRequest,
    RefreshTokenRequest,
    SignupRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post(
    "/signup",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit("10/minute")
def signup(
    request: Request,
    response: Response,
    body: SignupRequest,
    db: Session = Depends(get_db),
):
    result = auth_service.signup(db, body)
    set_auth_cookies(
        response,
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "User registered successfully",
        "data": result,
    }


@router.post(
    "/google",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Login or register customer with Google OAuth2",
)
@limiter.limit("15/minute")
def google_login(
    request: Request,
    response: Response,
    body: GoogleLoginRequest,
    db: Session = Depends(get_db),
):
    result = auth_service.login_with_google(db, body)
    set_auth_cookies(
        response,
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Google authentication successful",
        "data": result,
    }


@router.post(
    "/login",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="User credential login",
)
@limiter.limit("15/minute")
def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    result = auth_service.login(db, body)
    set_auth_cookies(
        response,
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Authentication successful",
        "data": result,
    }


@router.post(
    "/admin/login",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Admin credential login",
)
@limiter.limit("10/minute")
def admin_login(
    request: Request,
    response: Response,
    body: AdminLoginRequest,
    db: Session = Depends(get_db),
):
    result = auth_service.admin_login(db, body)
    set_auth_cookies(
        response,
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
    )
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Admin authentication successful",
        "data": result,
    }


@router.post(
    "/refresh",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
@limiter.limit("20/minute")
def refresh_token(
    request: Request,
    response: Response,
    body: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db),
):
    # Accept refresh token from either request body or HttpOnly cookie
    refresh_token_val = None
    if body and body.refresh_token:
        refresh_token_val = body.refresh_token
    elif request.cookies.get("refresh_token"):
        refresh_token_val = request.cookies.get("refresh_token")

    if not refresh_token_val:
        clear_auth_cookies(response)
        raise UnauthorizedException("Refresh token was not provided.")

    try:
        tokens = auth_service.refresh_token(db, refresh_token_val)
        set_auth_cookies(response, access_token=tokens["access_token"])
        return {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Token refreshed successfully",
            "data": tokens,
        }
    except Exception:
        clear_auth_cookies(response)
        raise


@router.post(
    "/logout",
    response_model=StandardResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="User logout and clear auth cookies",
)
def logout(
    response: Response,
):
    clear_auth_cookies(response)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Logged out successfully",
        "data": {},
    }


@router.get(
    "/me",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
)
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = auth_service.get_me(db, current_user)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Profile retrieved successfully",
        "data": profile,
    }


@router.patch(
    "/me",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update customer profile",
)
def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = auth_service.update_me(db, current_user, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Profile updated successfully",
        "data": updated,
    }
