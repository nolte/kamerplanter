"""Request and response schemas of the tenant export and import (REQ-056 §8, §14, #2138)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.api.v1.auth.schemas import CredentialStepUp
from app.domain.models.tenant_export import (
    TenantExportFailureReason,
    TenantExportOrigin,
    TenantExportRequest,
    TenantExportStatus,
    TenantImportRequest,
    TenantImportStatus,
)
from app.domain.services.tenant_export_service import StepUpFactors


class TenantExportCreateRequest(CredentialStepUp):
    """The requester's own step-up (``tenant_export``, bound to the tenant's key, REQ-056 §12.1)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"examples": [{"current_password": "<your current password>"}]},
    )

    def to_factors(self) -> StepUpFactors:
        return StepUpFactors(password=self.current_password, code=self.step_up_code, reauth_token=self.step_up_token)


class TenantExportResponse(BaseModel):
    """One export request; the archive itself is read through the download route."""

    key: str
    status: TenantExportStatus
    origin: TenantExportOrigin
    failure_reason: TenantExportFailureReason | None = None
    size_bytes: int | None = None
    counts: dict[str, int] = {}
    requested_at: datetime
    completed_at: datetime | None = None
    expires_at: datetime | None = None

    @classmethod
    def from_request(cls, request: TenantExportRequest) -> TenantExportResponse:
        return cls(
            key=request.key or "",
            status=request.status,
            origin=request.origin,
            failure_reason=request.failure_reason,
            size_bytes=request.size_bytes,
            counts=request.counts,
            requested_at=request.requested_at,
            completed_at=request.completed_at,
            expires_at=request.expires_at,
        )


class TenantImportResponse(BaseModel):
    """The import request and, once it ran, its report (counts only, no contents — REQ-056 §13.5)."""

    key: str
    status: TenantImportStatus
    source_format: str
    target_tenant_key: str | None = None
    plan_key: str | None = None
    report: dict[str, int] = {}
    failure_reason: str | None = None
    missing_catalog_entries: list[str] = []
    requested_at: datetime
    completed_at: datetime | None = None

    @classmethod
    def from_request(cls, request: TenantImportRequest) -> TenantImportResponse:
        return cls(
            key=request.key or "",
            status=request.status,
            source_format=request.source_format,
            target_tenant_key=request.target_tenant_key,
            plan_key=request.plan_key,
            report=request.report,
            failure_reason=request.failure_reason,
            missing_catalog_entries=request.missing_catalog_entries,
            requested_at=request.requested_at,
            completed_at=request.completed_at,
        )
