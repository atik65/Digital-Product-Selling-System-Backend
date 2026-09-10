from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    status_code: int = 200
    message: str = "Operation successful"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    success: bool = False
    status_code: int = 400
    message: str
    errors: Optional[Any] = None
    request_id: Optional[str] = None
