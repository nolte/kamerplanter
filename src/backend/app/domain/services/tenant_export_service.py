"""Tenant export and import (REQ-056 §8, #2138, audit MT-042).

**Export** (``POST /tenants/{slug}/exports``, ``POST /admin/platform/tenants/{key}/exports``):
the management of a tenant — the lead role **and** the ``management`` scope, proven from
the stored membership like a tenant deletion — or a platform admin asks; the requester's
own step-up (``tenant_export``, bound to the tenant's key) confirms it; at most one export
runs per tenant (``409 EXPORT_ALREADY_RUNNING``) and at most ``TENANT_EXPORTS_PER_DAY`` are
requested in 24 hours (``429``). The request is recorded and answered ``202``; a Celery task
on the ``bulk`` queue writes the archive (:class:`TenantArchiveWriter`) and stores it under
``t/<tenant>/tenant_export/<export_key>.zip``. Larger than the tenant's effective storage
quota plus 10 % and the run ends ``failed``/``too_large`` without a partial archive. The
archive is downloadable by its requester only, until NFR-011 R-05 (the hourly
``retention.expire_data_exports`` beat removes it with the personal exports).

**Import** (``POST /admin/platform/tenant-imports``): platform admins only, step-up
``tenant_import`` bound to ``archive:<first 32 hex of the upload's SHA-256>`` — checked
before a single byte of the upload is parsed. The upload is then verified (ZIP directory
bounds, format, checksums, the manifest signature, ownership of every row, declared
references, object keys and types, catalogue entries, member mapping) **before** anything
is written — a refusal is ``422`` with the code and the entries — then stored and imported
by a ``bulk`` task into a **new** tenant with new keys for every document
(:class:`TenantImportEngine`). The tenant is founded ``importing`` (it resolves for nobody)
with inactive memberships, and only becomes ``active`` once every row is written. Its key is
recorded on the request *before* the founding, so a run that dies at any point leaves a
request that names its tenant. A failure part-way removes everything the run wrote; when
that removal itself fails, the tenant stays ``importing`` and the request ``cleanup_pending``
with the tenant's key, and the hourly beat erases it through the tenant-erasure inventory —
as it does for a run that died. Every refused or failed import is audited
(``tenant_import_requested`` with the outcome and the archive's SHA-256).

**Trust** (SEC-003 of the PR #2267 review): the per-part SHA-256 in the manifest only detects
corruption — anyone can recompute it. An archive is *verified* when its manifest carries this
installation's HMAC signature; a foreign or unsigned archive is imported as *unverified* (the
request says so). Roles never come from the archive: the admin confirms each mapped member's
role and scopes.

Not part of this slice (REQ-056 AK Stand, #2138): TimescaleDB readings, the quota checks of
the target plan before the write, the per-document validation against the domain models,
and the frontend.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import tempfile
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import IO, Any

import structlog

from app.common.async_bridge import run_async
from app.common.enums import (
    AdminScope,
    EntitlementDimension,
    SecurityAuditAction,
    SecurityAuditVia,
    TenantRole,
    TenantStatus,
)
from app.common.exceptions import (
    ExportAlreadyRunningError,
    ForbiddenError,
    NotFoundError,
    PayloadTooLargeError,
    RateLimitError,
    TenantImportRefusedError,
    ValidationError,
)
from app.common.log_privacy import log_subject, log_tenant
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_export_engine import (
    ARCHIVE_FORMAT,
    ARCHIVE_STORAGE_CATEGORY,
    EDGES_DIR,
    MAX_UNCOMPRESSED_BYTES,
    MEMBERS_NAME,
    TENANT_NAME,
    ArchiveTooLargeError,
    TenantArchiveError,
    TenantArchiveWriter,
    TenantExportEngine,
    archive_document,
    read_tenant_archive,
)
from app.domain.engines.tenant_import_engine import TenantImportEngine, new_document_key
from app.domain.interfaces.email_service import IEmailService
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter
from app.domain.interfaces.tenant_export_store import (
    ITenantDataStore,
    ITenantExportRequestRepository,
    ITenantImportRequestRepository,
)
from app.domain.interfaces.tenant_repository import ITenantRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.membership import Membership
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import TenantErasureEntry
from app.domain.models.tenant_export import (
    TenantArchive,
    TenantExportOrigin,
    TenantExportRequest,
    TenantImportMemberGrant,
    TenantImportOutcome,
    TenantImportRequest,
)
from app.domain.models.user import User, allows_interactive_auth
from app.domain.services.entitlement_service import EntitlementService
from app.domain.services.security_audit_service import SecurityAuditService
from app.domain.services.step_up_service import StepUpVerifier
from app.domain.services.tenant_service import TenantService

logger = structlog.get_logger()

_PLATFORM_TENANT_KEY = "platform"

#: One answer for an unknown slug and a tenant the requester may not export (REQ-056 §12.2).
_REFUSED = "Exporting a tenant requires the lead role and the management scope."

#: States the management may export in (AK-27); a platform admin may in every state but ``deleted``.
_MANAGEMENT_STATES = frozenset({TenantStatus.ACTIVE, TenantStatus.PENDING_DELETION})

#: Rows read per query and written per transaction.
PAGE_SIZE = 500

#: An archive is kept in memory up to this size, then spilled to a temporary file.
_SPOOL_BYTES = 32 * 1024 * 1024

#: The size headroom over the storage quota (REQ-056 §8.3: ``wirksam(storage_mb)`` plus 10 %).
_SIZE_HEADROOM = 1.10

#: A pending or running export untouched this long belongs to a crashed or lost run.
STALE_AFTER = timedelta(hours=6)

#: NFR-011 R-40 — export and import request records are kept this long after they ended.
REQUEST_RETENTION = timedelta(days=30)

#: An uploaded import archive's storage key; outside ``t/`` (no tenant owns it yet).
_IMPORT_UPLOAD_PREFIX = "tenant-imports/"

#: The step-up target of an import: the archive, by its content (SEC-009).
IMPORT_TARGET_PREFIX = "archive:"

#: Hex digits of the upload's SHA-256 the step-up target carries (128 bit).
_IMPORT_TARGET_DIGITS = 32

#: Never stored or served from an import, whatever the target's whitelist says (SEC-010): an SVG
#: is a document that runs script when a browser renders it inline.
_NEVER_IMPORTED_TYPES = frozenset({"image/svg+xml", "text/html", "application/xhtml+xml"})

_IMPORT_ACTIVE_STATES = ("pending", "validating", "running")

_CHUNK = 1024 * 1024


@dataclass
class ImportCleanupPendingError(Exception):
    """An import failed and its rollback could not remove everything (SEC-R2-03 of the PR #2267 review).

    The tenant stays ``importing`` (nobody reaches it) and keeps its key on the request; the
    hourly sweep erases what is left through the tenant-erasure inventory. ``code`` is the
    failure's ``IMPORT_*`` code, never an exception text.
    """

    tenant_key: str
    code: str


@dataclass(frozen=True)
class StepUpFactors:
    """The step-up factors a request carries (password, mailed code, re-authentication token)."""

    password: str | None = None
    code: str | None = None
    reauth_token: str | None = None


class TenantExportService:
    """Requests, runs, serves and expires tenant exports; verifies and runs tenant imports."""

    def __init__(
        self,
        *,
        store: ITenantDataStore,
        export_repo: ITenantExportRequestRepository,
        import_repo: ITenantImportRequestRepository,
        tenant_repo: ITenantRepository,
        membership_repo: IMembershipRepository,
        user_repo: IUserRepository,
        tenant_service: TenantService,
        storage: IObjectStorageAdapter | None,
        step_up_verifier: StepUpVerifier,
        security_audit: SecurityAuditService | None,
        entitlements: EntitlementService,
        email_service: IEmailService | None = None,
        exports_per_day: int = 3,
        export_retention_hours: int = 72,
        import_max_upload_bytes: int = 512 * 1024 * 1024,
        dispatch_export: Callable[[str], None] | None = None,
        dispatch_import: Callable[[str], None] | None = None,
        clock: Callable[[], datetime] | None = None,
        signing_key: bytes | None = None,
        allowed_mime_types: Callable[[str], list[str]] | None = None,
        max_object_bytes: int | None = None,
    ) -> None:
        if exports_per_day < 1:
            raise ValueError("exports_per_day must be at least 1")
        self._store = store
        self._exports = export_repo
        self._imports = import_repo
        self._tenants = tenant_repo
        self._memberships = membership_repo
        self._users = user_repo
        self._tenant_service = tenant_service
        self._storage = storage
        self._step_up = step_up_verifier
        self._audit = security_audit
        self._entitlements = entitlements
        self._email = email_service
        self._exports_per_day = exports_per_day
        self._retention = timedelta(hours=export_retention_hours)
        self._max_upload = import_max_upload_bytes
        self._dispatch_export: Callable[[str], None] | None = dispatch_export
        self._dispatch_import: Callable[[str], None] | None = dispatch_import
        self._clock: Callable[[], datetime] = clock or (lambda: datetime.now(UTC))
        self._signing_key = signing_key or None
        self._allowed_mime_types = allowed_mime_types
        self._max_object_bytes = max_object_bytes

    def _now(self) -> datetime:
        clock = self._clock
        return clock()

    # ── authorization ──────────────────────────────────────────────────

    def _is_platform_admin(self, user_key: str) -> bool:
        membership = self._memberships.get_by_user_and_tenant(user_key, _PLATFORM_TENANT_KEY)
        return bool(membership and membership.is_active and membership.role == TenantRole.LEAD)

    def _may_manage(self, user_key: str, tenant_key: str) -> bool:
        membership = self._memberships.get_by_user_and_tenant(user_key, tenant_key)
        return bool(
            membership
            and membership.is_active
            and MembershipEngine.can_delete_tenant(membership.role, membership.admin_scopes)
        )

    def _require_person(self, requester: User, authenticated_with_api_key: bool) -> None:
        if not allows_interactive_auth(requester) or authenticated_with_api_key:
            raise ForbiddenError("A tenant export or import needs a signed-in person, not an API key.")

    def _resolve_for(
        self, *, requester: User, origin: TenantExportOrigin, slug: str | None = None, tenant_key: str | None = None
    ) -> Tenant:
        """The tenant the requester may export, or the one 403 (unknown slug included, §12.2)."""
        user_key = requester.key or ""
        if origin == "platform_admin":
            if not self._is_platform_admin(user_key):
                raise ForbiddenError("Platform admin role required.")
            tenant = self._tenants.get_by_key(tenant_key or "")
            if tenant is None or tenant.status == TenantStatus.DELETED:
                raise NotFoundError("Tenant", tenant_key or "")
            return tenant
        tenant = self._tenants.get_by_slug(slug or "")
        if tenant is None or not tenant.key or not self._may_manage(user_key, tenant.key):
            raise ForbiddenError(_REFUSED)
        return tenant

    # ── export: request ────────────────────────────────────────────────

    def request_export(
        self,
        *,
        requester: User,
        authenticated_with_api_key: bool,
        origin: TenantExportOrigin,
        factors: StepUpFactors,
        client_ip: str | None,
        slug: str | None = None,
        tenant_key: str | None = None,
    ) -> TenantExportRequest:
        """Record an export and dispatch its run (REQ-056 §8.2, AK-26 … AK-28, AK-36)."""
        self._require_person(requester, authenticated_with_api_key)
        tenant = self._resolve_for(requester=requester, origin=origin, slug=slug, tenant_key=tenant_key)
        key = tenant.key or ""
        if tenant.is_platform:
            raise ForbiddenError("The platform tenant cannot be exported.")
        if origin == "tenant_management" and tenant.status not in _MANAGEMENT_STATES:
            # AK-27 — suspended/orphaned: the management cannot act on the tenant; a platform admin can.
            raise ForbiddenError(_REFUSED)
        self._step_up.verify(
            requester,
            action="tenant_export",
            target=key,
            echo_ok=None,
            password=factors.password,
            code=factors.code,
            reauth_token=factors.reauth_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        now = self._now()
        if self._exports.active_keys(tenant_key=key):
            raise ExportAlreadyRunningError
        if (
            self._exports.count_requested_since(tenant_key=key, since=now - timedelta(hours=24))
            >= self._exports_per_day
        ):
            raise RateLimitError("tenant_export", retry_after=3600)
        created = self._exports.create(
            TenantExportRequest(
                tenant_key=key,
                requested_by_user_key=requester.key or "",
                origin=origin,
                status="pending",
                requested_at=now,
                updated_at=now,
            )
        )
        # Counted again after the insert: of two concurrent requests only the oldest stays.
        active = self._exports.active_keys(tenant_key=key)
        if active and active[0] != created.key:
            self._exports.delete(created.key or "")
            raise ExportAlreadyRunningError
        if self._audit is not None:
            self._audit.record_tenant_change(
                action=SecurityAuditAction.TENANT_EXPORT_REQUESTED,
                via=SecurityAuditVia.PLATFORM_ADMIN if origin == "platform_admin" else SecurityAuditVia.TENANT_ADMIN,
                actor_user_key=requester.key or "",
                tenant_key=key,
            )
        logger.info(
            "tenant_export.requested", tenant=log_tenant(key), origin=origin, subject=log_subject(requester.key)
        )
        self._notify_management(tenant)
        if self._dispatch_export is not None and created.key:
            try:
                dispatch = self._dispatch_export
                dispatch(created.key)
            except Exception as exc:  # noqa: BLE001 - a broker outage leaves the request pending; the beat ends it
                logger.error("tenant_export.dispatch_failed", error_type=type(exc).__name__)
        return created

    def _notify_management(self, tenant: Tenant) -> None:
        """AK-36 — every member with the management scope is told an export was requested (best effort)."""
        if self._email is None:
            logger.warning("tenant_export.notice_not_sent", reason="no_mailer")
            return
        recipients = [
            member.user_key
            for member in self._memberships.active_memberships_of(tenant_key=tenant.key or "")
            if AdminScope.MANAGEMENT in member.admin_scopes
        ]
        body = (
            "<p>A complete export of the data of your garden was requested in Kamerplanter. "
            "If you did not expect this, check the garden's members and contact your operator.</p>"
        )
        for user_key in sorted(set(recipients)):
            try:
                account = self._users.get_by_key(user_key)
                if account is None or not account.email:
                    continue
                self._email.send_notification_email(
                    to_email=account.email, subject="Kamerplanter: garden export requested", html_body=body
                )
            except Exception as exc:  # noqa: BLE001 - one mailbox must not stop the others
                logger.warning(
                    "tenant_export.notice_failed", member=log_subject(user_key), error_type=type(exc).__name__
                )

    # ── export: list and download ──────────────────────────────────────

    def list_exports(
        self,
        *,
        requester: User,
        authenticated_with_api_key: bool,
        origin: TenantExportOrigin,
        offset: int,
        limit: int,
        slug: str | None = None,
        tenant_key: str | None = None,
    ) -> list[TenantExportRequest]:
        """The requester's own exports of the tenant, newest first, one page (REQ-056 §8.2); a person only."""
        self._require_person(requester, authenticated_with_api_key)
        tenant = self._resolve_for(requester=requester, origin=origin, slug=slug, tenant_key=tenant_key)
        return self._exports.list_by_tenant(
            tenant_key=tenant.key or "", requested_by_user_key=requester.key or "", offset=offset, limit=limit
        )

    def prepare_download(
        self,
        export_key: str,
        *,
        requester: User,
        authenticated_with_api_key: bool,
        origin: TenantExportOrigin,
        slug: str | None = None,
        tenant_key: str | None = None,
    ) -> TenantExportRequest:
        """The completed, unexpired export of the requester (404 otherwise — AK-35); audited (SEC-006).

        A person only, never an API key: the archive holds every member's data (SEC-006).
        """
        self._require_person(requester, authenticated_with_api_key)
        tenant = self._resolve_for(requester=requester, origin=origin, slug=slug, tenant_key=tenant_key)
        request = self._exports.get(export_key)
        if request is None or request.tenant_key != tenant.key or request.requested_by_user_key != requester.key:
            raise NotFoundError("TenantExportRequest", export_key)
        expires_at = request.expires_at
        if expires_at is not None and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if (
            request.status != "completed"
            or not request.storage_key
            or (expires_at is not None and expires_at <= self._now())
        ):
            raise NotFoundError("TenantExportRequest", export_key)
        if self._audit is not None:
            self._audit.record_tenant_change(
                action=SecurityAuditAction.TENANT_EXPORT_DOWNLOADED,
                via=SecurityAuditVia.PLATFORM_ADMIN if origin == "platform_admin" else SecurityAuditVia.TENANT_ADMIN,
                actor_user_key=requester.key or "",
                tenant_key=request.tenant_key,
            )
        logger.info(
            "tenant_export.downloaded", tenant=log_tenant(request.tenant_key), subject=log_subject(requester.key)
        )
        return request

    async def open_download(self, request: TenantExportRequest) -> AsyncIterator[bytes]:
        if self._storage is None or not request.storage_key:
            raise NotFoundError("TenantExportRequest", request.key or "")
        return await self._storage.get_object(request.storage_key)

    # ── export: run (Celery, bulk queue) ───────────────────────────────

    def storage_key_of(self, request: TenantExportRequest) -> str:
        return f"t/{request.tenant_key}/{ARCHIVE_STORAGE_CATEGORY}/{request.key}.zip"

    def _size_limit(self, tenant_key: str) -> int | None:
        limit_mb = self._entitlements.limit(tenant_key, EntitlementDimension.STORAGE_MB)
        if limit_mb is None:
            return None
        return int(limit_mb * 1024 * 1024 * _SIZE_HEADROOM)

    async def run_export(self, export_key: str) -> TenantExportRequest | None:
        """Claim the export, write the archive, store it and complete the request — or end it ``failed``."""
        now = self._now()
        claimed = self._exports.claim(export_key, now)
        if claimed is None:
            logger.info("tenant_export.not_claimed", export_key=export_key)
            return self._exports.get(export_key)
        tenant = self._tenants.get_by_key(claimed.tenant_key)
        if tenant is None or self._storage is None:
            return self._fail_export(claimed, "tenant_not_exportable" if tenant is None else "storage_unavailable")
        storage_key = self.storage_key_of(claimed)
        with tempfile.SpooledTemporaryFile(max_size=_SPOOL_BYTES) as target:
            try:
                counts = await self.write_archive(
                    tenant,
                    target,
                    max_bytes=self._size_limit(claimed.tenant_key),
                    heartbeat=lambda: self._beat(claimed),
                )
            except ArchiveTooLargeError:
                logger.info("tenant_export.too_large", tenant=log_tenant(claimed.tenant_key))
                return self._fail_export(claimed, "too_large")
            except Exception as exc:  # noqa: BLE001 - recorded as failed; the requester may ask again
                logger.error(
                    "tenant_export.failed", tenant=log_tenant(claimed.tenant_key), error_type=type(exc).__name__
                )
                return self._fail_export(claimed, "internal_error")
            size = target.tell()
            target.seek(0)
            try:
                await self._storage.put_object(
                    storage_key,
                    _chunks(target),
                    "application/zip",
                    metadata={"export_key": claimed.key or ""},
                )
            except Exception as exc:  # noqa: BLE001 - recorded as failed
                logger.error("tenant_export.store_failed", error_type=type(exc).__name__)
                return self._fail_export(claimed, "storage_unavailable")
        done = self._now()
        completed = self._exports.update_fields(
            claimed.key or "",
            {
                "status": "completed",
                "storage_key": storage_key,
                "size_bytes": size,
                "counts": counts,
                "completed_at": done,
                "expires_at": done + self._retention,
                "updated_at": done,
            },
        )
        logger.info("tenant_export.completed", tenant=log_tenant(claimed.tenant_key), size_bytes=size)
        return completed

    def _beat(self, request: TenantExportRequest) -> None:
        self._exports.update_fields(request.key or "", {"updated_at": self._now()})

    def _fail_export(self, request: TenantExportRequest, reason: str) -> TenantExportRequest | None:
        now = self._now()
        return self._exports.update_fields(
            request.key or "", {"status": "failed", "failure_reason": reason, "completed_at": None, "updated_at": now}
        )

    async def write_archive(
        self,
        tenant: Tenant,
        target: IO[bytes],
        *,
        max_bytes: int | None,
        heartbeat: Callable[[], None] | None = None,
    ) -> dict[str, int]:
        """Write the archive of *tenant* into *target*; returns rows per part (REQ-056 §8.3)."""
        tenant_key = tenant.key or ""
        writer = TenantArchiveWriter(target, max_bytes=max_bytes)
        beat = heartbeat or (lambda: None)
        try:
            stored_tenant = self._store.tenant_document(tenant_key) or {}
            writer.write_json(TENANT_NAME, _tenant_part(stored_tenant))
            present = self._store.collection_names()
            exported_ids: set[str] = {f"tenants/{tenant_key}"}
            parent_keys: dict[str, list[str]] = {}
            parents = {p.collection for e in TenantExportEngine.exported_entries() for p in e.parents}
            attachments: list[dict[str, Any]] = []
            for entry in TenantExportEngine.exported_entries():
                if entry.collection not in present:
                    continue
                keys: list[str] = []
                writer.write_lines(
                    f"collections/{entry.collection}.jsonl",
                    self._pages(entry, tenant_key, parent_keys, keys, attachments, beat),
                )
                exported_ids.update(f"{entry.collection}/{key}" for key in keys)
                if entry.collection in parents:
                    parent_keys[entry.collection] = keys
            self._write_edges(writer, exported_ids, beat)
            writer.write_lines(MEMBERS_NAME, [self._members_of(tenant_key)])
            await self._write_objects(writer, tenant_key, attachments, beat)
            return writer.finish(
                {
                    "format": ARCHIVE_FORMAT,
                    "source_tenant_key": tenant_key,
                    "source_migration": self._store.migration_level(),
                    "created_at": self._now().isoformat(),
                    # Random per archive, never a URL or a host name (§8.3).
                    "source_instance_id": secrets.token_hex(16),
                    "excluded": TenantExportEngine.excluded_manifest(),
                },
                signing_key=self._signing_key,
            )
        except BaseException:
            writer.abort()
            raise

    def _pages(
        self,
        entry: TenantErasureEntry,
        tenant_key: str,
        parent_keys: dict[str, list[str]],
        keys: list[str],
        attachments: list[dict[str, Any]],
        beat: Callable[[], None],
    ) -> Iterator[list[dict[str, Any]]]:
        """The tenant's rows of *entry*, page by page, as the archive carries them; records keys and attachments."""
        for page in self._store.iter_tenant_rows(
            entry, tenant_key=tenant_key, parent_keys=parent_keys, page_size=PAGE_SIZE
        ):
            keys.extend(str(doc["_key"]) for doc in page)
            if entry.collection == "attachments":
                attachments.extend(page)
            beat()
            yield [archive_document(doc, collection=entry.collection) for doc in page]

    def _write_edges(self, writer: TenantArchiveWriter, exported_ids: set[str], beat: Callable[[], None]) -> None:
        """Every edge with both ends in the archive, or one end in it and the other a global catalogue row."""
        catalogues = TenantExportEngine.global_catalogues()
        hybrid = TenantExportEngine.HYBRID_CATALOGUES
        ids = sorted(exported_ids)
        for edge_collection in self._store.edge_collection_names():
            if edge_collection not in TenantExportEngine.IMPORTABLE_EDGES:
                continue  # SEC-002 — only what an import may write is carried
            kept: list[dict[str, Any]] = []
            foreign_hybrid: dict[str, set[str]] = {}
            candidates = self._store.edges_touching(edge_collection, ids)
            for edge in candidates:
                for end in ("_from", "_to"):
                    other: str = str(edge[end])
                    collection, _, key = _split_id(other)
                    if other not in exported_ids and collection in hybrid:
                        foreign_hybrid.setdefault(collection, set()).add(key)
            global_ids = {
                f"{collection}/{key}"
                for collection, keys in foreign_hybrid.items()
                for key in self._store.existing_global_keys(collection, sorted(keys))
            }
            for edge in candidates:
                ends_ok = True
                for end in ("_from", "_to"):
                    end_id = str(edge[end])
                    collection = _split_id(end_id)[0]
                    if end_id in exported_ids or collection in catalogues or end_id in global_ids:
                        continue
                    ends_ok = False
                if ends_ok:
                    kept.append(archive_document(edge))
            beat()
            writer.write_lines(f"{EDGES_DIR}{edge_collection}.jsonl", [kept])

    def _members_of(self, tenant_key: str) -> list[dict[str, Any]]:
        """``members.jsonl``: user key, display name, role, scopes, joined_at — no e-mail (E-09)."""
        rows: list[dict[str, Any]] = []
        for member in self._memberships.active_memberships_of(tenant_key=tenant_key):
            account = self._users.get_by_key(member.user_key)
            if account is not None and not allows_interactive_auth(account):
                continue  # service accounts are not exported (§8.2)
            rows.append(
                {
                    "user_key": member.user_key,
                    "display_name": account.display_name if account is not None else None,
                    "role": str(member.role),
                    "admin_scopes": [str(scope) for scope in member.admin_scopes],
                    "is_active": member.is_active,
                    "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                }
            )
        return rows

    async def _write_objects(
        self,
        writer: TenantArchiveWriter,
        tenant_key: str,
        attachments: list[dict[str, Any]],
        beat: Callable[[], None],
    ) -> None:
        """The original of every exported attachment under ``objects/`` (renditions are re-rendered on demand)."""
        if self._storage is None:
            return
        prefix = f"t/{tenant_key}/"
        for attachment in attachments:
            row: dict[str, Any] = attachment
            key = row.get("storage_key")
            if not isinstance(key, str) or key[: len(prefix)] != prefix:
                continue
            try:
                stream = await self._storage.get_object(key)
                data = b"".join([chunk async for chunk in stream])
            except NotFoundError:
                logger.warning("tenant_export.object_missing", tenant=log_tenant(tenant_key))
                continue
            writer.write_object(key[len(prefix) :], data)
            beat()

    # ── import: request (sync, behind the route) ──────────────────────

    def request_import(
        self,
        upload: IO[bytes],
        *,
        size_bytes: int,
        requester: User,
        authenticated_with_api_key: bool,
        member_mapping: dict[str, dict[str, Any]],
        plan_key: str | None,
        factors: StepUpFactors,
        client_ip: str | None,
    ) -> TenantImportRequest:
        """Verify an uploaded archive completely, then store it and dispatch the import (REQ-056 §8.4).

        The step-up comes first, bound to the upload's content hash (SEC-008/-009): nothing of an
        archive is parsed for a request that has not proven who is asking.
        """
        self._require_person(requester, authenticated_with_api_key)
        if not self._is_platform_admin(requester.key or ""):
            raise ForbiddenError("Platform admin role required.")
        if size_bytes > self._max_upload:
            raise PayloadTooLargeError(self._max_upload)
        digest = upload_sha256(upload)
        self._step_up.verify(
            requester,
            action="tenant_import",
            target=f"{IMPORT_TARGET_PREFIX}{digest[:_IMPORT_TARGET_DIGITS]}",
            echo_ok=None,
            password=factors.password,
            code=factors.code,
            reauth_token=factors.reauth_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        upload.seek(0)
        try:
            archive = self._verified_archive(upload)
            member_grants = self._resolve_member_mapping(archive, member_mapping)
            chosen_plan = plan_key or self._entitlements.default_plan_key()
            if self._entitlements.get_plan(chosen_plan) is None:
                raise ValidationError(f"Plan '{chosen_plan}' does not exist.")
            if self._storage is None:
                raise ValidationError("This installation has no object storage to hold the upload.")
        except (TenantImportRefusedError, ValidationError) as exc:
            # I9 — a refused archive leaves a trace: who tried which archive, and why it was refused.
            code = exc.error_code if isinstance(exc, TenantImportRefusedError) else "VALIDATION_ERROR"
            self._audit_import_refused(requester, digest, code)
            raise
        now = self._now()
        created = self._imports.create(
            TenantImportRequest(
                requested_by_user_key=requester.key or "",
                status="pending",
                source_format=archive.format,
                member_grants=member_grants,
                verified=archive.verified,
                plan_key=chosen_plan,
                archive_sha256=digest,
                requested_at=now,
                updated_at=now,
            )
        )
        upload_key = f"{_IMPORT_UPLOAD_PREFIX}{created.key}.zip"
        upload.seek(0)
        run_async(self._storage.put_object(upload_key, _chunks(upload), "application/zip"))
        stored = self._imports.update_fields(created.key or "", {"upload_storage_key": upload_key, "updated_at": now})
        if self._audit is not None:
            self._audit.record_tenant_change(
                action=SecurityAuditAction.TENANT_IMPORT_REQUESTED,
                via=SecurityAuditVia.PLATFORM_ADMIN,
                actor_user_key=requester.key or "",
                tenant_key="",
                archive_sha256=digest,
                outcome="accepted",
            )
        logger.info("tenant_import.requested", subject=log_subject(requester.key), verified=archive.verified)
        if self._dispatch_import is not None and created.key:
            try:
                dispatch = self._dispatch_import
                dispatch(created.key)
            except Exception as exc:  # noqa: BLE001 - logged; the beat ends a request that never runs
                logger.error("tenant_import.dispatch_failed", error_type=type(exc).__name__)
        return stored or created

    def _audit_import_refused(self, requester: User, digest: str, code: str) -> None:
        if self._audit is not None:
            self._audit.record_tenant_change(
                action=SecurityAuditAction.TENANT_IMPORT_REQUESTED,
                via=SecurityAuditVia.PLATFORM_ADMIN,
                actor_user_key=requester.key or "",
                tenant_key="",
                archive_sha256=digest,
                outcome=f"refused:{code}",
            )
        logger.info("tenant_import.refused", subject=log_subject(requester.key), code=code)

    def get_import(
        self, import_key: str, *, requester: User, authenticated_with_api_key: bool = False
    ) -> TenantImportRequest:
        """The import's state and report — a platform admin in person, never an API key (I6)."""
        self._require_person(requester, authenticated_with_api_key)
        if not self._is_platform_admin(requester.key or ""):
            raise ForbiddenError("Platform admin role required.")
        request = self._imports.get(import_key)
        if request is None:
            raise NotFoundError("TenantImportRequest", import_key)
        return request

    def _verified_archive(self, upload: IO[bytes]) -> TenantArchive:
        """Directory bounds, format, checksums, signature, ownership, references, objects, catalogue (§8.4 step 1)."""
        try:
            # SEC-R2-01 — a fixed ceiling, not a multiple of the upload limit; ratio and row bounds inside.
            archive = read_tenant_archive(
                upload,
                max_uncompressed_bytes=MAX_UNCOMPRESSED_BYTES,
                max_entry_bytes=self._max_object_bytes or self._max_upload,
                signing_key=self._signing_key,
            )
            TenantImportEngine.validate_structure(archive)
            engine = TenantImportEngine(archive, target_tenant_key="", member_accounts={})
            engine.validate_documents()
            self._check_objects(archive)
        except TenantArchiveError as exc:
            raise TenantImportRefusedError(exc.code, str(exc), exc.entries) from exc
        level = self._store.migration_level()
        if archive.source_migration and level and archive.source_migration > level:
            raise TenantImportRefusedError(
                "IMPORT_FORMAT_UNSUPPORTED",
                "The archive comes from a newer installation than this one; update this installation first.",
            )
        missing = self._missing_catalogue_entries(engine)
        if missing:
            raise TenantImportRefusedError(
                "IMPORT_MISSING_CATALOG_ENTRIES",
                "The archive points at catalogue entries this installation does not have.",
                missing,
            )
        return archive

    def _check_objects(self, archive: TenantArchive) -> None:
        """Every object belongs to an attachment row of the archive and has a type the target accepts (SEC-010)."""
        prefix = f"t/{archive.source_tenant_key}/"
        types: dict[str, str] = {}
        refused: list[str] = []
        for row in archive.collections.get("attachments", []):
            document: dict[str, Any] = row
            key = document.get("storage_key")
            stated_type: str = str(document.get("mime_type") or "")
            mime = stated_type.lower().strip()
            category = str(document.get("category") or "")
            if not isinstance(key, str) or not key.startswith(prefix):
                continue  # the engine refuses a foreign key; a missing one has no object
            path = key[len(prefix) :]
            allowed_for: Callable[[str], list[str]] | None = self._allowed_mime_types
            allowed = allowed_for(category) if allowed_for is not None else [mime]
            if mime in _NEVER_IMPORTED_TYPES or mime not in allowed:
                refused.append(f"attachments/{document.get('_key')}: {mime or 'no type'}")
            types[path] = mime
        for path, data in archive.objects.items():
            if path not in types:
                refused.append(f"objects/{path}: no attachment of the archive names it")
            elif self._max_object_bytes is not None and len(data) > self._max_object_bytes:
                refused.append(f"objects/{path}: larger than the object limit")
        if refused:
            raise TenantArchiveError(
                "IMPORT_FORMAT_UNSUPPORTED",
                "the archive carries objects this installation does not accept",
                entries=refused,
            )

    def _catalogue_rows(self, engine: TenantImportEngine) -> tuple[set[str], list[str]]:
        """``(existing "<collection>/<key>", missing "<collection>/<key>")`` of every catalogue row referenced."""
        existing: set[str] = set()
        missing: list[str] = []
        catalogues = TenantExportEngine.global_catalogues()
        for targets, keys in engine.catalogue_requirements().items():
            found: set[str] = set()
            for collection in targets.split("|"):
                # I10 — no row of a pure catalogue is a tenant's: a legacy ``tenant_key`` stamp on one
                # (v0004, kept on operator-created harvest indicators by v0070) is not ownership.
                hits = self._store.existing_global_keys(collection, sorted(keys), any_row=collection in catalogues)
                existing.update(f"{collection}/{key}" for key in hits)
                found |= hits
            missing.extend(f"{targets.split('|')[0]}/{key}" for key in sorted(keys - found))
        return existing, sorted(missing)

    def _missing_catalogue_entries(self, engine: TenantImportEngine) -> list[str]:
        return self._catalogue_rows(engine)[1]

    def _resolve_member_mapping(
        self, archive: TenantArchive, member_mapping: dict[str, dict[str, Any]]
    ) -> dict[str, TenantImportMemberGrant]:
        """``archive user key → account + the role the admin confirmed``; 422 for anything unresolvable.

        The role and scopes come from the mapping, never from ``members.jsonl`` (SEC-003): the
        admin states what each person gets in the new tenant.
        """
        known = {member.user_key for member in archive.members}
        resolved: dict[str, TenantImportMemberGrant] = {}
        refused: list[str] = []
        for old_key, entry in member_mapping.items():
            stated_email: str = str(entry.get("email") or "")
            email = stated_email.strip().lower()
            account = self._users.get_by_email(email) if old_key in known and email else None
            try:
                role = TenantRole(str(entry.get("role") or ""))
                raw_scopes = entry.get("admin_scopes") or []
                if not isinstance(raw_scopes, list):
                    raise ValueError("admin_scopes")
                scopes = sorted({AdminScope(str(scope)) for scope in raw_scopes})
            except ValueError:
                refused.append(old_key)
                continue
            if account is None or not account.key or not account.is_active or not allows_interactive_auth(account):
                # I8 — a deactivated account is no member to hand a garden to.
                refused.append(old_key)
                continue
            resolved[old_key] = TenantImportMemberGrant(account_key=account.key, role=role, admin_scopes=scopes)
        accounts = [grant.account_key for grant in resolved.values()]
        if len(accounts) != len(set(accounts)):
            refused.extend(sorted(k for k, g in resolved.items() if accounts.count(g.account_key) > 1))
        if refused:
            raise TenantImportRefusedError(
                "IMPORT_MEMBER_NOT_FOUND",
                "Each mapped member must be a member of the archive, the address an existing, active account "
                "(each once), and the role and scopes valid ones.",
                sorted(set(refused)),
            )
        return resolved

    # ── import: run (Celery, bulk queue) ───────────────────────────────

    async def run_import(self, import_key: str) -> TenantImportRequest | None:
        """Import a stored archive into a new tenant; on failure remove everything written (§8.4 step 5)."""
        claimed = self._imports.claim(import_key, self._now())
        if claimed is None:
            return self._imports.get(import_key)
        upload_key = claimed.upload_storage_key
        try:
            if self._storage is None or not upload_key:
                return self._fail_import(claimed, "IMPORT_STORAGE")
            with tempfile.SpooledTemporaryFile(max_size=_SPOOL_BYTES) as buffer:
                stream = await self._storage.get_object(upload_key)
                async for chunk in stream:
                    buffer.write(chunk)
                buffer.seek(0)
                self._touch_import(import_key)
                try:
                    archive = self._verified_archive(buffer)
                except TenantImportRefusedError as exc:
                    return self._fail_import(claimed, exc.error_code, missing=_reasons(exc))
            self._touch_import(import_key)
            outcome = await self.import_archive(
                archive,
                actor_user_key=claimed.requested_by_user_key,
                member_grants=claimed.member_grants,
                plan_key=claimed.plan_key or self._entitlements.default_plan_key(),
                # I3 — the key is on the request before the tenant exists: no window in which a founded
                # tenant is named by nothing the sweep reads.
                before_founding=lambda key: self._imports.update_fields(
                    import_key, {"status": "running", "target_tenant_key": key, "updated_at": self._now()}
                ),
                heartbeat=lambda: self._touch_import(import_key),
            )
        except ImportCleanupPendingError as exc:
            return self._fail_import(claimed, exc.code, cleanup_pending_tenant=exc.tenant_key)
        except TenantImportRefusedError as exc:
            return self._fail_import(claimed, exc.error_code, missing=_reasons(exc))
        except Exception as exc:  # noqa: BLE001 - recorded as failed; the rollback removed what the run wrote
            logger.error("tenant_import.failed", error_type=type(exc).__name__)
            return self._fail_import(claimed, "IMPORT_FAILED")
        finally:
            if self._storage is not None and upload_key:
                try:
                    await self._storage.delete_object(upload_key)
                except Exception as exc:  # noqa: BLE001 - the stale sweep retries it
                    logger.warning("tenant_import.upload_delete_failed", error_type=type(exc).__name__)
        done = self._now()
        if self._audit is not None:
            self._audit.record_tenant_change(
                action=SecurityAuditAction.TENANT_IMPORTED,
                via=SecurityAuditVia.PLATFORM_ADMIN,
                actor_user_key=claimed.requested_by_user_key,
                tenant_key=outcome.tenant_key,
                archive_sha256=claimed.archive_sha256,
            )
        return self._imports.update_fields(
            import_key,
            {
                "status": "completed",
                "target_tenant_key": outcome.tenant_key,
                "report": outcome.report,
                "completed_at": done,
                "updated_at": done,
                "upload_storage_key": None,
                "member_grants": {},
            },
        )

    def _touch_import(self, import_key: str) -> None:
        """The run's heartbeat: the stale sweep (SEC-007) only takes a run whose heartbeat stopped."""
        self._imports.update_fields(import_key, {"updated_at": self._now()})

    def _fail_import(
        self,
        request: TenantImportRequest,
        code: str,
        *,
        missing: list[str] | None = None,
        cleanup_pending_tenant: str | None = None,
    ) -> TenantImportRequest | None:
        """End the request ``failed`` — or ``cleanup_pending`` with the tenant's key when a rollback left rows.

        Audited either way (``tenant_import_requested`` with the outcome and the archive's hash, I9).
        """
        now = self._now()
        pending = bool(cleanup_pending_tenant)
        if self._audit is not None:
            self._audit.record_tenant_change(
                action=SecurityAuditAction.TENANT_IMPORT_REQUESTED,
                via=SecurityAuditVia.PLATFORM_ADMIN,
                actor_user_key=request.requested_by_user_key,
                tenant_key=cleanup_pending_tenant or request.target_tenant_key or "",
                archive_sha256=request.archive_sha256,
                outcome=f"{'cleanup_pending' if pending else 'failed'}:{code}",
            )
        return self._imports.update_fields(
            request.key or "",
            {
                "status": "cleanup_pending" if pending else "failed",
                "failure_reason": code,
                "missing_catalog_entries": (missing or [])[:200] if code == "IMPORT_MISSING_CATALOG_ENTRIES" else [],
                "target_tenant_key": cleanup_pending_tenant if pending else None,
                "completed_at": None if pending else now,
                "updated_at": now,
                "upload_storage_key": None,
                "member_grants": {},
            },
        )

    async def import_archive(
        self,
        archive: TenantArchive,
        *,
        actor_user_key: str,
        member_grants: dict[str, TenantImportMemberGrant],
        plan_key: str,
        before_founding: Callable[[str], object] | None = None,
        heartbeat: Callable[[], object] | None = None,
    ) -> TenantImportOutcome:
        """Found the new tenant (``importing``), write the archive into it, then activate it; roll back on failure.

        The tenant and its memberships stay unreachable until the last row is written (SEC-007): a
        member never sees a half-imported garden, and a run that dies leaves a tenant the stale sweep
        erases rather than one somebody works in. The tenant's key is chosen here and handed to
        *before_founding* first (the run records it on its request). A rollback that cannot remove
        everything raises :class:`ImportCleanupPendingError` and leaves the tenant ``importing``.

        The owner is the longest-serving mapped member the admin confirmed as lead + management, with
        the scopes the admin confirmed (SEC-R2-02). Without one, the acting admin becomes the owner of
        the new tenant with both scopes — the documented fallback, so the tenant is never stranded
        without a member who can manage it.
        """
        owner_grant = self._owner_of(archive, member_grants)
        owner = owner_grant.account_key if owner_grant is not None else actor_user_key
        joined = {member.user_key: member.joined_at for member in archive.members}
        members = [
            Membership(
                user_key=grant.account_key,
                tenant_key="",
                role=grant.role,
                admin_scopes=list(grant.admin_scopes),
                is_active=False,
                joined_at=joined.get(old_key),
            )
            for old_key, grant in member_grants.items()
        ]
        source = archive.tenant
        raw_description = source.get("description")
        raw_settings = source.get("settings")
        description: str | None = raw_description if isinstance(raw_description, str) else None
        tenant_settings: dict[str, Any] = raw_settings if isinstance(raw_settings, dict) else {}
        tenant_key = new_document_key()
        if before_founding is not None:
            before_founding(tenant_key)
        self._tenant_service.found_imported_tenant(
            actor_user_key=actor_user_key,
            name=str(source.get("name") or "Imported garden"),
            slug_hint=str(source.get("slug") or source.get("name") or "imported-garden"),
            description=description,
            settings=tenant_settings,
            plan_key=plan_key,
            owner_user_key=owner,
            members=members,
            founder_scopes=list(owner_grant.admin_scopes) if owner_grant is not None else None,
            tenant_key=tenant_key,
        )
        account_keys = {old_key: grant.account_key for old_key, grant in member_grants.items()}
        engine = TenantImportEngine(archive, target_tenant_key=tenant_key, member_accounts=account_keys)
        written: dict[str, list[str]] = {}
        objects_written: list[str] = []
        beat = heartbeat or (lambda: None)
        try:
            existing_global, missing = self._catalogue_rows(engine)
            if missing:
                raise TenantImportRefusedError(
                    "IMPORT_MISSING_CATALOG_ENTRIES", "catalogue entries vanished during the import", missing
                )
            beat()
            report: dict[str, int] = {}
            for collection in TenantExportEngine.exported_collections():
                documents = archive.collections.get(collection, [])
                for start in range(0, len(documents), PAGE_SIZE):
                    batch = [
                        engine.remap_document(collection, document, existing_global=existing_global)
                        for document in documents[start : start + PAGE_SIZE]
                    ]
                    if collection == "attachments":
                        batch = [_object_facts(row, archive.objects, tenant_key) for row in batch]
                    written.setdefault(collection, []).extend(self._store.insert_documents(collection, batch))
                    beat()
                if documents:
                    report[collection] = len(documents)
            for name, edges in sorted(archive.edges.items()):
                if name not in TenantExportEngine.IMPORTABLE_EDGES:
                    raise TenantImportRefusedError(
                        "IMPORT_FORMAT_UNSUPPORTED", f"edge collection {name} is not imported"
                    )
                remapped = [
                    rewritten
                    for edge in edges
                    if (rewritten := engine.remap_edge(edge, existing_global=existing_global)) is not None
                ]
                for start in range(0, len(remapped), PAGE_SIZE):
                    keys = self._store.insert_documents(name, remapped[start : start + PAGE_SIZE])
                    written.setdefault(name, []).extend(keys)
                    beat()
                if remapped:
                    report[f"edges:{name}"] = len(remapped)
            if archive.objects and self._storage is not None:
                types = self._object_types(archive)
                for path, data in sorted(archive.objects.items()):
                    target = f"t/{tenant_key}/{path}"
                    await self._storage.put_object(target, _single(data), types.get(path) or "application/octet-stream")
                    objects_written.append(target)
                    beat()
                report["objects"] = len(objects_written)
            report["members"] = len({m.user_key for m in members} | {owner})
            self._tenant_service.activate_imported_tenant(tenant_key)
        except BaseException as exc:
            clean = await self._rollback(tenant_key, written, objects_written)
            if not clean and isinstance(exc, Exception):
                code = exc.error_code if isinstance(exc, TenantImportRefusedError) else "IMPORT_FAILED"
                raise ImportCleanupPendingError(tenant_key, code) from exc
            raise
        logger.info("tenant_import.completed", tenant=log_tenant(tenant_key), nulled=engine.nulled_references)
        return TenantImportOutcome(
            tenant_key=tenant_key,
            report=report,
            key_mapping=engine.mapping,
            nulled_references=engine.nulled_references,
        )

    @staticmethod
    def _object_types(archive: TenantArchive) -> dict[str, str]:
        prefix = f"t/{archive.source_tenant_key}/"
        types: dict[str, str] = {}
        for row in archive.collections.get("attachments", []):
            document: dict[str, Any] = row
            key = document.get("storage_key")
            if isinstance(key, str) and key.startswith(prefix):
                types[key[len(prefix) :]] = str(document.get("mime_type") or "")
        return types

    async def _rollback(self, tenant_key: str, written: dict[str, list[str]], objects: list[str]) -> bool:
        """Remove every row, edge and object the failed run wrote, then the tenant itself; ``True`` when clean.

        The tenant document and its memberships go only when everything else went (SEC-R2-03): a
        tenant shell removed over rows that stayed would leave rows of no tenant that no sweep finds.
        When anything is left, the tenant stays ``importing`` — unreachable — and the caller hands
        it to the sweep, which erases it through the tenant-erasure inventory.
        """
        clean = True
        for collection, keys in written.items():
            try:
                self._store.remove_documents(collection, keys)
            except Exception as exc:  # noqa: BLE001 - continue with the rest; the sweep erases what is left
                clean = False
                logger.error("tenant_import.rollback_failed", collection=collection, error_type=type(exc).__name__)
        if self._storage is not None:
            for key in objects:
                try:
                    await self._storage.delete_object(key)
                except NotFoundError:
                    continue
                except Exception as exc:  # noqa: BLE001 - continue with the rest; the sweep erases what is left
                    clean = False
                    logger.error("tenant_import.rollback_object_failed", error_type=type(exc).__name__)
        if not clean:
            logger.error("tenant_import.rollback_incomplete", tenant=log_tenant(tenant_key))
            return False
        try:
            self._store.remove_tenant_shell(tenant_key=tenant_key)
        except Exception as exc:  # noqa: BLE001 - the tenant is still ``importing``; the sweep erases it
            logger.error(
                "tenant_import.rollback_shell_failed", tenant=log_tenant(tenant_key), error_type=type(exc).__name__
            )
            return False
        logger.warning("tenant_import.rolled_back", tenant=log_tenant(tenant_key))
        return True

    @staticmethod
    def _owner_of(
        archive: TenantArchive, member_grants: dict[str, TenantImportMemberGrant]
    ) -> TenantImportMemberGrant | None:
        """The longest-serving mapped member the admin confirmed as lead + management, else ``None`` (the admin)."""
        joined = {member.user_key: member.joined_at or "" for member in archive.members}
        candidates = sorted(
            (
                (joined.get(old_key, ""), grant.account_key, grant)
                for old_key, grant in member_grants.items()
                if MembershipEngine.can_delete_tenant(grant.role, list(grant.admin_scopes))
            ),
            key=lambda candidate: (candidate[0], candidate[1]),
        )
        return candidates[0][2] if candidates else None

    # ── retention (hourly, with ``retention.expire_data_exports``) ─────

    async def expire(self) -> dict[str, int]:
        """Delete archives past R-05, end stale runs (exports and imports), purge request records past R-40."""
        now = self._now()
        expired = 0
        for request in self._exports.list_expiry_due(now):
            if request.storage_key and self._storage is not None:
                try:
                    await self._storage.delete_object(request.storage_key)
                except Exception as exc:  # noqa: BLE001 - retried by the next run
                    logger.warning("tenant_export.expire_delete_failed", error_type=type(exc).__name__)
                    continue
            elif request.storage_key:
                continue
            self._exports.update_fields(
                request.key or "", {"status": "expired", "storage_key": None, "updated_at": now}
            )
            expired += 1
        stale = 0
        for request in self._exports.list_stale_active(now - STALE_AFTER):
            await self._delete_partial_archive(request)
            self._fail_export(request, "internal_error")
            stale += 1
        abandoned = 0
        for stale_import in self._imports.list_stale_active(now - STALE_AFTER):
            if await self._sweep_abandoned_import(stale_import, now):
                abandoned += 1
        purged = self._exports.delete_finished_before(now - REQUEST_RETENTION)
        purged += self._imports.delete_finished_before(now - REQUEST_RETENTION)
        if expired or stale or purged or abandoned:
            logger.info(
                "tenant_export.expired", expired=expired, stale=stale, purged=purged, abandoned_imports=abandoned
            )
        return {"expired": expired, "stale": stale, "purged": purged, "abandoned_imports": abandoned}

    async def _delete_partial_archive(self, request: TenantExportRequest) -> None:
        """A run that died between storing the archive and completing the request leaves the object behind."""
        if self._storage is None or not request.key:
            return
        try:
            await self._storage.delete_object(self.storage_key_of(request))
        except NotFoundError:
            return
        except Exception as exc:  # noqa: BLE001 - best effort; the request ends failed either way
            logger.warning("tenant_export.stale_archive_delete_failed", error_type=type(exc).__name__)

    async def _sweep_abandoned_import(self, request: TenantImportRequest, now: datetime) -> bool:
        """An import whose run died, or whose rollback was incomplete: erase its half tenant, end the request.

        The tenant is still ``importing`` — nobody ever reached it — and goes through the
        tenant-erasure inventory like any deleted tenant (rows, edges, objects, readings; SEC-007,
        SEC-R2-03). The request keeps the tenant's key until the erasure has taken the tenant: when
        it cannot (yet), the request stays as it is and the next sweep tries again — ending it
        would leave rows no sweep can find. ``True`` when the request was ended.
        """
        target = request.target_tenant_key
        if target:
            try:
                erased = self._tenant_service.erase_abandoned_import(target, now=now)
            except Exception as exc:  # noqa: BLE001 - kept; the next sweep retries
                logger.error(
                    "tenant_import.sweep_erase_failed", tenant=log_tenant(target), error_type=type(exc).__name__
                )
                return False
            if not erased:
                left = self._tenants.get_by_key(target)
                if left is not None and left.status == TenantStatus.IMPORTING:
                    logger.error("tenant_import.sweep_erase_deferred", tenant=log_tenant(target))
                    return False
        if request.upload_storage_key and self._storage is not None:
            try:
                await self._storage.delete_object(request.upload_storage_key)
            except Exception as exc:  # noqa: BLE001 - an orphaned upload is logged
                logger.warning("tenant_import.sweep_upload_delete_failed", error_type=type(exc).__name__)
        pending_code = request.failure_reason if request.status == "cleanup_pending" else None
        self._fail_import(request, pending_code or "IMPORT_ABANDONED")
        logger.warning("tenant_import.abandoned", tenant=log_tenant(target or ""))
        return True


def _reasons(exc: TenantImportRefusedError) -> list[str]:
    return [str(detail["reason"]) for detail in exc.details if "reason" in detail]


def _object_facts(row: dict[str, Any], objects: dict[str, bytes], tenant_key: str) -> dict[str, Any]:
    """An imported attachment's ``sha256``/``byte_size`` from the object it names, never the archive's word (I7).

    The quota counts ``byte_size`` and a re-upload deduplicates on ``sha256``: both are facts of the
    bytes, and the bytes are in the archive. A row whose object the archive does not carry keeps its values
    (nothing is stored for it to contradict).
    """
    key = row.get("storage_key")
    prefix = f"t/{tenant_key}/"
    if not isinstance(key, str) or key[: len(prefix)] != prefix:
        return row
    data = objects.get(key[len(prefix) :])
    if data is None:
        return row
    return {**row, "sha256": hashlib.sha256(data).hexdigest(), "byte_size": len(data)}


def _split_id(document_id: str) -> tuple[str, str, str]:
    """``collection/key`` → ``(collection, "/", key)``."""
    return document_id.partition("/")


def _tenant_part(stored: dict[str, Any]) -> dict[str, Any]:
    """``tenant.json``: what the new tenant is founded from — no owner, no state, no plan of this installation."""
    keep = ("name", "slug", "tenant_type", "description", "settings", "max_members", "created_at")
    return {name: stored.get(name) for name in keep if name in stored}


async def _chunks(handle: IO[bytes]) -> AsyncIterator[bytes]:
    while chunk := handle.read(_CHUNK):
        yield chunk


async def _single(data: bytes) -> AsyncIterator[bytes]:
    yield data


_MAPPING_SHAPE = (
    'member_mapping must be a JSON object {"<archive user key>": {"email": "...", "role": "lead|grower|viewer", '
    '"admin_scopes": ["management", "technical"]}}.'
)


def member_mapping_from_form(raw: str | None) -> dict[str, dict[str, Any]]:
    """The ``member_mapping`` form field — per archive member the account's e-mail and the confirmed role; 422."""
    if not raw:
        return {}
    if len(raw) > 512 * 1024:
        raise ValidationError("member_mapping is too large.")
    try:
        value = json.loads(raw)
    except (ValueError, RecursionError) as exc:
        raise ValidationError(_MAPPING_SHAPE) from exc
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and isinstance(entry, dict) and isinstance(dict(entry).get("email"), str)
        for key, entry in value.items()
    ):
        raise ValidationError(_MAPPING_SHAPE)
    if len(value) > 1000:
        raise ValidationError("member_mapping lists too many members.")
    return value


def export_signing_key(secret: str) -> bytes | None:
    """The installation key that signs tenant archives (SEC-003), derived from an installation secret.

    A separate derivation (HMAC with a fixed label) so the archive signature never equals a token
    signature. Rotating the secret makes older archives read as unverified, nothing worse.
    """
    if not secret:
        return None
    return hmac.new(secret.encode("utf-8"), b"kamerplanter-tenant-export-signature/1", hashlib.sha256).digest()


def upload_sha256(upload: IO[bytes]) -> str:
    """The upload's SHA-256 (hex), read in chunks, nothing parsed: the one thing computed before the step-up."""
    upload.seek(0)
    digest = hashlib.sha256()
    while chunk := upload.read(_CHUNK):
        digest.update(chunk)
    upload.seek(0)
    return digest.hexdigest()


def import_step_up_target(upload: IO[bytes]) -> str:
    """``archive:<first 32 hex of the upload's SHA-256>`` — the step-up names the archive by content (SEC-009)."""
    return f"{IMPORT_TARGET_PREFIX}{upload_sha256(upload)[:_IMPORT_TARGET_DIGITS]}"
