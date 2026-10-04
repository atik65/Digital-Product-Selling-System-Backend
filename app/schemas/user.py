from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, model_validator
from app.schemas.wallet import WalletResponse
from app.schemas.order import OrderResponse
from app.schemas.topup import TopUpResponse


class UserBase(BaseModel):
    email: EmailStr
    username: str
    name: Optional[str] = None
    image: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    image: Optional[str] = None


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    wallet_balance: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserResponse):
    wallet: Optional[WalletResponse] = None
    orders: List[OrderResponse] = []
    topups: List[TopUpResponse] = []
    total_orders: int = 0
    total_spent: float = 0.0

    @model_validator(mode="after")
    def calculate_totals(self) -> "UserDetailResponse":
        self.total_orders = len(self.orders)
        self.total_spent = round(
            sum(
                o.total_amount
                for o in self.orders
                if o.status in ["PAID", "PROCESSING", "COMPLETED"]
            ),
            2,
        )
        return self


class GoogleLoginRequest(BaseModel):
    id_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    username: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
