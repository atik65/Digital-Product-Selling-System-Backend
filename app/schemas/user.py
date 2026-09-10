from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr = Field(description="User's email address")
    username: str = Field(min_length=3, max_length=50, description="Unique username")


class UserRegister(UserBase):
    password: str = Field(
        min_length=6, max_length=100, description="User password (min 6 characters)"
    )
    role: str = Field(default="user", description="User role (e.g. 'user' or 'admin')")


class UserLogin(BaseModel):
    email_or_username: str = Field(description="Email address or username")
    password: str = Field(description="User password")


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(description="Valid refresh token")
