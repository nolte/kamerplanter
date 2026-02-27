from datetime import datetime

from pydantic import BaseModel, Field


class RowValidationErrorSchema(BaseModel):
    row: int
    field: str
    message: str


class PreviewRowSchema(BaseModel):
    row_number: int
    data: dict
    status: str
    errors: list[RowValidationErrorSchema] = Field(default_factory=list)
    duplicate_key: str | None = None


class ImportResultSchema(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[RowValidationErrorSchema] = Field(default_factory=list)


class ImportJobResponse(BaseModel):
    key: str
    entity_type: str
    status: str
    filename: str
    row_count: int
    duplicate_strategy: str
    preview_rows: list[PreviewRowSchema] = Field(default_factory=list)
    result: ImportResultSchema | None = None
    error_message: str | None = None
    uploaded_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
