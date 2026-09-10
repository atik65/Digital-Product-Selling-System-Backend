from typing import Generic, TypeVar
from pydantic import BaseModel, Field
from typing import Optional

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number (starts at 1)")
    size: int = Field(10, ge=1, description="Number of items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


class PaginationMeta(BaseModel):
    total: int
    current_page: int
    last_page: int
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
    from_item: int = Field(alias="from")
    to_item: int = Field(alias="to")


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    pagination: PaginationMeta
