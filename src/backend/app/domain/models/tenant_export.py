"""Domain models of the tenant export and import (REQ-056 §8, §13.3, §13.5, #2138).

A tenant export is an archive of every row a tenant owns — the collections of the
tenant-erasure inventory minus declared exclusions, the edges between them (or onto a
global catalogue row), and the memberships as ``members.jsonl`` without any e-mail
address. An import always founds a **new** tenant and gives every document a new
key: ``_key`` is global per collection, so an archive cannot be written back into a
shared database without a key-mapping table (§8.4).

The request records live in ``tenant_export_requests`` (tenant-scoped, part of the
tenant-erasure inventory) and ``tenant_import_requests`` (global: the target tenant
only comes into being during the run).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.common.enums import AdminScope, TenantRole

#: Who asked for the export (REQ-056 §8.2).
type TenantExportOrigin = Literal["tenant_management", "platform_admin"]

#: ``pending`` (recorded, task dispatched) → ``running`` (a worker claimed it) →
#: ``completed`` (archive stored) / ``failed`` (``failure_reason``) → ``expired``
#: (the archive is gone after NFR-011 R-05).
type TenantExportStatus = Literal["pending", "running", "completed", "failed", "expired"]

#: ``validating`` (checksums, format, catalogue references) → ``running`` (the new tenant's key is
#: recorded, the tenant exists and documents are being written) → ``completed`` / ``failed``.
#: ``cleanup_pending``: the run failed and its rollback could not remove everything; the tenant is
#: still ``importing`` (unreachable) and ``target_tenant_key`` names it until the hourly sweep has
#: erased it through the tenant-erasure inventory, then the request ends ``failed`` (SEC-R2-03).
type TenantImportStatus = Literal["pending", "validating", "running", "completed", "failed", "cleanup_pending"]

#: The only failure reasons a requester reads on the record (never an exception text).
type TenantExportFailureReason = Literal["too_large", "tenant_not_exportable", "storage_unavailable", "internal_error"]


class TenantExportRequest(BaseModel):
    """One requested tenant export (REQ-056 §13.3)."""

    key: str | None = Field(default=None, alias="_key")
    tenant_key: str
    requested_by_user_key: str
    origin: TenantExportOrigin
    status: TenantExportStatus = "pending"
    failure_reason: TenantExportFailureReason | None = None
    #: The archive's object-storage key (``t/<tenant>/tenant_export/<export_key>.zip``). The spec
    #: draft named an attachment key; the archive has no attachment record (it must not count
    #: against the storage quota, nor be exported itself), so the request holds the object key.
    storage_key: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    #: Rows per archive part (``collections/<name>.jsonl``, ``edges/<name>.jsonl``, ``members.jsonl``).
    counts: dict[str, int] = Field(default_factory=dict)
    requested_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    #: ``completed_at`` + NFR-011 R-05 (``RETENTION_EXPORT_FILE_RETENTION_HOURS``).
    expires_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TenantImportMemberGrant(BaseModel):
    """What the importing admin confirmed for one archive member (SEC-003 of the PR #2267 review).

    The role and scopes are the admin's, never ``members.jsonl``'s: an archive is a file
    someone handed over, and a role written into it must not become a grant by itself.
    """

    account_key: str
    role: TenantRole
    admin_scopes: list[AdminScope] = Field(default_factory=list)


class TenantImportRequest(BaseModel):
    """One import of a tenant archive by a platform admin (REQ-056 §13.5)."""

    key: str | None = Field(default=None, alias="_key")
    requested_by_user_key: str
    status: TenantImportStatus = "pending"
    source_format: str
    #: The uploaded archive until the run ends (deleted on completion and on failure).
    upload_storage_key: str | None = None
    #: ``member_mapping`` resolved at request time: archive user key → account and confirmed role.
    member_grants: dict[str, TenantImportMemberGrant] = Field(default_factory=dict)
    #: The archive carried this installation's valid signature (SEC-003); ``False`` = unverified.
    verified: bool = False
    plan_key: str | None = None
    #: The uploaded archive's SHA-256 (hex): the audit names the archive by it (I9).
    archive_sha256: str | None = None
    target_tenant_key: str | None = None
    #: Rows written per collection; no contents.
    report: dict[str, int] = Field(default_factory=dict)
    #: A code (``IMPORT_*``), never an exception text.
    failure_reason: str | None = None
    missing_catalog_entries: list[str] = Field(default_factory=list)
    requested_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"populate_by_name": True}


class TenantArchiveMember(BaseModel):
    """One line of ``members.jsonl`` — no e-mail address, no account document (REQ-056 E-09)."""

    user_key: str
    display_name: str | None = None
    role: str
    admin_scopes: list[str] = Field(default_factory=list)
    is_active: bool = True
    joined_at: str | None = None


class TenantArchive(BaseModel):
    """A verified, parsed archive (checksums and format checked before this exists).

    ``collections`` and ``edges`` hold the documents as stored in the source — with
    their *source* keys; nothing of it may reach a database before the key mapping
    rewrote it (:class:`~app.domain.engines.tenant_import_engine.TenantImportEngine`).
    """

    format: str
    source_tenant_key: str
    source_migration: str | None = None
    tenant: dict[str, object]
    collections: dict[str, list[dict[str, object]]] = Field(default_factory=dict)
    edges: dict[str, list[dict[str, object]]] = Field(default_factory=dict)
    members: list[TenantArchiveMember] = Field(default_factory=list)
    objects: dict[str, bytes] = Field(default_factory=dict)
    #: The manifest carries this installation's signature and it matches (SEC-003). ``False`` for an
    #: archive another installation wrote, an unsigned one, or one changed after it was signed: its
    #: content is then only as trustworthy as the person who handed it over.
    verified: bool = False
    #: Optional parts this reader lists but does not read (``timeseries/readings.csv``, #2138), with
    #: the row count the manifest states — reported, never imported.
    ignored_parts: dict[str, int] = Field(default_factory=dict)


class TenantImportOutcome(BaseModel):
    """What one import run wrote (returned to the caller; only ``report`` is persisted)."""

    tenant_key: str
    report: dict[str, int] = Field(default_factory=dict)
    #: ``collection -> {source key: new key}``. Held in memory only, for the caller (and the
    #: roundtrip test); never stored — it would map the source installation's keys.
    key_mapping: dict[str, dict[str, str]] = Field(default_factory=dict)
    nulled_references: int = 0
