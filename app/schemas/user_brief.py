from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserBriefResponse(BaseModel):
    id: int
    email: str
    username: str
    name: Optional[str] = None
    phone: Optional[str] = None
    image: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    wallet_balance: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
