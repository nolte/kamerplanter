"""Request and response schemas for REQ-025 privacy endpoints."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# ── Data export (Art. 15 / 20) ─────────────────────────────────────


class DataExportResponse(BaseModel):
    key: str
    status: Literal["pending", "processing", "completed", "expired", "failed"]
    requested_at: datetime | None
    completed_at: datetime | None = None
    expires_at: datetime | None = None
    file_size_bytes: int | None = None
    download_count: int = 0


# ── Email change (Art. 16) ─────────────────────────────────────────


class EmailChangeCreateRequest(BaseModel):
    new_email: EmailStr


class EmailChangeConfirmRequest(BaseModel):
    token: str = Field(min_length=1, max_length=200)


class EmailChangeResponse(BaseModel):
    key: str
    new_email: str
    status: Literal["pending", "confirmed", "expired"]
    requested_at: datetime | None
    expires_at: datetime
    confirmed_at: datetime | None = None


# ── Erasure (Art. 17) ──────────────────────────────────────────────


class ErasureCreateRequest(BaseModel):
    password: str | None = None


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
