"""Request and response schemas for REQ-025 privacy endpoints."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.models.privacy import ErasureRequest
from app.domain.services.step_up_service import StepUpConfirmation

# ── Data export (Art. 15 / 20) ─────────────────────────────────────


class DataExportResponse(BaseModel):
    key: str
    status: Literal["pending", "processing", "completed", "expired", "failed"]
    requested_at: datetime | None
    completed_at: datetime | None = None
    expires_at: datetime | None = None
    file_size_bytes: int | None = None
    download_count: int = 0
    #: #1645 - why a ``failed`` run did not deliver. Without it the requester
    #: sees a status name and no way to learn what happened to a statutory
    #: request, which is the failure mode that made the scaffold invisible.
    error_message: str | None = None


# ── Email change (Art. 16) ─────────────────────────────────────────


class EmailChangeCreateRequest(BaseModel):
    """An e-mail change and its step-up (#1841, REQ-025 Art. 16).

    Both step-up fields are optional in the schema; the step-up verifier decides
    which one the account needs — ``password`` for an account with a local
    password, ``step_up_code`` for one without (401 ``STEP_UP_CODE_REQUIRED``).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"new_email": "erika.neu@example.org", "password": "<your current password>"},
                {"new_email": "erika.neu@example.org", "step_up_code": "48213907"},
            ]
        }
    )

    new_email: EmailStr
    password: str | None = Field(
        default=None,
        max_length=1024,
        description="The current password. Required when the account has a local password.",
    )
    step_up_code: str | None = Field(
        default=None,
        max_length=32,
        description=(
            "The one-time code mailed by POST /users/me/step-up-code. Required when the account has no local "
            "password (federated sign-in only)."
        ),
    )
    step_up_token: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "The one-time token of a fresh sign-in at the account's identity provider, from the fragment of "
            "/auth/step-up/callback after POST /users/me/step-up/oidc (#1815). Required instead of step_up_code "
            "when the account has no local password but a provider that can re-authenticate "
            "(401 STEP_UP_REAUTH_REQUIRED without it); valid five minutes, for one act, once."
        ),
    )


class EmailChangeConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=200)


class EmailChangeRevertRequest(BaseModel):
    """The one-time token from the notice to the previous address (#1848)."""

    token: str = Field(min_length=1, max_length=200)


class EmailChangeResponse(BaseModel):
    key: str
    new_email: str
    status: Literal["pending", "confirmed", "expired", "cancelled"]
    requested_at: datetime | None
    expires_at: datetime
    confirmed_at: datetime | None = None


# ── Erasure (Art. 17) ──────────────────────────────────────────────


class ErasureCreateRequest(BaseModel):
    """The step-up an account erasure carries (#1813, #1814, REQ-025 Art. 17).

    Taken by the three routes that erase an account — ``POST /privacy/erasure``,
    ``DELETE /users/me`` (the account's own) and ``DELETE /admin/platform/users/{key}``
    (a platform admin erasing another account). ``confirm_email`` is the e-mail of
    the account being erased, typed back; ``password`` is the *requester's* current
    password, required when the requester's account has one; ``step_up_code`` the
    one-time code mailed to a requester without one (#1815).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"confirm_email": "erika.gruen@example.org", "password": "<your current password>"},
                {"confirm_email": "erika.gruen@example.org", "step_up_code": "48213907"},
            ]
        },
    )

    confirm_email: str = Field(
        min_length=1,
        max_length=320,
        description="The e-mail address of the account being erased, typed back to confirm which account it is.",
    )
    password: str | None = Field(
        default=None,
        max_length=1024,
        description=(
            "The requester's current password. Required when the requester's account has a local password; "
            "an account that signs in only through a federated provider omits it and sends step_up_code."
        ),
    )
    step_up_code: str | None = Field(
        default=None,
        max_length=32,
        description=(
            "The one-time code mailed by POST /users/me/step-up-code. Required when the requester's account has "
            "no local password (federated sign-in only); 401 STEP_UP_CODE_REQUIRED without it (#1815)."
        ),
    )
    step_up_token: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "The one-time token of a fresh sign-in at the account's identity provider, from the fragment of "
            "/auth/step-up/callback after POST /users/me/step-up/oidc (#1815). Required instead of step_up_code "
            "when the account has no local password but a provider that can re-authenticate "
            "(401 STEP_UP_REAUTH_REQUIRED without it); valid five minutes, for one act, once."
        ),
    )

    def to_confirmation(self) -> StepUpConfirmation:
        return StepUpConfirmation(
            echo=self.confirm_email, password=self.password, code=self.step_up_code, reauth_token=self.step_up_token
        )


class ErasureResponse(BaseModel):
    key: str
    status: Literal["scheduled", "in_progress", "completed", "partially_completed"]
    requested_at: datetime | None
    soft_deleted_at: datetime | None
    hard_delete_scheduled_at: datetime | None
    completed_at: datetime | None = None
    anonymized_collections: list[str] = Field(default_factory=list)
    deleted_collections: list[str] = Field(default_factory=list)
    #: The third AK-08a category (#1800): retained under its own,
    #: account-independent period rather than deleted or anonymised outright
    #: (consent_records, R-04). Dropped here would repeat, one layer further
    #: out, the exact "confirmation silently drops a category" defect #1800
    #: fixed on the domain model (``ErasureRequest.pseudonymized_collections``).
    pseudonymized_collections: list[str] = Field(default_factory=list)
    retained_reason: str | None = None

    @classmethod
    def from_request(cls, erasure: ErasureRequest) -> ErasureResponse:
        """The response for one stored request — shared by ``/privacy`` and the admin status read (#1949)."""
        return cls(
            key=erasure.key or "",
            status=erasure.status,
            requested_at=erasure.requested_at,
            soft_deleted_at=erasure.soft_deleted_at,
            hard_delete_scheduled_at=erasure.hard_delete_scheduled_at,
            completed_at=erasure.completed_at,
            anonymized_collections=list(erasure.anonymized_collections),
            deleted_collections=list(erasure.deleted_collections),
            pseudonymized_collections=list(erasure.pseudonymized_collections),
            retained_reason=erasure.retained_reason,
        )


class AccountDeletionAcceptedResponse(BaseModel):
    """The ``202 Accepted`` body of the platform-admin account deletion (#1949, REQ-025 AK-PT-01).

    The erasure is *recorded*, the account *closed* (deactivated, sessions revoked)
    and the other members of its personal gardens *told*; the erasure itself runs
    afterwards in a Celery task. The body says so — it is never "deleted". Poll
    ``GET /admin/platform/erasures/{erasure_key}`` for the outcome: ``completed``,
    or ``partially_completed`` for a run that left a declared step open and that
    the daily beat retries. Names no account and no address.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "erasure_key": "9f2c0e6a4b1d",
                    "status": "scheduled",
                    "requested_at": "2026-10-02T10:00:00Z",
                    "message": "Account deletion accepted: the account is closed and its data is being erased.",
                }
            ]
        }
    )

    erasure_key: str
    status: Literal["scheduled", "in_progress", "completed", "partially_completed"]
    requested_at: datetime | None = None
    message: str = "Account deletion accepted: the account is closed and its data is being erased."


class PersonalTenantErasurePreviewItem(BaseModel):
    """One personal tenant an account erasure takes with it (AK-FK-06)."""

    #: The subject's own tenant name — never another member's.
    name: str
    #: How many *other* active members lose the tenant; a count, never who.
    other_member_count: int = Field(ge=0)

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Ada's garden", "other_member_count": 2}]})


class ErasurePreviewResponse(BaseModel):
    """What confirming the erasure would delete beyond the account itself (REQ-025 AK-FK-06, #1824)."""

    personal_tenants: list[PersonalTenantErasurePreviewItem] = Field(default_factory=list)

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"personal_tenants": [{"name": "Ada's garden", "other_member_count": 2}]}]}
    )


# ── Restriction (Art. 18) ──────────────────────────────────────────


class RestrictionCreateRequest(BaseModel):
    scope: str = Field(min_length=1, max_length=100)
    reason: Literal[
        "accuracy_contested",
        "unlawful_processing",
        "purpose_expired",
        "objection_pending",
    ]
    notes: str | None = Field(default=None, max_length=2000)


class RestrictionResponse(BaseModel):
    key: str
    scope: str
    reason: str
    notes: str | None
    created_at: datetime | None
    lifted_at: datetime | None = None


# ── Objection (Art. 21) ────────────────────────────────────────────


class ObjectionRequest(BaseModel):
    purpose: str = Field(min_length=1, max_length=100)
    reason: str = Field(min_length=1, max_length=2000)


# ── Consent ────────────────────────────────────────────────────────


class ConsentGrantRequest(BaseModel):
    purpose: str = Field(min_length=1, max_length=100)


class ConsentResponse(BaseModel):
    purpose: str
    label: str
    description: str
    legal_basis: str
    required: bool
    granted: bool
    granted_at: datetime | None = None
    revoked_at: datetime | None = None


# ── Privacy policy ─────────────────────────────────────────────────


class ConsentPurposeInfoResponse(BaseModel):
    key: str
    label_de: str
    label_en: str
    description_de: str
    description_en: str
    legal_basis: str
    required: bool


class RetentionCategoryInfoResponse(BaseModel):
    category: str
    description: str
    retention_period: str
    rule_id: str
    latest_deletion_point: str
    enforcement_status: Literal["enforced", "partial", "not_implemented"]
    exception_note: str | None = None


class DataControllerInfoResponse(BaseModel):
    name: str
    contact_email: str
    address: str | None = None


class RightInfoResponse(BaseModel):
    article: str
    title: str
    description: str


class PrivacyPolicyResponse(BaseModel):
    version: str
    effective_date: date
    purposes: list[ConsentPurposeInfoResponse]
    retention_summary: list[RetentionCategoryInfoResponse]
    data_controller: DataControllerInfoResponse
    rights_summary: list[RightInfoResponse]


class MessageResponse(BaseModel):
    message: str
