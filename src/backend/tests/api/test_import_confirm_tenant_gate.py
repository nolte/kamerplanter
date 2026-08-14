"""The import-confirm route carries the caller's tenant and role to the service (#1110).

`ImportService` grew an ownership stamp and a role gate, but a gate the HTTP
route never hands its inputs to is inert — the failure mode that has bitten this
repository more than once, and the one a service-level test cannot see. So this
file asserts the *wiring*: that `POST /import/jobs/{key}/confirm` resolves the
active tenant, resolves the platform-admin flag, and passes both to
`ImportService.confirm` — and that the refusal the service raises actually
reaches the wire as a 403.

## Real vs doubled

**Real**: the imports router, the error handler that shapes the 403, and the
dependency graph FastAPI resolves for the route. **Doubled**: `ImportService`
itself, as a recorder — the point here is *what the route told it*, which a real
service would swallow into a repository call. The service's own decisions are
pinned separately in `tests/unit/domain/services/test_import_tenant_scoping.py`.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.imports.router import router as imports_router
from app.common import auth as auth_mod
from app.common.dependencies import get_import_service
from app.common.enums import DuplicateStrategy, EntityType, ImportJobStatus, TenantRole
from app.common.error_handlers import app_error_handler
from app.common.exceptions import ForbiddenError, KamerplanterError
from app.domain.models.import_job import ImportJob
from app.domain.models.tenant_context import TenantContext

_TENANT = "tenant_acme"


class _RecordingImportService:
    """Records the confirm arguments; optionally refuses like the real gate would."""

    def __init__(self, *, refuse: bool = False) -> None:
        self.confirm_calls: list[dict[str, Any]] = []
        self._refuse = refuse

    def confirm(self, key: str, **kwargs: Any) -> ImportJob:
        self.confirm_calls.append({"key": key, **kwargs})
        if self._refuse:
            raise ForbiddenError("Your role may not modify species in this tenant.")
        return ImportJob(
            entity_type=EntityType.SPECIES,
            status=ImportJobStatus.COMPLETED,
            filename="rows.csv",
            duplicate_strategy=DuplicateStrategy.SKIP,
        )


def _client(
    service: _RecordingImportService,
    *,
    role: TenantRole = TenantRole.GROWER,
    tenant_key: str = _TENANT,
    platform_admin: bool = False,
) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(imports_router, prefix="/api/v1")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_import_service] = lambda: service
    app.dependency_overrides[auth_mod.get_is_platform_admin] = lambda: platform_admin
    app.dependency_overrides[auth_mod.get_active_tenant_context] = lambda: TenantContext(
        tenant_key=tenant_key,
        tenant_slug="acme",
        user_key="user_1",
        role=role,
        admin_scopes=[],
    )
    return TestClient(app)


@pytest.fixture
def service() -> _RecordingImportService:
    return _RecordingImportService()


class TestTheRouteHandsOverTheCallersContext:
    """Without these the service gate is unreachable from the wire — i.e. inert."""

    def test_the_active_tenant_reaches_the_service(self, service: _RecordingImportService) -> None:
        response = _client(service).post("/api/v1/import/jobs/job1/confirm")

        assert response.status_code == 200, response.text
        assert service.confirm_calls[0]["tenant_key"] == _TENANT

    def test_the_callers_role_reaches_the_service(self, service: _RecordingImportService) -> None:
        _client(service, role=TenantRole.VIEWER).post("/api/v1/import/jobs/job1/confirm")

        assert service.confirm_calls[0]["caller_role"] == TenantRole.VIEWER

    def test_the_platform_admin_flag_reaches_the_service(self, service: _RecordingImportService) -> None:
        _client(service, platform_admin=True).post("/api/v1/import/jobs/job1/confirm")

        assert service.confirm_calls[0]["is_platform_admin"] is True

    def test_the_role_is_never_silently_dropped(self, service: _RecordingImportService) -> None:
        """A `confirm(key)` with no context at all is the pre-#1110 call shape.

        Stated separately from the positive assertions above because *omission* is
        how this regresses: a refactor that drops one keyword leaves the route
        working, the tests above still passing on the others, and the service
        falling back to its ungated system-context default.
        """
        _client(service).post("/api/v1/import/jobs/job1/confirm")

        assert {"tenant_key", "caller_role", "is_platform_admin"} <= service.confirm_calls[0].keys()


class TestTheRefusalReachesTheWire:
    def test_a_gated_confirm_answers_403(self) -> None:
        service = _RecordingImportService(refuse=True)

        response = _client(service, role=TenantRole.VIEWER).post("/api/v1/import/jobs/job1/confirm")

        assert response.status_code == 403, response.text


class TestReadsAreUnaffected:
    """The gate belongs on the write; staging and listing stay open to any member."""

    def test_listing_jobs_needs_no_tenant_role(self, service: _RecordingImportService) -> None:
        service.list_jobs = lambda offset, limit: ([], 0)  # type: ignore[attr-defined]

        response = _client(service, role=TenantRole.VIEWER).get("/api/v1/import/jobs")

        assert response.status_code == 200, response.text
