"""The four global routers of #1501 refuse a member who is not entitled to write.

Four routers mounted on the **global** ``api_router`` exposed write routes behind
``get_current_user`` and nothing more. `#1501` names the ``DELETE``s; the sweep of
all their methods found twenty more writes of the same shape — every ``POST`` and
``PUT`` on the phase-sequence and IPM catalogues — plus, on the import router, a
pair of unscoped reads.

## What each file here proves, and why a service test could not

Each route is driven through FastAPI so the **route's own dependency chain** is
what refuses. That is the half a service test cannot reach and the half that was
actually missing: the services re-gate nothing on their own until they are handed
a flag, so a gate present in the service and absent on the route is inert, and a
gate present on the route and absent in the service is one caller away from being
inert. The service-level decisions are pinned in :class:`TestImportServiceDecides`
and :class:`TestTheSignaturesRefuseAnOmission` at the bottom of this file, and for
the #1110 import gate in
``tests/unit/domain/services/test_import_tenant_scoping.py``.

## Real vs doubled

**Real**: the four routers, their dependency graphs, and the error handler that
shapes the refusal. **Doubled**: the services, as recorders — a real service would
need a database, and what is under test is which caller the route admits and what
it hands over.

Every test in this file is red against the pre-#1501 routers: the catalogue routes
answered 200/201/204 for any authenticated caller, and the import routes answered
for any tenant's job.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.imports.router import router as imports_router
from app.api.v1.ipm.router import router as ipm_router
from app.api.v1.phase_sequences.router import router as phase_sequences_router
from app.common import auth as auth_mod
from app.common.dependencies import get_import_service, get_ipm_service, get_phase_sequence_service
from app.common.enums import DuplicateStrategy, EntityType, ImportJobStatus, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import ForbiddenError, KamerplanterError, NotFoundError
from app.domain.models.import_job import ImportJob
from app.domain.models.ipm import Disease, Pest, Treatment
from app.domain.models.phase_sequence import PhaseDefinition, PhaseSequence, PhaseSequenceEntry
from app.domain.models.tenant_context import TenantContext
from app.domain.services.import_service import ImportService

_TENANT = "tenant_acme"
_OTHER_TENANT = "tenant_rival"


def _user() -> SimpleNamespace:
    return SimpleNamespace(key="user_1")


def _app(router, service_dependency, service, *, platform_admin: bool, role: TenantRole) -> FastAPI:
    """Mount one router with a doubled service and a caller of the given standing.

    ``require_platform_admin`` is **not** overridden: it is the dependency under
    test, and overriding it would leave every assertion below measuring a stub. It
    is driven through its own input instead — ``auth_mod.is_platform_admin``, the
    single function both it and ``get_is_platform_admin`` call — so the route gate
    and the flag the handler threads to the service can never be told apart here
    while disagreeing in production.
    """
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[auth_mod.get_current_user] = _user
    app.dependency_overrides[service_dependency] = lambda: service
    app.dependency_overrides[auth_mod.get_tenant_service] = lambda: SimpleNamespace()
    app.dependency_overrides[auth_mod.get_active_tenant_context] = lambda: TenantContext(
        tenant_key=_TENANT,
        tenant_slug="acme",
        user_key="user_1",
        role=role,
        admin_scopes=[],
    )
    return app


@pytest.fixture
def platform_admin_flag(monkeypatch: pytest.MonkeyPatch):
    """Set what ``is_platform_admin`` answers, for the whole dependency graph at once."""

    def _set(value: bool) -> None:
        monkeypatch.setattr(auth_mod, "is_platform_admin", lambda _svc, _key: value)

    return _set


# ─────────────────────────── phase sequences ───────────────────────────


class _RecordingPhaseSequenceService:
    """Records the flag each write was handed; answers reads with a stub row."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def _record(self, name: str, is_platform_admin: bool) -> None:
        self.calls.append((name, is_platform_admin))

    # writes
    def create_definition(self, defn, *, is_platform_admin):
        self._record("create_definition", is_platform_admin)
        return PhaseDefinition(_key="pd1", name=defn.name)

    def update_definition(self, key, data, *, is_platform_admin):
        self._record("update_definition", is_platform_admin)
        return PhaseDefinition(_key=key, name="vegetative")

    def delete_definition(self, key, *, is_platform_admin):
        self._record("delete_definition", is_platform_admin)
        return True

    def create_sequence(self, seq, *, is_platform_admin):
        self._record("create_sequence", is_platform_admin)
        return PhaseSequence(_key="ps1", name=seq.name)

    def update_sequence(self, key, data, *, is_platform_admin):
        self._record("update_sequence", is_platform_admin)
        return PhaseSequence(_key=key, name="standard")

    def delete_sequence(self, key, *, is_platform_admin):
        self._record("delete_sequence", is_platform_admin)
        return True

    def clone_sequence(self, source_key, new_name, *, is_platform_admin):
        self._record("clone_sequence", is_platform_admin)
        return PhaseSequence(_key="ps2", name=new_name)

    def create_entry(self, entry, *, is_platform_admin):
        self._record("create_entry", is_platform_admin)
        return PhaseSequenceEntry(_key="pse1", phase_sequence_key="ps1", phase_definition_key="pd1")

    def update_entry(self, key, data, *, is_platform_admin):
        self._record("update_entry", is_platform_admin)
        return PhaseSequenceEntry(_key=key, phase_sequence_key="ps1", phase_definition_key="pd1")

    def delete_entry(self, key, *, is_platform_admin):
        self._record("delete_entry", is_platform_admin)
        return True

    def reorder_entries(self, seq_key, orders, *, is_platform_admin):
        self._record("reorder_entries", is_platform_admin)
        return []

    # reads the write handlers perform on the way
    def get_entry(self, key):
        return PhaseSequenceEntry(_key=key, phase_sequence_key="ps1", phase_definition_key="pd1")

    def get_sequence(self, key):
        return PhaseSequence(_key=key, name="standard")

    def get_full_sequence(self, key):
        return {"entries": []}

    def get_definition(self, key):
        return PhaseDefinition(_key=key, name="vegetative")

    def list_definitions(self, offset, limit, name_filter=None):
        return ([], 0)

    @property
    def _repo(self):  # the list route reads a usage count straight off it
        return SimpleNamespace(get_definition_usage_count=lambda key: 0)


#: Every write the phase-sequence router mounts, as
#: ``(method, path, json body, expected success code, service method)``.
#:
#: Written out per route rather than derived from the router, because a table
#: derived from the thing under test cannot notice a route disappearing from it.
_PHASE_SEQUENCE_WRITES = [
    ("POST", "/api/v1/phase-definitions", {"name": "veg"}, 201, "create_definition"),
    ("PUT", "/api/v1/phase-definitions/pd1", {"name": "veg2"}, 200, "update_definition"),
    ("DELETE", "/api/v1/phase-definitions/pd1", None, 204, "delete_definition"),
    ("POST", "/api/v1/phase-sequences", {"name": "std"}, 201, "create_sequence"),
    ("PUT", "/api/v1/phase-sequences/ps1", {"name": "std2"}, 200, "update_sequence"),
    ("DELETE", "/api/v1/phase-sequences/ps1", None, 204, "delete_sequence"),
    ("POST", "/api/v1/phase-sequences/ps1/clone", {"new_name": "copy"}, 201, "clone_sequence"),
    (
        "POST",
        "/api/v1/phase-sequences/ps1/entries",
        {"phase_definition_key": "pd1", "sequence_order": 0},
        201,
        "create_entry",
    ),
    ("PUT", "/api/v1/phase-sequences/ps1/entries/pse1", {"sequence_order": 1}, 200, "update_entry"),
    ("DELETE", "/api/v1/phase-sequences/ps1/entries/pse1", None, 204, "delete_entry"),
    (
        "POST",
        "/api/v1/phase-sequences/ps1/entries/reorder",
        {"entries": [{"key": "pse1", "sequence_order": 0}]},
        200,
        "reorder_entries",
    ),
]


def _phase_sequence_client(platform_admin_flag, *, admin: bool):
    platform_admin_flag(admin)
    service = _RecordingPhaseSequenceService()
    app = _app(
        phase_sequences_router,
        get_phase_sequence_service,
        service,
        platform_admin=admin,
        role=TenantRole.GROWER,
    )
    return TestClient(app), service


class TestPhaseSequenceCatalogueIsPlatformAdminOnly:
    """Eleven writes on a catalogue with no ``tenant_key`` anywhere in its models."""

    @pytest.mark.parametrize(
        ("method", "path", "body", "_ok", "_call"),
        _PHASE_SEQUENCE_WRITES,
        ids=[f"{m}-{p}" for m, p, _b, _o, _c in _PHASE_SEQUENCE_WRITES],
    )
    def test_a_grower_of_a_tenant_is_refused(
        self, platform_admin_flag, method: str, path: str, body: Any, _ok: int, _call: str
    ) -> None:
        client, service = _phase_sequence_client(platform_admin_flag, admin=False)

        response = client.request(method, path, json=body)

        assert response.status_code == 403, response.text
        assert service.calls == [], "the gate must refuse BEFORE the service is reached"

    @pytest.mark.parametrize(
        ("method", "path", "body", "ok", "call"),
        _PHASE_SEQUENCE_WRITES,
        ids=[f"{m}-{p}" for m, p, _b, _o, _c in _PHASE_SEQUENCE_WRITES],
    )
    def test_a_platform_admin_succeeds_and_the_flag_reaches_the_service(
        self, platform_admin_flag, method: str, path: str, body: Any, ok: int, call: str
    ) -> None:
        """The other direction, and the one an over-rejecting gate fails.

        It also pins the second half of the rule: the handler must hand the SAME
        flag down, or the service's own copy of the gate is decided by a default
        nobody set.
        """
        client, service = _phase_sequence_client(platform_admin_flag, admin=True)

        response = client.request(method, path, json=body)

        assert response.status_code == ok, response.text
        assert service.calls == [(call, True)]

    def test_the_reads_stay_open_to_an_ordinary_member(self, platform_admin_flag) -> None:
        """The #706 direction: a catalogue nobody may read is as broken as one anybody may edit."""
        client, _service = _phase_sequence_client(platform_admin_flag, admin=False)

        assert client.get("/api/v1/phase-definitions").status_code == 200
        assert client.get("/api/v1/phase-definitions/pd1").status_code == 200
        assert client.get("/api/v1/phase-sequences/ps1").status_code == 200


# ─────────────────────────────── IPM ───────────────────────────────


class _RecordingIpmService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def _record(self, name, flag):
        self.calls.append((name, flag))

    def create_pest(self, pest, *, is_platform_admin):
        self._record("create_pest", is_platform_admin)
        return pest

    def update_pest(self, key, data, *, is_platform_admin):
        self._record("update_pest", is_platform_admin)
        return Pest(_key=key, scientific_name="Tetranychus urticae", common_name="Spider mite")

    def delete_pest(self, key, *, is_platform_admin):
        self._record("delete_pest", is_platform_admin)
        return True

    def create_disease(self, disease, *, is_platform_admin):
        self._record("create_disease", is_platform_admin)
        return disease

    def update_disease(self, key, data, *, is_platform_admin):
        self._record("update_disease", is_platform_admin)
        return Disease(_key=key, scientific_name="Botrytis cinerea", common_name="Grey mould", pathogen_type="fungal")

    def delete_disease(self, key, *, is_platform_admin):
        self._record("delete_disease", is_platform_admin)
        return True

    def create_treatment(self, treatment, *, is_platform_admin):
        self._record("create_treatment", is_platform_admin)
        return treatment

    def update_treatment(self, key, data, *, is_platform_admin):
        self._record("update_treatment", is_platform_admin)
        return Treatment(_key=key, name="Neem", treatment_type="biological")

    def delete_treatment(self, key, *, is_platform_admin):
        self._record("delete_treatment", is_platform_admin)
        return True

    def get_pest(self, key):
        return Pest(_key=key, scientific_name="Tetranychus urticae", common_name="Spider mite")

    def list_pests(self, offset, limit):
        return ([], 0)


_IPM_WRITES = [
    (
        "POST",
        "/api/v1/ipm/pests",
        {"scientific_name": "Aphis fabae", "common_name": "Black bean aphid"},
        201,
        "create_pest",
    ),
    ("PUT", "/api/v1/ipm/pests/p1", {"common_name": "Renamed"}, 200, "update_pest"),
    ("DELETE", "/api/v1/ipm/pests/p1", None, 204, "delete_pest"),
    (
        "POST",
        "/api/v1/ipm/diseases",
        {"scientific_name": "Podosphaera pannosa", "common_name": "Mildew", "pathogen_type": "fungal"},
        201,
        "create_disease",
    ),
    ("PUT", "/api/v1/ipm/diseases/d1", {"common_name": "Renamed"}, 200, "update_disease"),
    ("DELETE", "/api/v1/ipm/diseases/d1", None, 204, "delete_disease"),
    (
        "POST",
        "/api/v1/ipm/treatments",
        {"name": "Neem oil", "treatment_type": "biological"},
        201,
        "create_treatment",
    ),
    ("PUT", "/api/v1/ipm/treatments/t1", {"name": "Renamed"}, 200, "update_treatment"),
    ("DELETE", "/api/v1/ipm/treatments/t1", None, 204, "delete_treatment"),
]


def _ipm_client(platform_admin_flag, *, admin: bool):
    platform_admin_flag(admin)
    service = _RecordingIpmService()
    app = _app(ipm_router, get_ipm_service, service, platform_admin=admin, role=TenantRole.GROWER)
    return TestClient(app), service


class TestIpmCatalogueIsPlatformAdminOnly:
    """Nine writes on global reference data — ``ipm/tenant_router.py`` says so itself."""

    @pytest.mark.parametrize(
        ("method", "path", "body", "_ok", "_call"),
        _IPM_WRITES,
        ids=[f"{m}-{p}" for m, p, _b, _o, _c in _IPM_WRITES],
    )
    def test_a_grower_of_a_tenant_is_refused(
        self, platform_admin_flag, method: str, path: str, body: Any, _ok: int, _call: str
    ) -> None:
        client, service = _ipm_client(platform_admin_flag, admin=False)

        response = client.request(method, path, json=body)

        assert response.status_code == 403, response.text
        assert service.calls == []

    @pytest.mark.parametrize(
        ("method", "path", "body", "ok", "call"),
        _IPM_WRITES,
        ids=[f"{m}-{p}" for m, p, _b, _o, _c in _IPM_WRITES],
    )
    def test_a_platform_admin_succeeds_and_the_flag_reaches_the_service(
        self, platform_admin_flag, method: str, path: str, body: Any, ok: int, call: str
    ) -> None:
        client, service = _ipm_client(platform_admin_flag, admin=True)

        response = client.request(method, path, json=body)

        assert response.status_code == ok, response.text
        assert service.calls == [(call, True)]

    def test_the_reads_stay_open_to_an_ordinary_member(self, platform_admin_flag) -> None:
        client, _service = _ipm_client(platform_admin_flag, admin=False)

        assert client.get("/api/v1/ipm/pests/p1").status_code == 200


# ───────────────────────────── import jobs ─────────────────────────────


class _RecordingScopedImportService:
    """Records the scope/rank each import route resolved.

    Deliberately NOT a ``MagicMock``: the keyword-only arguments without defaults
    are half of what #1501 adds, and a mock accepts every signature there is. A
    real ``def`` with the real signature is what makes a route that forgot to pass
    one fail here rather than pass silently.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def upload(self, content, entity_type, filename, duplicate_strategy, uploaded_by="", *, tenant_key=""):
        self.calls.append(("upload", {"uploaded_by": uploaded_by, "tenant_key": tenant_key}))
        return ImportJob(
            _key="job1",
            entity_type=entity_type,
            status=ImportJobStatus.PREVIEW_READY,
            filename=filename,
            duplicate_strategy=duplicate_strategy,
            tenant_key=tenant_key,
            uploaded_by=uploaded_by,
        )

    def get_job(self, key, *, tenant_key=None):
        self.calls.append(("get_job", {"tenant_key": tenant_key}))
        return ImportJob(_key=key, entity_type=EntityType.SPECIES, tenant_key=tenant_key or "")

    def list_jobs(self, offset=0, limit=50, *, tenant_key=None):
        self.calls.append(("list_jobs", {"tenant_key": tenant_key}))
        return ([], 0)

    def delete_job(self, key, *, tenant_key, caller_role, is_platform_admin):
        self.calls.append(
            (
                "delete_job",
                {"tenant_key": tenant_key, "caller_role": caller_role, "is_platform_admin": is_platform_admin},
            )
        )
        return True


def _import_client(platform_admin_flag, *, role: TenantRole, admin: bool = False):
    platform_admin_flag(admin)
    service = _RecordingScopedImportService()
    app = _app(imports_router, get_import_service, service, platform_admin=admin, role=role)
    return TestClient(app), service


class TestImportJobsAreTenantScoped:
    """The import router takes the tenant axis, not the platform-admin one.

    A job is tenant-owned staged work: it carries an uploaded CSV. So the fix is a
    scope plus a rank, and the scope is the half that mattered — the three routes
    below had neither.
    """

    def test_upload_stamps_the_callers_tenant_and_user(self, platform_admin_flag) -> None:
        client, service = _import_client(platform_admin_flag, role=TenantRole.GROWER)

        response = client.post(
            "/api/v1/import/upload",
            files={"file": ("rows.csv", b"scientific_name\nRosa canina\n", "text/csv")},
            data={"entity_type": EntityType.SPECIES.value, "duplicate_strategy": DuplicateStrategy.SKIP.value},
        )

        assert response.status_code == 202, response.text
        assert service.calls == [("upload", {"uploaded_by": "user_1", "tenant_key": _TENANT})]

    def test_a_viewer_may_not_stage_an_import(self, platform_admin_flag) -> None:
        client, service = _import_client(platform_admin_flag, role=TenantRole.VIEWER)

        response = client.post(
            "/api/v1/import/upload",
            files={"file": ("rows.csv", b"scientific_name\nRosa canina\n", "text/csv")},
            data={"entity_type": EntityType.SPECIES.value, "duplicate_strategy": DuplicateStrategy.SKIP.value},
        )

        assert response.status_code == 403, response.text
        assert service.calls == []

    def test_reading_one_job_is_scoped_to_the_callers_tenant(self, platform_admin_flag) -> None:
        client, service = _import_client(platform_admin_flag, role=TenantRole.VIEWER)

        assert client.get("/api/v1/import/jobs/job1").status_code == 200
        assert service.calls == [("get_job", {"tenant_key": _TENANT})]

    def test_listing_jobs_is_scoped_to_the_callers_tenant(self, platform_admin_flag) -> None:
        client, service = _import_client(platform_admin_flag, role=TenantRole.VIEWER)

        assert client.get("/api/v1/import/jobs").status_code == 200
        assert service.calls == [("list_jobs", {"tenant_key": _TENANT})]

    def test_delete_hands_the_service_the_scope_and_the_rank(self, platform_admin_flag) -> None:
        client, service = _import_client(platform_admin_flag, role=TenantRole.LEAD)

        assert client.delete("/api/v1/import/jobs/job1").status_code == 204
        assert service.calls == [
            (
                "delete_job",
                {"tenant_key": _TENANT, "caller_role": TenantRole.LEAD, "is_platform_admin": False},
            )
        ]


# ───────────────── the service decisions, not the wiring ─────────────────


def _import_service_with(job: ImportJob) -> tuple[ImportService, Any]:
    class _Repo:
        def __init__(self) -> None:
            self.deleted: list[str] = []

        def get_or_raise(self, key):
            return job

        def delete(self, key):
            self.deleted.append(key)
            return True

    repo = _Repo()
    return ImportService(repo), repo


class TestImportServiceDecides:
    """The service's own arms, driven directly — the half a route test cannot isolate."""

    def test_a_foreign_job_is_404_not_403(self) -> None:
        service, repo = _import_service_with(
            ImportJob(_key="job1", entity_type=EntityType.SPECIES, tenant_key=_OTHER_TENANT)
        )

        with pytest.raises(NotFoundError):
            service.delete_job("job1", tenant_key=_TENANT, caller_role=TenantRole.LEAD, is_platform_admin=False)

        assert repo.deleted == []

    def test_a_grower_may_not_delete_their_own_tenants_job(self) -> None:
        service, repo = _import_service_with(ImportJob(_key="job1", entity_type=EntityType.SPECIES, tenant_key=_TENANT))

        with pytest.raises(ForbiddenError):
            service.delete_job("job1", tenant_key=_TENANT, caller_role=TenantRole.GROWER, is_platform_admin=False)

        assert repo.deleted == []

    def test_a_lead_deletes_their_own_tenants_job(self) -> None:
        service, repo = _import_service_with(ImportJob(_key="job1", entity_type=EntityType.SPECIES, tenant_key=_TENANT))

        assert (
            service.delete_job("job1", tenant_key=_TENANT, caller_role=TenantRole.LEAD, is_platform_admin=False) is True
        )
        assert repo.deleted == ["job1"]

    def test_a_platform_admin_bypasses_the_rank_but_not_the_scope(self) -> None:
        """Both halves in one test, because they are one decision.

        The platform admin bypasses the *rank* on their own tenant's job and is
        still refused a *foreign* one with a 404 — ownership hiding does not have a
        privileged exception, and an admin arm that also skipped the scope would
        turn the 404 into a cross-tenant read.
        """
        own, own_repo = _import_service_with(ImportJob(_key="job1", entity_type=EntityType.SPECIES, tenant_key=_TENANT))
        assert own.delete_job("job1", tenant_key=_TENANT, caller_role=TenantRole.VIEWER, is_platform_admin=True) is True
        assert own_repo.deleted == ["job1"]

        foreign, foreign_repo = _import_service_with(
            ImportJob(_key="job1", entity_type=EntityType.SPECIES, tenant_key=_OTHER_TENANT)
        )
        with pytest.raises(NotFoundError):
            foreign.delete_job("job1", tenant_key=_TENANT, caller_role=TenantRole.LEAD, is_platform_admin=True)
        assert foreign_repo.deleted == []

    def test_the_system_context_stays_ungated(self) -> None:
        """A gate that also stopped the seeders would be a regression in a fix's clothes."""
        service, repo = _import_service_with(ImportJob(_key="job1", entity_type=EntityType.SPECIES, tenant_key=_TENANT))

        assert service.delete_job("job1", tenant_key=None, caller_role=None, is_platform_admin=False) is True
        assert repo.deleted == ["job1"]


class TestTheSignaturesRefuseAnOmission:
    """The keyword-only-without-default half, asserted as behaviour rather than prose.

    A caller that forgets the authorisation argument must not inherit permission.
    This is the same claim ``delete_job``'s docstring makes, checked — the pattern
    #1441 exists to prevent is an authorisation claim living only in a comment.
    """

    def test_delete_job_refuses_a_call_that_omits_the_context(self) -> None:
        service, _repo = _import_service_with(
            ImportJob(_key="job1", entity_type=EntityType.SPECIES, tenant_key=_TENANT)
        )

        with pytest.raises(TypeError):
            service.delete_job("job1")  # type: ignore[call-arg]

    @pytest.mark.parametrize(
        ("method", "args"),
        [
            ("create_definition", (PhaseDefinition(name="veg"),)),
            ("update_definition", ("pd1", {})),
            ("delete_definition", ("pd1",)),
            ("create_sequence", (PhaseSequence(name="std"),)),
            ("update_sequence", ("ps1", {})),
            ("delete_sequence", ("ps1",)),
            ("clone_sequence", ("ps1", "copy")),
            ("create_entry", (PhaseSequenceEntry(),)),
            ("update_entry", ("pse1", {})),
            ("delete_entry", ("pse1",)),
            ("reorder_entries", ("ps1", [])),
        ],
    )
    def test_phase_sequence_writes_refuse_a_call_that_omits_the_flag(self, method: str, args: tuple) -> None:
        from app.domain.services.phase_sequence_service import PhaseSequenceService

        service = PhaseSequenceService(SimpleNamespace())

        with pytest.raises(TypeError):
            getattr(service, method)(*args)

    @pytest.mark.parametrize(
        ("method", "args"),
        [
            ("create_pest", (Pest(scientific_name="A b", common_name="x"),)),
            ("update_pest", ("p1", {})),
            ("delete_pest", ("p1",)),
            ("create_disease", (Disease(scientific_name="A b", common_name="x", pathogen_type="fungal"),)),
            ("update_disease", ("d1", {})),
            ("delete_disease", ("d1",)),
            ("create_treatment", (Treatment(name="Neem", treatment_type="biological"),)),
            ("update_treatment", ("t1", {})),
            ("delete_treatment", ("t1",)),
        ],
    )
    def test_ipm_catalogue_writes_refuse_a_call_that_omits_the_flag(self, method: str, args: tuple) -> None:
        from app.domain.services.ipm_service import IpmService

        service = IpmService(SimpleNamespace(), SimpleNamespace(), SimpleNamespace(), SimpleNamespace())

        with pytest.raises(TypeError):
            getattr(service, method)(*args)
