"""FastAPI router for REQ-025 privacy & data subject rights endpoints."""

from fastapi import APIRouter, Depends, Request

from app.api.v1.privacy.schemas import (
    ConsentGrantRequest,
    ConsentPurposeInfoResponse,
    ConsentResponse,
    DataControllerInfoResponse,
    DataExportResponse,
    EmailChangeConfirmRequest,
    EmailChangeCreateRequest,
    EmailChangeResponse,
    ErasureCreateRequest,
    ErasureResponse,
    MessageResponse,
    ObjectionRequest,
    PrivacyPolicyResponse,
    RestrictionCreateRequest,
    RestrictionResponse,
    RetentionCategoryInfoResponse,
    RightInfoResponse,
)
from app.common.auth import get_current_user
from app.common.dependencies import get_privacy_service
from app.domain.models.privacy import (
    ConsentRecord,
    DataExportRequest,
    EmailChangeRequest,
    ErasureRequest,
    ProcessingRestriction,
)
from app.domain.models.user import User
from app.domain.services.privacy_service import PrivacyService

router = APIRouter(prefix="/privacy", tags=["privacy"])


# ── Helpers ────────────────────────────────────────────────────────


def _to_export_response(export: DataExportRequest) -> DataExportResponse:
    return DataExportResponse(
        key=export.key or "",
        status=export.status,
        requested_at=export.requested_at,
        completed_at=export.completed_at,
        expires_at=export.expires_at,
        file_size_bytes=export.file_size_bytes,
        download_count=export.download_count,
    )


def _to_email_change_response(change: EmailChangeRequest) -> EmailChangeResponse:
    return EmailChangeResponse(
        key=change.key or "",
        new_email=str(change.new_email),
        status=change.status,
        requested_at=change.requested_at,
        expires_at=change.expires_at,
        confirmed_at=change.confirmed_at,
    )


def _to_erasure_response(erasure: ErasureRequest) -> ErasureResponse:
    return ErasureResponse(
        key=erasure.key or "",
        status=erasure.status,
        requested_at=erasure.requested_at,
        soft_deleted_at=erasure.soft_deleted_at,
        hard_delete_scheduled_at=erasure.hard_delete_scheduled_at,
        completed_at=erasure.completed_at,
        anonymized_collections=list(erasure.anonymized_collections),
        deleted_collections=list(erasure.deleted_collections),
        retained_reason=erasure.retained_reason,
    )


def _to_restriction_response(
    restriction: ProcessingRestriction,
) -> RestrictionResponse:
    return RestrictionResponse(
        key=restriction.key or "",
        scope=restriction.scope,
        reason=restriction.reason,
        notes=restriction.notes,
        created_at=restriction.created_at,
        lifted_at=restriction.lifted_at,
    )


def _to_consent_response_from_record(
    record: ConsentRecord,
    label: str,
    description: str,
    legal_basis: str,
    required: bool,
) -> ConsentResponse:
    return ConsentResponse(
        purpose=record.purpose,
        label=label,
        description=description,
        legal_basis=legal_basis,
        required=required,
        granted=record.granted,
        granted_at=record.granted_at,
        revoked_at=record.revoked_at,
    )


# ── Art. 15 / 20: data export ─────────────────────────────────────


@router.post("/export", response_model=DataExportResponse, status_code=201)
def request_data_export(
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Initiate a new data-export job (Art. 15 / 20)."""
    export = service.request_data_export(current_user.key or "")
    return _to_export_response(export)


@router.get("/export/{export_key}", response_model=DataExportResponse)
def get_export_status(
    export_key: str,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Return status of a single export job (ownership-checked)."""
    export = service.get_export_status(current_user.key or "", export_key)
    return _to_export_response(export)


@router.get("/export/{export_key}/download", response_model=DataExportResponse)
def download_export(
    export_key: str,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Mark an export as downloaded and return its metadata.

    Streaming the actual file is delegated to a future Celery/FileResponse
    integration. Returning the metadata is enough to validate the contract
    and record the download.
    """
    export = service.prepare_export_download(current_user.key or "", export_key)
    return _to_export_response(export)


# ── Art. 16: email change ─────────────────────────────────────────


@router.post("/email-change", response_model=EmailChangeResponse, status_code=201)
def request_email_change(
    body: EmailChangeCreateRequest,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Initiate an email-change request (Art. 16)."""
    change = service.request_email_change(current_user.key or "", body.new_email)
    return _to_email_change_response(change)


@router.post("/email-change/confirm", response_model=MessageResponse)
def confirm_email_change(
    body: EmailChangeConfirmRequest,
    service: PrivacyService = Depends(get_privacy_service),
):
    """Confirm an email change via the verification token (no auth required)."""
    service.confirm_email_change(body.token)
    return MessageResponse(message="Email address has been updated.")


# ── Art. 17: erasure ──────────────────────────────────────────────


@router.post("/erasure", response_model=ErasureResponse, status_code=201)
def request_erasure(
    body: ErasureCreateRequest,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Request account erasure (Art. 17)."""
    erasure = service.request_erasure(current_user.key or "", body.password)
    return _to_erasure_response(erasure)


@router.get("/erasure/{erasure_key}", response_model=ErasureResponse)
def get_erasure_status(
    erasure_key: str,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Return status of an erasure request."""
    erasure = service.get_erasure_status(erasure_key)
    return _to_erasure_response(erasure)


# ── Art. 18: processing restriction ───────────────────────────────


@router.post("/restrict", response_model=RestrictionResponse, status_code=201)
def restrict_processing(
    body: RestrictionCreateRequest,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Create a processing-restriction (Art. 18)."""
    restriction = service.restrict_processing(
        current_user.key or "",
        body.scope,
        body.reason,
        body.notes,
    )
    return _to_restriction_response(restriction)


@router.delete("/restrict/{restriction_key}", response_model=RestrictionResponse)
def lift_restriction(
    restriction_key: str,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Lift an existing processing-restriction."""
    restriction = service.lift_restriction(current_user.key or "", restriction_key)
    return _to_restriction_response(restriction)


# ── Art. 21: objection ────────────────────────────────────────────


@router.post("/object", response_model=RestrictionResponse, status_code=201)
def object_to_processing(
    body: ObjectionRequest,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """File an objection (Art. 21) — stored as restriction with objection_pending."""
    restriction = service.object_to_processing(
        current_user.key or "",
        body.purpose,
        body.reason,
    )
    return _to_restriction_response(restriction)


# ── Consent ────────────────────────────────────────────────────────


@router.get("/consents", response_model=list[ConsentResponse])
def list_consents(
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """List all known purposes annotated with current consent state."""
    consents = service.list_consents(current_user.key or "")
    return [
        ConsentResponse(
            purpose=c.purpose,
            label=c.label,
            description=c.description,
            legal_basis=c.legal_basis,
            required=c.required,
            granted=c.granted,
            granted_at=c.granted_at,
            revoked_at=c.revoked_at,
        )
        for c in consents
    ]


@router.post("/consents", response_model=ConsentResponse, status_code=201)
def grant_consent(
    body: ConsentGrantRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Grant consent for a processing purpose."""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    record = service.grant_consent(
        current_user.key or "",
        body.purpose,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    purpose = service._consent_engine.find_purpose(body.purpose)  # noqa: SLF001
    label = purpose.label_en if purpose else body.purpose
    description = purpose.description_en if purpose else ""
    legal_basis = purpose.legal_basis if purpose else ""
    required = purpose.required if purpose else False
    return _to_consent_response_from_record(record, label, description, legal_basis, required)


@router.delete("/consents/{purpose}", response_model=ConsentResponse)
def revoke_consent(
    purpose: str,
    current_user: User = Depends(get_current_user),
    service: PrivacyService = Depends(get_privacy_service),
):
    """Revoke consent for an optional processing purpose."""
    record = service.revoke_consent(current_user.key or "", purpose)
    purpose_def = service._consent_engine.find_purpose(purpose)  # noqa: SLF001
    label = purpose_def.label_en if purpose_def else purpose
    description = purpose_def.description_en if purpose_def else ""
    legal_basis = purpose_def.legal_basis if purpose_def else ""
    required = purpose_def.required if purpose_def else False
    return _to_consent_response_from_record(record, label, description, legal_basis, required)


# ── Privacy policy (public) ───────────────────────────────────────


@router.get("/policy", response_model=PrivacyPolicyResponse)
def get_privacy_policy(
    service: PrivacyService = Depends(get_privacy_service),
):
    """Return the current privacy policy (no auth required)."""
    info = service.get_privacy_policy()
    return PrivacyPolicyResponse(
        version=info.version,
        effective_date=info.effective_date,
        purposes=[
            ConsentPurposeInfoResponse(
                key=p.key,
                label_de=p.label_de,
                label_en=p.label_en,
                description_de=p.description_de,
                description_en=p.description_en,
                legal_basis=p.legal_basis,
                required=p.required,
            )
            for p in info.purposes
        ],
        retention_summary=[RetentionCategoryInfoResponse(**r.model_dump()) for r in info.retention_summary],
        data_controller=DataControllerInfoResponse(**info.data_controller.model_dump()),
        rights_summary=[RightInfoResponse(**r.model_dump()) for r in info.rights_summary],
    )
