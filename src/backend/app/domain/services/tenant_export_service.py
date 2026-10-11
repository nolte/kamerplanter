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
``tenant_import`` (target ``new:<slug>``). The upload is verified (format, checksums,
declared references, catalogue entries, member mapping) **before** anything is written —
a refusal is ``422`` with the code and the entries — then stored and imported by a
``bulk`` task into a **new** tenant with new keys for every document
(:class:`TenantImportEngine`). A failure part-way removes everything the run wrote:
no half tenant is left behind.

Not part of this slice (REQ-056 AK Stand, #2138): TimescaleDB readings, the quota checks of
the target plan before the write, the per-document validation against the domain models,
and the frontend.
"""

from __future__ import annotations

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
    MEMBERS_NAME,
    TENANT_NAME,
    ArchiveTooLargeError,
    TenantArchiveError,
    TenantArchiveWriter,
    TenantExportEngine,
    archive_document,
    peek_tenant_slug,
    read_tenant_archive,
)
from app.domain.engines.tenant_import_engine import TenantImportEngine
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

_CHUNK = 1024 * 1024


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
        origin: TenantExportOrigin,
        offset: int,
        limit: int,
        slug: str | None = None,
        tenant_key: str | None = None,
    ) -> list[TenantExportRequest]:
        """The requester's own exports of the tenant, newest first, one page (REQ-056 §8.2)."""
        tenant = self._resolve_for(requester=requester, origin=origin, slug=slug, tenant_key=tenant_key)
        return self._exports.list_by_tenant(
            tenant_key=tenant.key or "", requested_by_user_key=requester.key or "", offset=offset, limit=limit
        )

    def prepare_download(
        self,
        export_key: str,
        *,
        requester: User,
        origin: TenantExportOrigin,
        slug: str | None = None,
        tenant_key: str | None = None,
    ) -> TenantExportRequest:
        """The completed, unexpired export of the requester (404 otherwise — AK-35)."""
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
                }
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
            yield [archive_document(doc) for doc in page]

    def _write_edges(self, writer: TenantArchiveWriter, exported_ids: set[str], beat: Callable[[], None]) -> None:
        """Every edge with both ends in the archive, or one end in it and the other a global catalogue row."""
        catalogues = TenantExportEngine.global_catalogues()
        hybrid = TenantExportEngine.HYBRID_CATALOGUES
        ids = sorted(exported_ids)
        for edge_collection in self._store.edge_collection_names():
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
        member_mapping: dict[str, str],
        plan_key: str | None,
        factors: StepUpFactors,
        client_ip: str | None,
    ) -> TenantImportRequest:
        """Verify an uploaded archive completely, then store it and dispatch the import (REQ-056 §8.4)."""
        self._require_person(requester, authenticated_with_api_key)
        if not self._is_platform_admin(requester.key or ""):
            raise ForbiddenError("Platform admin role required.")
        if size_bytes > self._max_upload:
            raise PayloadTooLargeError(self._max_upload)
        slug = peek_tenant_slug(upload) or "tenant"
        self._step_up.verify(
            requester,
            action="tenant_import",
            target=f"new:{slug}",
            echo_ok=None,
            password=factors.password,
            code=factors.code,
            reauth_token=factors.reauth_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        upload.seek(0)
        archive = self._verified_archive(upload)
        member_accounts = self._resolve_member_mapping(archive, member_mapping)
        chosen_plan = plan_key or self._entitlements.default_plan_key()
        if self._entitlements.get_plan(chosen_plan) is None:
            raise ValidationError(f"Plan '{chosen_plan}' does not exist.")
        now = self._now()
        created = self._imports.create(
            TenantImportRequest(
                requested_by_user_key=requester.key or "",
                status="pending",
                source_format=archive.format,
                member_accounts=member_accounts,
                plan_key=chosen_plan,
                requested_at=now,
                updated_at=now,
            )
        )
        upload_key = f"{_IMPORT_UPLOAD_PREFIX}{created.key}.zip"
        if self._storage is None:
            self._imports.update_fields(created.key or "", {"status": "failed", "failure_reason": "IMPORT_STORAGE"})
            raise ValidationError("This installation has no object storage to hold the upload.")
        upload.seek(0)
        run_async(self._storage.put_object(upload_key, _chunks(upload), "application/zip"))
        stored = self._imports.update_fields(created.key or "", {"upload_storage_key": upload_key, "updated_at": now})
        if self._audit is not None:
            self._audit.record_tenant_change(
                action=SecurityAuditAction.TENANT_IMPORT_REQUESTED,
                via=SecurityAuditVia.PLATFORM_ADMIN,
                actor_user_key=requester.key or "",
                tenant_key="",
            )
        logger.info("tenant_import.requested", subject=log_subject(requester.key))
        if self._dispatch_import is not None and created.key:
            try:
                dispatch = self._dispatch_import
                dispatch(created.key)
            except Exception as exc:  # noqa: BLE001 - logged; the admin sees the request stay pending
                logger.error("tenant_import.dispatch_failed", error_type=type(exc).__name__)
        return stored or created

    def get_import(self, import_key: str, *, requester: User) -> TenantImportRequest:
        if not self._is_platform_admin(requester.key or ""):
            raise ForbiddenError("Platform admin role required.")
        request = self._imports.get(import_key)
        if request is None:
            raise NotFoundError("TenantImportRequest", import_key)
        return request

    def _verified_archive(self, upload: IO[bytes]) -> TenantArchive:
        """Format, checksums, declared references, migration level and catalogue entries (§8.4 step 1)."""
        try:
            archive = read_tenant_archive(upload, max_uncompressed_bytes=self._max_upload * 4)
            TenantImportEngine.validate_structure(archive)
        except TenantArchiveError as exc:
            raise TenantImportRefusedError(exc.code, str(exc), exc.entries) from exc
        level = self._store.migration_level()
        if archive.source_migration and level and archive.source_migration > level:
            raise TenantImportRefusedError(
                "IMPORT_FORMAT_UNSUPPORTED",
                "The archive comes from a newer installation than this one; update this installation first.",
            )
        missing = self._missing_catalogue_entries(TenantImportEngine(archive, target_tenant_key="", member_accounts={}))
        if missing:
            raise TenantImportRefusedError(
                "IMPORT_MISSING_CATALOG_ENTRIES",
                "The archive points at catalogue entries this installation does not have.",
                missing,
            )
        return archive

    def _catalogue_rows(self, engine: TenantImportEngine) -> tuple[set[str], list[str]]:
        """``(existing "<collection>/<key>", missing "<collection>/<key>")`` of every catalogue row referenced."""
        existing: set[str] = set()
        missing: list[str] = []
        for targets, keys in engine.catalogue_requirements().items():
            found: set[str] = set()
            for collection in targets.split("|"):
                hits = self._store.existing_global_keys(collection, sorted(keys))
                existing.update(f"{collection}/{key}" for key in hits)
                found |= hits
            missing.extend(f"{targets.split('|')[0]}/{key}" for key in sorted(keys - found))
        return existing, sorted(missing)

    def _missing_catalogue_entries(self, engine: TenantImportEngine) -> list[str]:
        return self._catalogue_rows(engine)[1]

    def _resolve_member_mapping(self, archive: TenantArchive, member_mapping: dict[str, str]) -> dict[str, str]:
        """``archive user key → account key`` for every mapping entry; 422 for an unknown key or address."""
        known = {member.user_key for member in archive.members}
        resolved: dict[str, str] = {}
        refused: list[str] = []
        for old_key, email in member_mapping.items():
            account = self._users.get_by_email(email.strip().lower()) if old_key in known else None
            if account is None or not account.key or not allows_interactive_auth(account):
                refused.append(old_key)
                continue
            resolved[old_key] = account.key
        if refused:
            raise TenantImportRefusedError(
                "IMPORT_MEMBER_NOT_FOUND",
                "Each mapped member must be a member of the archive and the address an existing account.",
                sorted(refused),
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
                try:
                    archive = self._verified_archive(buffer)
                except TenantImportRefusedError as exc:
                    return self._fail_import(
                        claimed, exc.error_code, missing=[d["reason"] for d in exc.details if "reason" in d]
                    )
            outcome = await self.import_archive(
                archive,
                actor_user_key=claimed.requested_by_user_key,
                member_accounts=claimed.member_accounts,
                plan_key=claimed.plan_key or self._entitlements.default_plan_key(),
                on_founded=lambda key: self._imports.update_fields(
                    import_key, {"status": "running", "target_tenant_key": key, "updated_at": self._now()}
                ),
            )
        except TenantImportRefusedError as exc:
            return self._fail_import(claimed, exc.error_code, missing=[d["reason"] for d in exc.details])
        except Exception as exc:  # noqa: BLE001 - recorded as failed; the import wrote nothing that stays
            logger.error("tenant_import.failed", error_type=type(exc).__name__)
            return self._fail_import(claimed, "IMPORT_FAILED")
        finally:
            if self._storage is not None and upload_key:
                try:
                    await self._storage.delete_object(upload_key)
                except Exception as exc:  # noqa: BLE001 - an orphaned upload is removed by the operator
                    logger.warning("tenant_import.upload_delete_failed", error_type=type(exc).__name__)
        done = self._now()
        if self._audit is not None:
            self._audit.record_tenant_change(
                action=SecurityAuditAction.TENANT_IMPORTED,
                via=SecurityAuditVia.PLATFORM_ADMIN,
                actor_user_key=claimed.requested_by_user_key,
                tenant_key=outcome.tenant_key,
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
                "member_accounts": {},
            },
        )

    def _fail_import(
        self, request: TenantImportRequest, code: str, *, missing: list[str] | None = None
    ) -> TenantImportRequest | None:
        now = self._now()
        return self._imports.update_fields(
            request.key or "",
            {
                "status": "failed",
                "failure_reason": code,
                "missing_catalog_entries": (missing or [])[:200] if code == "IMPORT_MISSING_CATALOG_ENTRIES" else [],
                "target_tenant_key": None,
                "completed_at": now,
                "updated_at": now,
                "upload_storage_key": None,
                "member_accounts": {},
            },
        )

    async def import_archive(
        self,
        archive: TenantArchive,
        *,
        actor_user_key: str,
        member_accounts: dict[str, str],
        plan_key: str,
        on_founded: Callable[[str], object] | None = None,
    ) -> TenantImportOutcome:
        """Found the new tenant and write the archive into it; roll everything back on any failure."""
        owner = self._owner_of(archive, member_accounts) or actor_user_key
        members = [
            Membership(
                user_key=member_accounts[member.user_key],
                tenant_key="",
                role=TenantRole(member.role),
                admin_scopes=[AdminScope(scope) for scope in member.admin_scopes],
                is_active=True,
                joined_at=member.joined_at,
            )
            for member in archive.members
            if member.user_key in member_accounts
        ]
        source = archive.tenant
        raw_description = source.get("description")
        raw_settings = source.get("settings")
        description: str | None = raw_description if isinstance(raw_description, str) else None
        tenant_settings: dict[str, Any] = raw_settings if isinstance(raw_settings, dict) else {}
        tenant = self._tenant_service.found_imported_tenant(
            actor_user_key=actor_user_key,
            name=str(source.get("name") or "Imported garden"),
            slug_hint=str(source.get("slug") or source.get("name") or "imported-garden"),
            description=description,
            settings=tenant_settings,
            plan_key=plan_key,
            owner_user_key=owner,
            members=members,
        )
        tenant_key = tenant.key or ""
        if on_founded is not None:
            on_founded(tenant_key)
        engine = TenantImportEngine(archive, target_tenant_key=tenant_key, member_accounts=member_accounts)
        written: dict[str, list[str]] = {}
        objects_written: list[str] = []
        try:
            existing_global, missing = self._catalogue_rows(engine)
            if missing:
                raise TenantImportRefusedError(
                    "IMPORT_MISSING_CATALOG_ENTRIES", "catalogue entries vanished during the import", missing
                )
            report: dict[str, int] = {}
            for collection in TenantExportEngine.exported_collections():
                documents = archive.collections.get(collection, [])
                for start in range(0, len(documents), PAGE_SIZE):
                    batch = [
                        engine.remap_document(collection, document, existing_global=existing_global)
                        for document in documents[start : start + PAGE_SIZE]
                    ]
                    written.setdefault(collection, []).extend(self._store.insert_documents(collection, batch))
                if documents:
                    report[collection] = len(documents)
            edge_names = set(self._store.edge_collection_names())
            for name, edges in archive.edges.items():
                if name not in edge_names:
                    raise TenantImportRefusedError("IMPORT_FORMAT_UNSUPPORTED", f"unknown edge collection {name}")
                remapped = [
                    rewritten
                    for edge in edges
                    if (rewritten := engine.remap_edge(edge, existing_global=existing_global)) is not None
                ]
                for start in range(0, len(remapped), PAGE_SIZE):
                    keys = self._store.insert_documents(name, remapped[start : start + PAGE_SIZE])
                    written.setdefault(name, []).extend(keys)
                if remapped:
                    report[f"edges:{name}"] = len(remapped)
            if archive.objects and self._storage is not None:
                for path, data in sorted(archive.objects.items()):
                    target = f"t/{tenant_key}/{path}"
                    await self._storage.put_object(target, _single(data), "application/octet-stream")
                    objects_written.append(target)
                report["objects"] = len(objects_written)
            report["members"] = len({m.user_key for m in members} | {owner})
        except BaseException:
            await self._rollback(tenant_key, written, objects_written)
            raise
        logger.info("tenant_import.completed", tenant=log_tenant(tenant_key), nulled=engine.nulled_references)
        return TenantImportOutcome(
            tenant_key=tenant_key,
            report=report,
            key_mapping=engine.mapping,
            nulled_references=engine.nulled_references,
        )

    async def _rollback(self, tenant_key: str, written: dict[str, list[str]], objects: list[str]) -> None:
        """Remove every row, edge and object the failed run wrote, then the tenant itself (no half tenant)."""
        for collection, keys in written.items():
            try:
                self._store.remove_documents(collection, keys)
            except Exception as exc:  # noqa: BLE001 - continue; the residue is logged
                logger.error("tenant_import.rollback_failed", collection=collection, error_type=type(exc).__name__)
        if self._storage is not None:
            for key in objects:
                try:
                    await self._storage.delete_object(key)
                except Exception as exc:  # noqa: BLE001
                    logger.error("tenant_import.rollback_object_failed", error_type=type(exc).__name__)
        self._store.remove_tenant_shell(tenant_key=tenant_key)
        logger.warning("tenant_import.rolled_back", tenant=log_tenant(tenant_key))

    @staticmethod
    def _owner_of(archive: TenantArchive, member_accounts: dict[str, str]) -> str | None:
        """The longest-serving mapped member with lead + management, else ``None`` (the admin owns it, §8.4)."""
        candidates = [
            member
            for member in archive.members
            if member.user_key in member_accounts
            and MembershipEngine.can_delete_tenant(
                TenantRole(member.role), [AdminScope(scope) for scope in member.admin_scopes]
            )
        ]
        candidates.sort(key=lambda member: member.joined_at or "")
        return member_accounts[candidates[0].user_key] if candidates else None

    # ── retention (hourly, with ``retention.expire_data_exports``) ─────

    async def expire(self) -> dict[str, int]:
        """Delete archives past R-05, end stale runs, purge request records past R-40."""
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
            self._fail_export(request, "internal_error")
            stale += 1
        purged = self._exports.delete_finished_before(now - REQUEST_RETENTION)
        purged += self._imports.delete_finished_before(now - REQUEST_RETENTION)
        if expired or stale or purged:
            logger.info("tenant_export.expired", expired=expired, stale=stale, purged=purged)
        return {"expired": expired, "stale": stale, "purged": purged}


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


def member_mapping_from_form(raw: str | None) -> dict[str, str]:
    """The ``member_mapping`` form field (JSON object ``{archive user key: e-mail}``); 422 when malformed."""
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise ValidationError("member_mapping must be a JSON object of user key to e-mail address.") from exc
    if not isinstance(value, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        raise ValidationError("member_mapping must be a JSON object of user key to e-mail address.")
    if len(value) > 1000:
        raise ValidationError("member_mapping lists too many members.")
    return value
