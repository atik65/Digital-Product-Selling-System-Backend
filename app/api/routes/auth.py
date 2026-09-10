from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.limiter import limiter
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.response import StandardResponse
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post(
    "/register",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit("5/minute")
def register(
    request: Request,
    response: Response,
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    created_user = auth_service.register_user(db, user_data)
    return {
        "success": True,
        "status_code": status.HTTP_201_CREATED,
        "message": "User registered successfully",
        "data": created_user,
    }


@router.post(
    "/login",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and receive JWT access & refresh tokens",
)
@limiter.limit("10/minute")
def login(
    request: Request,
    response: Response,
    credentials: UserLogin,
    db: Session = Depends(get_db),
):
    tokens = auth_service.authenticate_user(db, credentials)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Login successful",
        "data": tokens,
    }


@router.post(
    "/refresh",
    response_model=StandardResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Obtain a new access token using a valid refresh token",
)
def refresh_token(
    payload: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    new_tokens = auth_service.refresh_access_token(db, payload.refresh_token)
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Access token refreshed successfully",
        "data": new_tokens,
    }


@router.get(
    "/me",
    response_model=StandardResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get profile details of the currently authenticated user",
)
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "status_code": status.HTTP_200_OK,
        "message": "Current user profile retrieved successfully",
        "data": current_user,
    }
