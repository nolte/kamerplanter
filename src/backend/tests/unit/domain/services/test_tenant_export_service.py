"""#2138 (REQ-056 §8.2, AK-26 … AK-28, AK-35, AK-36, AK-44) — who may export a tenant, how often, and how big.

The service decides from the **stored** membership (never a request context): the lead
role and the ``management`` scope, a human account, no API key; then the requester's own
step-up ``tenant_export`` bound to the tenant's key. An unknown slug answers exactly like
a tenant the caller may not export (§12.2). One export runs at a time per tenant, at most
``TENANT_EXPORTS_PER_DAY`` are requested in 24 hours, an archive past the storage quota
plus 10 % ends ``failed``/``too_large``, and an expired archive is not served.

In-memory doubles for the stores; the step-up verifier is a recording double whose
refusals are the real exception types (the verifier's own rule is
``test_step_up_service.py``'s).
"""

from __future__ import annotations

import io
import os
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from app.common.async_bridge import run_async
from app.common.enums import AdminScope, EntitlementDimension, SecurityAuditAction, TenantRole, TenantStatus
from app.common.exceptions import (
    ExportAlreadyRunningError,
    ForbiddenError,
    MemberLimitReachedError,
    NotFoundError,
    PhotoQuotaExceededError,
    RateLimitError,
    StorageQuotaExceededError,
    TenantImportRefusedError,
    UnauthorizedError,
)
from app.domain.models.membership import Membership
from app.domain.models.plan import Plan, PlanLimits
from app.domain.models.tenant import Tenant
from app.domain.models.tenant_erasure import TenantErasureEntry
from app.domain.models.tenant_export import TenantExportRequest, TenantImportRequest
from app.domain.models.user import User
from app.domain.services.entitlement_service import EntitlementService
from app.domain.services.tenant_export_service import StepUpFactors, TenantExportService
from tests.support.entitlement_doubles import InMemoryPlanRepository, standard_plan

NOW = datetime(2026, 10, 11, 12, 0, tzinfo=UTC)
LEAD = User.model_validate({"_key": "u-lead", "email": "lead@example.com", "display_name": "Lead"})
GROWER = User.model_validate({"_key": "u-grower", "email": "grower@example.com", "display_name": "Grower"})
STRANGER = User.model_validate({"_key": "u-x", "email": "x@example.com", "display_name": "X"})
ADMIN = User.model_validate({"_key": "u-admin", "email": "admin@example.com", "display_name": "Admin"})
ROBOT = User.model_validate(
    {"_key": "u-robot", "email": "robot@example.com", "display_name": "Robot", "account_type": "service"}
)


class _Tenants:
    def __init__(self, *tenants: Tenant) -> None:
        self.by_key = {t.key: t for t in tenants}

    def get_by_key(self, key: str) -> Tenant | None:
        return self.by_key.get(key)

    def get_by_slug(self, slug: str) -> Tenant | None:
        return next((t for t in self.by_key.values() if t.slug == slug), None)


class _Memberships:
    def __init__(self, *memberships: Membership) -> None:
        self.rows = list(memberships)

    def get_by_user_and_tenant(self, user_key: str, tenant_key: str) -> Membership | None:
        return next((m for m in self.rows if m.user_key == user_key and m.tenant_key == tenant_key), None)

    def active_memberships_of(self, *, tenant_key: str) -> list[Membership]:
        return [m for m in self.rows if m.tenant_key == tenant_key and m.is_active]


class _Exports:
    def __init__(self) -> None:
        self.rows: dict[str, TenantExportRequest] = {}
        self.seq = 0

    def create(self, request: TenantExportRequest) -> TenantExportRequest:
        self.seq += 1
        stored = request.model_copy(update={"key": f"exp-{self.seq}"})
        self.rows[stored.key or ""] = stored
        return stored

    def get(self, key: str) -> TenantExportRequest | None:
        return self.rows.get(key)

    def delete(self, key: str) -> bool:
        return self.rows.pop(key, None) is not None

    def list_by_tenant(self, *, tenant_key: str, requested_by_user_key: str, offset: int, limit: int):
        rows = [
            r
            for r in self.rows.values()
            if r.tenant_key == tenant_key and r.requested_by_user_key == requested_by_user_key
        ]
        return rows[offset : offset + limit]

    def count_requested_since(self, *, tenant_key: str, since: datetime) -> int:
        return sum(1 for r in self.rows.values() if r.tenant_key == tenant_key and r.requested_at >= since)

    def active_keys(self, *, tenant_key: str) -> list[str]:
        return [k for k, r in self.rows.items() if r.tenant_key == tenant_key and r.status in ("pending", "running")]

    def claim(self, key: str, now: datetime) -> TenantExportRequest | None:
        row = self.rows.get(key)
        if row is None or row.status != "pending":
            return None
        return self.update_fields(key, {"status": "running", "started_at": now})

    def update_fields(self, key: str, fields: dict[str, Any]) -> TenantExportRequest | None:
        if key not in self.rows:
            return None
        self.rows[key] = self.rows[key].model_copy(update=fields)
        return self.rows[key]

    def list_expiry_due(self, now: datetime) -> list[TenantExportRequest]:
        return [r for r in self.rows.values() if r.status == "completed" and r.expires_at and r.expires_at <= now]

    def list_stale_active(self, before: datetime) -> list[TenantExportRequest]:
        return [
            r
            for r in self.rows.values()
            if r.status in ("pending", "running") and (r.updated_at or r.requested_at) <= before
        ]

    def delete_finished_before(self, before: datetime) -> int:
        return 0


class _Imports:
    def __init__(self) -> None:
        self.rows: dict[str, TenantImportRequest] = {}
        self.seq = 0

    def create(self, request: TenantImportRequest) -> TenantImportRequest:
        self.seq += 1
        stored = request.model_copy(update={"key": f"imp-{self.seq}"})
        self.rows[stored.key or ""] = stored
        return stored

    def get(self, key: str) -> TenantImportRequest | None:
        return self.rows.get(key)

    def claim(self, key: str, now: datetime) -> TenantImportRequest | None:
        row = self.rows.get(key)
        if row is None or row.status != "pending":
            return None
        return self.update_fields(key, {"status": "validating", "updated_at": now})

    def update_fields(self, key: str, fields: dict[str, Any]) -> TenantImportRequest | None:
        if key not in self.rows:
            return None
        self.rows[key] = self.rows[key].model_copy(update=fields)
        return self.rows[key]

    def list_stale_active(self, before: datetime) -> list[TenantImportRequest]:
        return [
            r
            for r in self.rows.values()
            if r.status == "cleanup_pending"
            or (r.status in ("pending", "validating", "running") and (r.updated_at or r.requested_at) <= before)
        ]

    def delete_finished_before(self, before: datetime) -> int:
        return 0


class _TenantService:
    def __init__(self) -> None:
        self.erased: list[str] = []
        self.erasable = True

    def erase_abandoned_import(self, tenant_key: str, *, now: datetime) -> bool:
        self.erased.append(tenant_key)
        return self.erasable


class _Store:
    """Two rows of the tenant in one collection; nothing else."""

    def __init__(self, payload: int = 10) -> None:
        self.payload = payload

    def migration_level(self) -> str | None:
        return "v0091"

    def tenant_document(self, tenant_key: str) -> dict[str, Any] | None:
        return {"_key": tenant_key, "name": "Garden", "slug": "garden", "_rev": "x"}

    def collection_names(self) -> set[str]:
        return {"sites"}

    def edge_collection_names(self) -> list[str]:
        return []

    def iter_tenant_rows(self, entry: TenantErasureEntry, *, tenant_key: str, parent_keys, page_size: int):
        if entry.collection == "sites":
            yield [
                {"_key": f"s{i}", "tenant_key": tenant_key, "blob": os.urandom(self.payload).hex()} for i in range(2)
            ]

    def edges_touching(self, edge_collection: str, ids: list[str]) -> list[dict[str, Any]]:
        return []

    def existing_global_keys(self, collection: str, keys: list[str], *, any_row: bool = False) -> set[str]:
        return set()


class _Storage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []

    async def put_object(self, key, stream, mime_type, metadata=None):
        self.objects[key] = b"".join([chunk async for chunk in stream])

    async def get_object(self, key):
        if key not in self.objects:
            raise NotFoundError("storage object", key)
        data = self.objects[key]

        async def chunks():
            yield data

        return chunks()

    async def delete_object(self, key):
        self.objects.pop(key, None)
        self.deleted.append(key)


class _StepUp:
    """Records every verify; refuses an API key (403) and a missing/wrong password (401) like the real one."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def verify(self, requester, *, action, target, password, authenticated_with_api_key, **_: Any):
        self.calls.append({"user": requester.key, "action": action, "target": target})
        if authenticated_with_api_key:
            raise ForbiddenError("API key")
        if password != "right":
            raise UnauthorizedError("step-up required")
        return "password"


class _Entitlements:
    def __init__(self, storage_mb: int | None = None) -> None:
        self.storage_mb = storage_mb

    def limit(self, tenant_key: str, dimension: EntitlementDimension) -> int | None:
        assert dimension == EntitlementDimension.STORAGE_MB
        return self.storage_mb

    def default_plan_key(self) -> str:
        return "standard"

    def require_for_new_tenant(
        self, plan_key: str, dimension: EntitlementDimension, *, projected: Any, subject: str | None = None
    ) -> int | None:
        """Unlimited: the quota of the target plan is measured with the real service (``TestTheTargetPlan…``)."""
        return None

    #: An attribute, not a method: the double-signature guard (#1145) pairs methods by name with every
    #: service, and ``NutrientPlanService.get_plan`` is no relative of ``EntitlementService.get_plan``.
    get_plan = staticmethod(lambda plan_key: object() if plan_key == "standard" else None)


class _Audit:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def record_tenant_change(self, **row: Any) -> None:
        self.rows.append(row)


class _Mail:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send_notification_email(self, *, to_email: str, subject: str, html_body: str) -> None:
        self.sent.append(to_email)


class _Users:
    def __init__(self, *users: User) -> None:
        self.by_key = {u.key: u for u in users}

    def get_by_key(self, key: str) -> User | None:
        return self.by_key.get(key)

    def get_by_email(self, email: str) -> User | None:
        return next((u for u in self.by_key.values() if u.email == email), None)


def _membership(user: str, tenant: str, role: TenantRole, scopes: list[AdminScope]) -> Membership:
    return Membership(user_key=user, tenant_key=tenant, role=role, admin_scopes=scopes, is_active=True)


@pytest.fixture
def world():
    tenants = _Tenants(
        Tenant(_key="t-1", name="Garden", slug="garden", owner_user_key="u-lead", max_members=10),
        Tenant(_key="t-2", name="Other", slug="other", owner_user_key="u-x", max_members=10),
        Tenant(_key="t-sus", name="Paused", slug="paused", owner_user_key="u-lead", status=TenantStatus.SUSPENDED),
        Tenant(
            _key="t-pend",
            name="Leaving",
            slug="leaving",
            owner_user_key="u-lead",
            status=TenantStatus.PENDING_DELETION,
        ),
        Tenant(_key="platform", name="Platform", slug="platform", owner_user_key="u-admin", is_platform=True),
    )
    memberships = _Memberships(
        *(
            _membership("u-lead", t, TenantRole.LEAD, [AdminScope.MANAGEMENT, AdminScope.TECHNICAL])
            for t in ("t-1", "t-sus", "t-pend")
        ),
        _membership("u-grower", "t-1", TenantRole.GROWER, [AdminScope.MANAGEMENT]),
        _membership("u-robot", "t-1", TenantRole.LEAD, [AdminScope.MANAGEMENT]),
        _membership("u-x", "t-2", TenantRole.LEAD, [AdminScope.MANAGEMENT]),
        _membership("u-admin", "platform", TenantRole.LEAD, [AdminScope.MANAGEMENT]),
    )
    clock = SimpleNamespace(now=NOW)
    exports = _Exports()
    step_up = _StepUp()
    storage = _Storage()
    audit = _Audit()
    mail = _Mail()
    dispatched: list[str] = []
    entitlements = _Entitlements()
    imports = _Imports()
    tenant_service = _TenantService()

    def build(store: _Store | None = None, **extra: Any) -> TenantExportService:
        return TenantExportService(
            store=store or _Store(),
            export_repo=exports,
            import_repo=imports,  # type: ignore[arg-type]
            tenant_repo=tenants,  # type: ignore[arg-type]
            membership_repo=memberships,  # type: ignore[arg-type]
            user_repo=_Users(LEAD, GROWER, STRANGER, ADMIN),  # type: ignore[arg-type]
            tenant_service=tenant_service,  # type: ignore[arg-type]
            storage=storage,  # type: ignore[arg-type]
            step_up_verifier=step_up,  # type: ignore[arg-type]
            security_audit=audit,  # type: ignore[arg-type]
            entitlements=entitlements,  # type: ignore[arg-type]
            email_service=mail,
            exports_per_day=3,
            dispatch_export=dispatched.append,
            clock=lambda: clock.now,
            **extra,
        )

    return SimpleNamespace(
        build=build,
        exports=exports,
        step_up=step_up,
        storage=storage,
        audit=audit,
        mail=mail,
        dispatched=dispatched,
        clock=clock,
        entitlements=entitlements,
        imports=imports,
        tenant_service=tenant_service,
        tenants=tenants,
    )


def _request(service: TenantExportService, user: User = LEAD, *, slug: str = "garden", api_key: bool = False, **kw):
    return service.request_export(
        requester=user,
        authenticated_with_api_key=api_key,
        origin="tenant_management",
        factors=StepUpFactors(password=kw.pop("password", "right")),
        client_ip=None,
        slug=slug,
        **kw,
    )


class TestWhoMayExport:
    def test_lead_with_management_and_step_up_is_accepted(self, world) -> None:
        created = _request(world.build())

        assert created.status == "pending" and created.tenant_key == "t-1"
        assert world.step_up.calls == [{"user": "u-lead", "action": "tenant_export", "target": "t-1"}]
        assert world.dispatched == [created.key]
        # AK-36 — audited and every management holder mailed.
        assert world.audit.rows[0]["action"] == SecurityAuditAction.TENANT_EXPORT_REQUESTED
        assert world.audit.rows[0]["tenant_key"] == "t-1"
        assert sorted(world.mail.sent) == ["grower@example.com", "lead@example.com"]

    def test_without_step_up_nothing_is_recorded(self, world) -> None:
        with pytest.raises(UnauthorizedError):
            _request(world.build(), password=None)
        assert world.exports.rows == {}

    def test_an_api_key_is_refused_before_the_step_up(self, world) -> None:
        with pytest.raises(ForbiddenError):
            _request(world.build(), api_key=True)
        assert world.step_up.calls == []
        assert world.exports.rows == {}

    def test_a_service_account_is_refused(self, world) -> None:
        with pytest.raises(ForbiddenError):
            _request(world.build(), ROBOT)
        assert world.exports.rows == {}

    @pytest.mark.parametrize(
        ("user", "slug"), [(GROWER, "garden"), (STRANGER, "garden"), (LEAD, "other"), (LEAD, "nope")]
    )
    def test_non_lead_foreign_tenant_and_unknown_slug_are_one_answer(self, world, user, slug) -> None:
        with pytest.raises(ForbiddenError) as refused:
            _request(world.build(), user, slug=slug)
        assert refused.value.message == "Exporting a tenant requires the lead role and the management scope."
        assert world.step_up.calls == []

    def test_pending_deletion_is_exportable_suspended_is_not_for_the_management(self, world) -> None:
        assert _request(world.build(), slug="leaving").tenant_key == "t-pend"
        with pytest.raises(ForbiddenError):
            _request(world.build(), slug="paused")

    def test_a_platform_admin_exports_a_suspended_tenant(self, world) -> None:
        created = world.build().request_export(
            requester=ADMIN,
            authenticated_with_api_key=False,
            origin="platform_admin",
            factors=StepUpFactors(password="right"),
            client_ip=None,
            tenant_key="t-sus",
        )
        assert created.origin == "platform_admin"

    def test_a_member_is_no_platform_admin(self, world) -> None:
        with pytest.raises(ForbiddenError):
            world.build().request_export(
                requester=LEAD,
                authenticated_with_api_key=False,
                origin="platform_admin",
                factors=StepUpFactors(password="right"),
                client_ip=None,
                tenant_key="t-1",
            )


class TestHowOften:
    def test_a_second_export_while_one_runs_is_409(self, world) -> None:
        service = world.build()
        _request(service)
        with pytest.raises(ExportAlreadyRunningError):
            _request(service)

    def test_the_fourth_request_in_24_hours_is_429_failed_ones_count(self, world) -> None:
        service = world.build()
        for _ in range(3):
            created = _request(service)
            world.exports.update_fields(created.key or "", {"status": "failed"})
        with pytest.raises(RateLimitError):
            _request(service)
        world.clock.now = NOW + timedelta(hours=25)
        assert _request(service).status == "pending"


class TestTheRun:
    def test_the_archive_is_stored_and_served_until_it_expires(self, world) -> None:
        service = world.build()
        created = _request(service)

        done = run_async(service.run_export(created.key or ""))

        assert done is not None and done.status == "completed"
        assert done.storage_key == f"t/t-1/tenant_export/{created.key}.zip"
        assert done.counts["collections/sites.jsonl"] == 2
        assert done.expires_at == NOW + timedelta(hours=72)
        assert service.prepare_download(
            created.key or "",
            authenticated_with_api_key=False,
            requester=LEAD,
            origin="tenant_management",
            slug="garden",
        )
        with pytest.raises(ForbiddenError):  # a member without lead + management
            service.prepare_download(
                created.key or "",
                authenticated_with_api_key=False,
                requester=GROWER,
                origin="tenant_management",
                slug="garden",
            )
        with pytest.raises(NotFoundError):  # a platform admin who did not request it
            service.prepare_download(
                created.key or "",
                authenticated_with_api_key=False,
                requester=ADMIN,
                origin="platform_admin",
                tenant_key="t-1",
            )

        world.clock.now = NOW + timedelta(hours=73)
        with pytest.raises(NotFoundError):  # AK-35
            service.prepare_download(
                created.key or "",
                authenticated_with_api_key=False,
                requester=LEAD,
                origin="tenant_management",
                slug="garden",
            )
        result = run_async(service.expire())
        assert result["expired"] == 1
        assert world.storage.objects == {}
        assert world.exports.rows[created.key or ""].status == "expired"

    def test_an_archive_past_the_quota_plus_ten_percent_fails_too_large(self, world) -> None:
        world.entitlements.storage_mb = 1  # 1.1 MB allowed
        service = world.build(_Store(payload=1024 * 1024))  # random hex: ~1 MB per row after deflate
        created = _request(service)

        done = run_async(service.run_export(created.key or ""))

        assert done is not None and done.status == "failed" and done.failure_reason == "too_large"
        assert world.storage.objects == {}  # no partial archive
        # AK-44 — the failed request still counts for the daily limit.
        assert world.exports.count_requested_since(tenant_key="t-1", since=NOW - timedelta(hours=1)) == 1

    def test_a_stale_run_is_ended_so_the_tenant_is_not_blocked(self, world) -> None:
        service = world.build()
        created = _request(service)
        world.clock.now = NOW + timedelta(hours=7)

        run_async(service.expire())

        assert world.exports.rows[created.key or ""].status == "failed"
        assert _request(service).status == "pending"


class TestImportRefusals:
    def test_only_a_platform_admin_imports(self, world) -> None:
        with pytest.raises(ForbiddenError):
            world.build().request_import(
                io.BytesIO(b"not a zip"),
                size_bytes=9,
                requester=LEAD,
                authenticated_with_api_key=False,
                member_mapping={},
                plan_key=None,
                factors=StepUpFactors(password="right"),
                client_ip=None,
            )

    def test_an_upload_that_is_no_archive_is_422_after_the_step_up(self, world) -> None:
        with pytest.raises(TenantImportRefusedError) as refused:
            world.build().request_import(
                io.BytesIO(b"not a zip"),
                size_bytes=9,
                requester=ADMIN,
                authenticated_with_api_key=False,
                member_mapping={},
                plan_key=None,
                factors=StepUpFactors(password="right"),
                client_ip=None,
            )
        assert refused.value.error_code == "IMPORT_FORMAT_UNSUPPORTED"
        assert world.step_up.calls[0]["action"] == "tenant_import"


# ── PR #2267 security review ─────────────────────────────────────────

SIGNING_KEY = b"k" * 32


def _archive_bytes(
    *,
    signing_key: bytes | None = SIGNING_KEY,
    members: list[dict[str, Any]] | None = None,
    attachments: list[dict[str, Any]] | None = None,
    objects: dict[str, bytes] | None = None,
    plants: list[dict[str, Any]] | None = None,
) -> bytes:
    from app.domain.engines.tenant_export_engine import TenantArchiveWriter

    buffer = io.BytesIO()
    writer = TenantArchiveWriter(buffer, max_bytes=None)
    writer.write_json("tenant.json", {"name": "Garden", "slug": "garden"})
    writer.write_lines("collections/sites.jsonl", [[{"_key": "s1", "tenant_key": "t-src"}]])
    if attachments:
        writer.write_lines("collections/attachments.jsonl", [attachments])
    if plants:
        writer.write_lines("collections/plant_instances.jsonl", [plants])
    writer.write_lines(
        "members.jsonl",
        [
            members
            or [{"user_key": "old-lead", "role": "lead", "admin_scopes": ["management"], "joined_at": "2026-01-01"}]
        ],
    )
    for path, data in (objects or {}).items():
        writer.write_object(path, data)
    writer.finish({"format": "kamerplanter-tenant-export/1", "source_tenant_key": "t-src"}, signing_key=signing_key)
    return buffer.getvalue()


def _import(service: TenantExportService, data: bytes, mapping: dict[str, Any] | None = None, **kw: Any):
    return service.request_import(
        io.BytesIO(data),
        size_bytes=len(data),
        requester=ADMIN,
        authenticated_with_api_key=False,
        member_mapping=mapping if mapping is not None else {},
        plan_key=kw.pop("plan_key", None),
        factors=StepUpFactors(password=kw.pop("password", "right")),
        client_ip=None,
    )


class TestTheArchiveIsAuthenticated:
    """SEC-003 — checksums detect corruption; only this installation's signature makes an archive verified."""

    def test_an_archive_this_installation_signed_is_verified(self, world) -> None:
        created = _import(world.build(signing_key=SIGNING_KEY), _archive_bytes())
        assert created.verified is True

    @pytest.mark.parametrize("signed_with", [None, b"another-installation-key-xxxxxxxx"])
    def test_an_unsigned_or_foreign_archive_is_imported_unverified(self, world, signed_with) -> None:
        created = _import(world.build(signing_key=SIGNING_KEY), _archive_bytes(signing_key=signed_with))
        assert created.verified is False

    def test_the_role_is_the_one_the_admin_confirms_not_the_archives(self, world) -> None:
        mapping = {"old-lead": {"email": "lead@example.com", "role": "viewer", "admin_scopes": []}}
        created = _import(world.build(signing_key=SIGNING_KEY), _archive_bytes(), mapping)
        grant = created.member_grants["old-lead"]
        assert (grant.account_key, grant.role, grant.admin_scopes) == ("u-lead", TenantRole.VIEWER, [])

    def test_a_mapping_without_a_valid_role_is_refused(self, world) -> None:
        with pytest.raises(TenantImportRefusedError) as refused:
            _import(world.build(), _archive_bytes(), {"old-lead": {"email": "lead@example.com", "role": "owner"}})
        assert refused.value.error_code == "IMPORT_MEMBER_NOT_FOUND"


class TestTheStepUpComesFirstAndNamesTheArchive:
    """SEC-008/SEC-009 — no byte of an upload is parsed before the step-up, which is bound to its hash."""

    def test_the_target_is_the_uploads_hash(self, world) -> None:
        import hashlib

        data = _archive_bytes()
        _import(world.build(), data)
        assert world.step_up.calls[-1]["target"] == "archive:" + hashlib.sha256(data).hexdigest()[:32]

    def test_a_failed_step_up_answers_before_the_upload_is_parsed(self, world) -> None:
        with pytest.raises(UnauthorizedError):
            _import(world.build(), b"not a zip at all", password="wrong")


class TestImportedObjectsAreChecked:
    """SEC-010 — every object belongs to an attachment of the archive with a type the target accepts."""

    def _attachment(self, mime: str) -> dict[str, Any]:
        return {
            "_key": "a1",
            "tenant_key": "t-src",
            "storage_key": "t/t-src/plant/2026/10/a1.bin",
            "mime_type": mime,
            "category": "plant",
        }

    def test_an_svg_is_refused_even_when_the_whitelist_has_it(self, world) -> None:
        service = world.build(allowed_mime_types=lambda category: ["image/jpeg", "image/svg+xml"])
        data = _archive_bytes(
            attachments=[self._attachment("image/svg+xml")], objects={"plant/2026/10/a1.bin": b"<svg/>"}
        )
        with pytest.raises(TenantImportRefusedError):
            _import(service, data)

    def test_an_object_no_attachment_names_is_refused(self, world) -> None:
        data = _archive_bytes(objects={"plant/2026/10/stray.bin": b"x"})
        with pytest.raises(TenantImportRefusedError):
            _import(world.build(allowed_mime_types=lambda category: ["image/jpeg"]), data)


class TestDownloadsArePeopleAndAudited:
    """SEC-006 — listing and downloading an archive is never done with an API key, and every download is audited."""

    def test_an_api_key_cannot_list_or_download(self, world) -> None:
        service = world.build()
        created = _request(service)
        run_async(service.run_export(created.key or ""))
        with pytest.raises(ForbiddenError):
            service.list_exports(
                requester=LEAD,
                authenticated_with_api_key=True,
                origin="tenant_management",
                slug="garden",
                offset=0,
                limit=10,
            )
        with pytest.raises(ForbiddenError):
            service.prepare_download(
                created.key or "",
                requester=LEAD,
                authenticated_with_api_key=True,
                origin="tenant_management",
                slug="garden",
            )

    def test_a_download_is_audited(self, world) -> None:
        service = world.build()
        created = _request(service)
        run_async(service.run_export(created.key or ""))
        service.prepare_download(
            created.key or "",
            requester=LEAD,
            authenticated_with_api_key=False,
            origin="tenant_management",
            slug="garden",
        )
        assert world.audit.rows[-1]["action"] == SecurityAuditAction.TENANT_EXPORT_DOWNLOADED
        assert world.audit.rows[-1]["tenant_key"] == "t-1"


class TestADeadImportIsSwept:
    """SEC-007 — an import whose run died leaves no half tenant and no upload behind."""

    def test_the_sweep_erases_the_half_tenant_and_the_upload(self, world) -> None:
        world.storage.objects["tenant-imports/imp-x.zip"] = b"zip"
        world.imports.rows["imp-x"] = TenantImportRequest.model_validate(
            {
                "_key": "imp-x",
                "requested_by_user_key": "u-admin",
                "status": "running",
                "source_format": "kamerplanter-tenant-export/1",
                "target_tenant_key": "t-half",
                "upload_storage_key": "tenant-imports/imp-x.zip",
                "requested_at": NOW,
                "updated_at": NOW,
            }
        )
        world.clock.now = NOW + timedelta(hours=7)

        result = run_async(world.build().expire())

        assert result["abandoned_imports"] == 1
        assert world.tenant_service.erased == ["t-half"]
        assert "tenant-imports/imp-x.zip" not in world.storage.objects
        assert world.imports.rows["imp-x"].status == "failed"
        assert world.imports.rows["imp-x"].failure_reason == "IMPORT_ABANDONED"


# ── PR #2267 security review, round 2 ────────────────────────────────


def _archive_with_sites_part(data: bytes, *, compression: int) -> bytes:
    """A well-formed, unsigned archive whose ``collections/sites.jsonl`` is *data* (true hashes in the manifest)."""
    import hashlib
    import json
    import zipfile

    tenant = json.dumps({"name": "Garden", "slug": "garden"}).encode()
    files = {
        "tenant.json": {"rows": 1, "sha256": hashlib.sha256(tenant).hexdigest()},
        "collections/sites.jsonl": {"rows": 0, "sha256": hashlib.sha256(data).hexdigest()},
    }
    manifest = json.dumps({"format": "kamerplanter-tenant-export/1", "source_tenant_key": "t-src", "files": files})
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as out:
        out.writestr("manifest.json", manifest, compress_type=zipfile.ZIP_DEFLATED)
        out.writestr("tenant.json", tenant, compress_type=zipfile.ZIP_DEFLATED)
        out.writestr("collections/sites.jsonl", data, compress_type=compression)
    return buffer.getvalue()


@pytest.fixture
def no_row_is_parsed(monkeypatch):
    """Fails the test the moment a row of a collection part reaches the JSON parser."""
    import app.domain.engines.tenant_export_engine as engine

    real = engine._loads

    def guarded(data: bytes, part: str, *rest: Any):
        if part.startswith("collections/"):
            raise AssertionError(f"a row was parsed before the archive was bounded: {part}")
        return real(data, part, *rest)

    monkeypatch.setattr(engine, "_loads", guarded)


class TestADecompressionBombIsRefusedBeforeItIsParsed:
    """SEC-R2-01 — the upload is small; what it unpacks to is bounded before a row is parsed."""

    def test_25_mib_of_empty_objects_deflated_is_refused_by_its_ratio(self, world, no_row_is_parsed) -> None:
        bomb = _archive_with_sites_part(b"{}\n" * (25 * 1024 * 1024 // 3), compression=8)  # ZIP_DEFLATED
        assert len(bomb) < 200 * 1024  # what the admin uploads: well under every upload limit

        with pytest.raises(TenantImportRefusedError) as refused:
            _import(world.build(), bomb)

        assert refused.value.error_code == "IMPORT_FORMAT_UNSUPPORTED"
        assert "compression ratio" in str(refused.value)
        assert world.imports.rows == {}

    def test_a_part_of_too_many_rows_is_refused_before_it_is_split(self, world, no_row_is_parsed) -> None:
        # Stored, not deflated: no ratio to catch, under 1 MiB, and still 300 001 dicts once parsed.
        flood = _archive_with_sites_part(b"{}\n" * 300_001, compression=0)  # ZIP_STORED

        with pytest.raises(TenantImportRefusedError) as refused:
            _import(world.build(), flood)

        assert refused.value.error_code == "IMPORT_FORMAT_UNSUPPORTED"
        assert "more than 250000 rows" in str(refused.value)


class TestTheSmallerRoundTwoFindings:
    def test_a_stale_export_takes_its_stored_archive_with_it(self, world) -> None:
        """I4 — a run that died after storing the archive leaves no object behind the failed request."""
        service = world.build()
        created = _request(service)
        stale = world.exports.update_fields(created.key or "", {"status": "running", "updated_at": NOW})
        assert stale is not None
        world.storage.objects[service.storage_key_of(stale)] = b"PK partial"
        world.clock.now = NOW + timedelta(hours=7)

        run_async(service.expire())

        assert service.storage_key_of(stale) not in world.storage.objects
        assert world.exports.rows[created.key or ""].status == "failed"

    def test_the_import_state_is_never_read_with_an_api_key(self, world) -> None:
        """I6 — like every other route of the export and import, the import's state is for a person."""
        created = _import(world.build(), _archive_bytes())
        with pytest.raises(ForbiddenError):
            world.build().get_import(created.key or "", requester=ADMIN, authenticated_with_api_key=True)
        assert world.build().get_import(created.key or "", requester=ADMIN).key == created.key

    def test_a_deactivated_account_is_no_member_to_map(self, world) -> None:
        """I8 — the mapping refuses an account that can no longer sign in."""
        inactive = LEAD.model_copy(update={"is_active": False})
        service = world.build()
        service._users = _Users(inactive, ADMIN)
        with pytest.raises(TenantImportRefusedError) as refused:
            _import(service, _archive_bytes(), {"old-lead": {"email": "lead@example.com", "role": "lead"}})
        assert refused.value.error_code == "IMPORT_MEMBER_NOT_FOUND"

    def test_a_refused_import_is_audited_with_the_archives_hash(self, world) -> None:
        """I9 — who tried which archive, and why it was refused."""
        import hashlib

        data = _archive_bytes()
        with pytest.raises(TenantImportRefusedError):
            _import(world.build(), data, {"old-lead": {"email": "nobody@example.com", "role": "lead"}})
        row = world.audit.rows[-1]
        assert row["action"] == SecurityAuditAction.TENANT_IMPORT_REQUESTED
        assert row["outcome"] == "refused:IMPORT_MEMBER_NOT_FOUND"
        assert row["archive_sha256"] == hashlib.sha256(data).hexdigest()

    def test_a_half_tenant_the_sweep_cannot_erase_yet_keeps_its_request(self, world) -> None:
        """SEC-R2-03 — ending the request before its tenant is gone would leave rows no sweep finds."""
        world.tenants.by_key["t-half"] = Tenant(
            _key="t-half", name="Half", slug="half", owner_user_key="u-admin", status=TenantStatus.IMPORTING
        )
        world.tenant_service.erasable = False  # e.g. the tenant erasure is not configured on this replica
        world.imports.rows["imp-y"] = TenantImportRequest.model_validate(
            {
                "_key": "imp-y",
                "requested_by_user_key": "u-admin",
                "status": "cleanup_pending",
                "failure_reason": "IMPORT_FAILED",
                "source_format": "kamerplanter-tenant-export/1",
                "target_tenant_key": "t-half",
                "requested_at": NOW,
                "updated_at": NOW,
            }
        )

        result = run_async(world.build().expire())

        assert result["abandoned_imports"] == 0
        kept = world.imports.rows["imp-y"]
        assert (kept.status, kept.target_tenant_key) == ("cleanup_pending", "t-half")

        world.tenant_service.erasable = True
        del world.tenants.by_key["t-half"]  # what the erasure does to the tenant
        run_async(world.build().expire())
        ended = world.imports.rows["imp-y"]
        assert (ended.status, ended.target_tenant_key, ended.failure_reason) == ("failed", None, "IMPORT_FAILED")


class TestOneLongLineIsNotOneCheapRow:
    """R3-02 — the row bound counts lines; the bytes of a line and the values of the archive are bounded too."""

    def test_a_25_mib_line_is_refused_before_it_is_parsed(self, world, no_row_is_parsed) -> None:
        line = b'{"_key":"x","tenant_key":"t-src","a":[' + b"{}," * (25 * 1024 * 1024 // 3) + b"{}]}\n"
        data = _archive_with_sites_part(line, compression=0)  # ZIP_STORED: no ratio to catch it

        with pytest.raises(TenantImportRefusedError) as refused:
            _import(world.build(), data)

        assert "longer than 1048576 bytes" in str(refused.value)

    def test_the_values_of_all_lines_together_are_bounded(self, world, monkeypatch) -> None:
        import json

        import app.domain.engines.tenant_export_engine as engine

        monkeypatch.setattr(engine, "MAX_JSON_NODES", 1000)
        rows = b"".join(
            json.dumps({"_key": f"s{i}", "tenant_key": "t-src", "a": list(range(100))}).encode() + b"\n"
            for i in range(20)
        )

        with pytest.raises(TenantImportRefusedError) as refused:
            _import(world.build(), _archive_with_sites_part(rows, compression=0))

        assert "too many JSON values" in str(refused.value)


# ── REQ-056 §8.4 step 6 (AK-46): the target plan's quotas before anything is written ──

MIB = 1024 * 1024
JPEG = "image/jpeg"


def _quota_service(world, **limits: int | None) -> tuple[TenantExportService, InMemoryPlanRepository]:
    """The export service on the real ``EntitlementService``; the plan ``small`` carries *limits*."""
    plans = InMemoryPlanRepository([standard_plan(), Plan(_key="small", name="Small", limits=PlanLimits(**limits))])
    service = world.build(allowed_mime_types=lambda category: [JPEG])
    service._entitlements = EntitlementService(
        plan_repo=plans,
        tenant_repo=None,
        # The instance settings of the default plan: room for everything the archives below hold.
        instance_overrides={
            EntitlementDimension.MEMBERS: 50,
            EntitlementDimension.STORAGE_MB: 100,
            EntitlementDimension.PHOTOS_PER_INSTANCE: 50,
        },
    )
    return service, plans


def _photo(key: str, *, data: bytes | None = None, byte_size: int = 10, storage: str | None = None) -> dict[str, Any]:
    return {
        "_key": key,
        "tenant_key": "t-src",
        "storage_key": f"t/t-src/plant/2026/10/{storage or key}.jpg",
        "mime_type": JPEG,
        "category": "plant",
        "byte_size": byte_size,
    }


def _plant(key: str, photos: list[str]) -> dict[str, Any]:
    return {"_key": key, "tenant_key": "t-src", "photo_refs": photos, "cover_photo_ref": photos[0] if photos else None}


#: The archive's member confirmed lead + management: the owner is the mapped account, not the acting admin.
OWNER_MAPPING = {"old-lead": {"email": "lead@example.com", "role": "lead", "admin_scopes": ["management"]}}
#: The same member as a viewer: the acting admin becomes the owner as well — two accounts.
VIEWER_MAPPING = {"old-lead": {"email": "lead@example.com", "role": "viewer", "admin_scopes": []}}


class TestTheTargetPlansQuotasAreCheckedBeforeTheWrite:
    """The new tenant does not exist yet; the archive is held against the plan the import founds it on."""

    def _refused(self, world, service: TenantExportService, data: bytes, mapping: dict[str, Any], error: type) -> Any:
        with pytest.raises(error) as refused:
            _import(service, data, mapping, plan_key="small")
        # Nothing is written: no request, no stored upload; the refusal is audited with the dimension's code.
        assert world.imports.rows == {}
        assert world.storage.objects == {}
        assert world.audit.rows[-1]["outcome"] == f"refused:{refused.value.error_code}"
        return refused.value

    def test_more_accounts_than_the_plan_admits_are_refused_with_member_limit_reached(self, world) -> None:
        service, _ = _quota_service(world, members=1)

        refused = self._refused(world, service, _archive_bytes(), VIEWER_MAPPING, MemberLimitReachedError)

        assert (refused.error_code, refused.status_code) == ("MEMBER_LIMIT_REACHED", 422)

    def test_the_owner_from_the_archive_is_one_account_the_plan_admits(self, world) -> None:
        service, _ = _quota_service(world, members=1)

        created = _import(service, _archive_bytes(), OWNER_MAPPING, plan_key="small")

        assert created.plan_key == "small"

    def test_more_bytes_than_the_plan_holds_are_refused_with_storage_quota_exceeded(self, world) -> None:
        # The archive claims 10 bytes; the object it carries is what the quota counts (I7).
        data = _archive_bytes(attachments=[_photo("a1")], objects={"plant/2026/10/a1.jpg": os.urandom(MIB + 1)})
        service, _ = _quota_service(world, storage_mb=1)

        refused = self._refused(world, service, data, {}, StorageQuotaExceededError)

        assert (refused.error_code, refused.status_code) == ("STORAGE_QUOTA_EXCEEDED", 409)

    def test_exactly_the_plans_bytes_are_admitted_and_shared_bytes_are_charged_once(self, world) -> None:
        # Two records on one deduplicated object (#1770) are one charge, as the storage quota counts them.
        rows = [_photo("a1"), _photo("a2", storage="a1")]
        data = _archive_bytes(attachments=rows, objects={"plant/2026/10/a1.jpg": os.urandom(MIB)})
        service, _ = _quota_service(world, storage_mb=1)

        assert _import(service, data, {}, plan_key="small").plan_key == "small"

    def test_a_record_without_its_object_is_charged_its_stated_size(self, world) -> None:
        data = _archive_bytes(attachments=[_photo("a1", byte_size=2 * MIB)])
        service, _ = _quota_service(world, storage_mb=1)

        self._refused(world, service, data, {}, StorageQuotaExceededError)

    def test_a_plant_with_more_photos_than_the_plan_admits_is_refused_with_photo_quota_exceeded(self, world) -> None:
        photos = [_photo(f"a{i}") for i in range(3)]
        data = _archive_bytes(attachments=photos, plants=[_plant("p-big", ["a0", "a1", "a2"]), _plant("p-1", ["a0"])])
        service, _ = _quota_service(world, photos_per_instance=2)

        refused = self._refused(world, service, data, {}, PhotoQuotaExceededError)

        assert (refused.error_code, refused.status_code) == ("PHOTO_QUOTA_EXCEEDED", 409)
        assert "p-big" in refused.details[0]["reason"]

    def test_a_gallery_as_long_as_the_plan_admits_is_imported(self, world) -> None:
        photos = [_photo(f"a{i}") for i in range(3)]
        data = _archive_bytes(attachments=photos, plants=[_plant("p-big", ["a0", "a1", "a2"])])
        service, _ = _quota_service(world, photos_per_instance=3)

        assert _import(service, data, {}, plan_key="small").plan_key == "small"

    @pytest.mark.parametrize(
        ("limits", "mapping", "code"),
        [
            ({"members": 1}, VIEWER_MAPPING, "MEMBER_LIMIT_REACHED"),
            ({"storage_mb": 1}, {}, "STORAGE_QUOTA_EXCEEDED"),
        ],
    )
    def test_a_plan_lowered_after_the_request_ends_the_run_before_the_tenant_is_founded(
        self, world, limits: dict[str, int], mapping: dict[str, Any], code: str
    ) -> None:
        """The run checks again: the plan may have changed since the request; nothing is founded or written."""
        data = _archive_bytes(attachments=[_photo("a1")], objects={"plant/2026/10/a1.jpg": os.urandom(MIB + 1)})
        service, plans = _quota_service(world)
        accepted = _import(service, data, mapping, plan_key="small")
        plans.plans["small"] = Plan(_key="small", name="Small", limits=PlanLimits(**limits))

        finished = run_async(service.run_import(accepted.key or ""))

        assert finished is not None
        assert (finished.status, finished.failure_reason, finished.target_tenant_key) == ("failed", code, None)
        assert not any(key.startswith("t/") for key in world.storage.objects)
        assert world.audit.rows[-1]["outcome"] == f"failed:{code}"
