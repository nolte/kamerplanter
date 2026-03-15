from datetime import datetime

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str | None = None
    reason: str
    code: str


class ErrorResponse(BaseModel):
    error_id: str = Field(description="Unique tracking ID (format: err_<uuid4>)")
    error_code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error description")
    details: list[ErrorDetail] = Field(default_factory=list)
    timestamp: datetime
    path: str
    method: str
