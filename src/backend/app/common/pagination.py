from pydantic import BaseModel, Field


class PaginatedRequest(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    offset: int
    limit: int
