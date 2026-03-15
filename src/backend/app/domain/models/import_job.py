
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.common.enums import DuplicateStrategy, EntityType, ImportJobStatus, RowStatus

if TYPE_CHECKING:
    from datetime import datetime


class RowValidationError(BaseModel):
    row: int
    field: str
    message: str


class PreviewRow(BaseModel):
    row_number: int
    data: dict
    status: RowStatus = RowStatus.VALID
    errors: list[RowValidationError] = Field(default_factory=list)
    duplicate_key: str | None = None


class ImportResult(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[RowValidationError] = Field(default_factory=list)


class ImportJob(BaseModel):
    key: str | None = Field(default=None, alias="_key")
    tenant_key: str = ""
    entity_type: EntityType
    status: ImportJobStatus = ImportJobStatus.UPLOADED
    filename: str = ""
    row_count: int = 0
    duplicate_strategy: DuplicateStrategy = DuplicateStrategy.SKIP
    preview_rows: list[PreviewRow] = Field(default_factory=list)
    result: ImportResult | None = None
    error_message: str | None = None
    uploaded_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}
