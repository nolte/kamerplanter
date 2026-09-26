"""Request and response schemas for REQ-025 privacy endpoints."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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
    retained_reason: str | None = None


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
