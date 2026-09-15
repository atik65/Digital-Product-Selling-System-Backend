from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    TokenResponse,
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
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Google authentication successful",
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
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    tokens = auth_service.refresh_token(db, body)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Token refreshed successfully",
        "data": tokens,
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
