"""An empty active tenant sees no import job at all — #1501 review SCR-001.

`get_active_tenant_context` resolves **three** ordinary caller classes to
``tenant_key == ""``: a user with no personal tenant, a service account sending no
`X-Active-Tenant` header, and the light-mode operator. The first version of
#1501's scope read ``tenant_key is not None and job.tenant_key != tenant_key``,
which made that empty key a **wildcard** over every pre-#1501 job (all of them —
`ImportJob.tenant_key` defaulted to `""` and nothing ever wrote it), and passed it
straight down to `_list_docs`, whose filter is `if tenant_key:` — so `GET
/import/jobs` answered an *unfiltered* list, `preview_rows` and all, i.e. the
contents of other tenants' uploaded CSVs.

## Why this file exists next to `test_global_router_write_gates_api.py`

That file overrides `get_active_tenant_context` with a fixed context, which is
right for asking *what the route does with the tenant it was given* and cannot
ask *which tenant the resolver gives*. The defect lived in the second question, so
every test here drives the **real** resolver: only `get_current_user` and
`get_tenant_service` are substituted, and the empty key is produced by
`_resolve_active_tenant` the way production produces it — a user whose
`get_personal_tenant` returns `None`.

## Real vs doubled

**Real**: the import router, `ImportService`, `get_active_tenant_context` and the
whole resolver beneath it, the error handler. **Doubled**: the job repository (a
dict-backed fake with the real signatures) and `TenantService`.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.imports.router import router as imports_router
from app.common import auth as auth_mod
from app.common.dependencies import get_import_service
from app.common.enums import EntityType
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.import_job import ImportJob
from app.domain.services.import_service import ImportService

_OWNED_BY_A = ImportJob(_key="job_a", entity_type=EntityType.SPECIES, tenant_key="tenant_a")
#: The shape every job in a pre-#1501 installation has: no owner at all.
_UNOWNED = ImportJob(_key="job_legacy", entity_type=EntityType.SPECIES, tenant_key="")


class _FakeJobRepo:
    """A dict-backed job repository carrying the REAL signatures.

    Not a ``MagicMock``: `list_all`'s ``tenant_key`` keyword and the empty-string
    case are the whole subject, and a mock accepts every call there is. It also
    reproduces the property that made the defect exploitable — an empty
    ``tenant_key`` means *no filter*, exactly as `_list_docs`' ``if tenant_key:``
    does — so a service that passes ``""`` down fails here instead of passing.
    """

    def __init__(self, jobs: list[ImportJob]) -> None:
        self._jobs = {j.key: j for j in jobs}
        self.list_calls: list[str | None] = []

    def get_or_raise(self, key: str) -> ImportJob:
        job = self._jobs.get(key)
        if job is None:
            raise NotFoundError("ImportJob", key)
        return job

    def list_all(self, offset: int = 0, limit: int = 50, *, tenant_key: str | None = None):
        self.list_calls.append(tenant_key)
        if not tenant_key:
            # The fail-open the real `_list_docs` performs for a falsy key.
            items = list(self._jobs.values())
        else:
            items = [j for j in self._jobs.values() if j.tenant_key == tenant_key]
        return (items, len(items))

    def delete(self, key: str) -> bool:
        return self._jobs.pop(key, None) is not None


def _client_with_no_resolvable_tenant() -> tuple[TestClient, _FakeJobRepo]:
    """A signed-in caller whose personal tenant does not exist → `tenant_key == ""`.

    The header is absent, so `_resolve_active_tenant` takes its personal-tenant
    branch and `get_personal_tenant` returning ``None`` is what yields the empty
    key — the production path, not a stubbed context.
    """
    repo = _FakeJobRepo([_OWNED_BY_A, _UNOWNED])
    service = ImportService(repo)

    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(imports_router, prefix="/api/v1")
    app.dependency_overrides[get_import_service] = lambda: service
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(
        key="user_without_tenant", account_type="user"
    )
    app.dependency_overrides[auth_mod.get_tenant_service] = lambda: SimpleNamespace(
        get_personal_tenant=lambda _user_key: None,
        get_membership=lambda _user_key, _tenant_key: None,
        # `is_platform_admin` consults this; an ordinary user is not one.
        get_tenant_by_slug=lambda _slug: None,
    )
    return TestClient(app), repo


class TestTheResolverReallyProducesTheEmptyKey:
    """The premise, checked — without it every assertion below is vacuous.

    A test that asserts "the empty context sees nothing" while the context is in
    fact a real tenant passes for the wrong reason, which is the failure class this
    whole file is a response to.
    """

    def test_a_user_without_a_personal_tenant_resolves_to_the_empty_key(self) -> None:
        ctx = auth_mod.get_active_tenant_context(
            user=SimpleNamespace(key="user_without_tenant", account_type="user"),  # type: ignore[arg-type]
            tenant_service=SimpleNamespace(  # type: ignore[arg-type]
                get_personal_tenant=lambda _k: None,
                get_membership=lambda _u, _t: None,
            ),
            active_tenant_slug=None,
        )

        assert ctx.tenant_key == ""

    def test_a_service_account_without_a_header_resolves_to_the_empty_key(self) -> None:
        """The second way in, and the one no fixture would have thought of.

        REQ-023 M2M callers have no personal-tenant fallback at all (#1122), so an
        integration hitting `/import/jobs` without the header arrives empty too.
        """
        ctx = auth_mod.get_active_tenant_context(
            user=SimpleNamespace(key="svc_1", account_type="service"),  # type: ignore[arg-type]
            tenant_service=SimpleNamespace(get_personal_tenant=lambda _k: None),  # type: ignore[arg-type]
            active_tenant_slug=None,
        )

        assert ctx.tenant_key == ""


class TestTheEmptyContextSeesNoJob:
    """Fail-closed, on all three routes that read or destroy a job."""

    def test_listing_returns_nothing_and_never_reaches_the_repository(self) -> None:
        client, repo = _client_with_no_resolvable_tenant()

        response = client.get("/api/v1/import/jobs")

        assert response.status_code == 200, response.text
        assert response.json() == []
        # The stronger half: the service must not hand `""` down at all. If it did,
        # the fake's falsy-key branch — a faithful copy of `_list_docs`' own — would
        # have returned both jobs, and an assertion on the body alone would pass the
        # day somebody "fixes" the filter instead of the scope.
        assert repo.list_calls == [], f"the empty key reached the repository: {repo.list_calls}"

    def test_reading_a_foreign_job_by_key_is_404(self) -> None:
        client, _repo = _client_with_no_resolvable_tenant()

        assert client.get("/api/v1/import/jobs/job_a").status_code == 404

    def test_reading_an_unowned_legacy_job_by_key_is_404_too(self) -> None:
        """The wildcard case: `""` must not match a job stamped `""`.

        This is the exact comparison the first version got wrong. Every job in a
        pre-#1501 installation is stamped `""`, so an equality test between the two
        empty strings handed the whole collection to the one caller class that owns
        nothing.
        """
        client, _repo = _client_with_no_resolvable_tenant()

        assert client.get("/api/v1/import/jobs/job_legacy").status_code == 404

    def test_deleting_an_unowned_legacy_job_is_404(self) -> None:
        client, repo = _client_with_no_resolvable_tenant()

        assert client.delete("/api/v1/import/jobs/job_legacy").status_code == 404
        assert repo.get_or_raise("job_legacy") is _UNOWNED, "the row must not have been deleted"

    def test_confirming_without_an_active_tenant_is_refused(self) -> None:
        """422, not 404: "you have no active tenant" hides no row's existence.

        A *foreign* job earns the 404 — the caller must not learn it exists. This
        caller's problem is about themselves, so the honest answer names it.
        """
        client, _repo = _client_with_no_resolvable_tenant()

        response = client.post("/api/v1/import/jobs/job_legacy/confirm")

        assert response.status_code == 422, response.text

    def test_uploading_without_an_active_tenant_is_refused(self) -> None:
        """The other end: nothing new can ever be stamped `""`.

        422, matching `confirm` — the refusal is about the caller having no tenant,
        which is a true statement about themselves and hides no row. Without it the
        collection would keep regrowing the very class `v0052` deletes, and the
        migration would be a one-off cleanup of a defect still in production.
        """
        client, _repo = _client_with_no_resolvable_tenant()

        response = client.post(
            "/api/v1/import/upload",
            files={"file": ("rows.csv", b"scientific_name\nRosa canina\n", "text/csv")},
            data={"entity_type": EntityType.SPECIES.value, "duplicate_strategy": "skip"},
        )

        assert response.status_code == 422, response.text


class TestTheServiceDecidesTheSameWayWithoutARequest:
    """The service arm on its own — the non-HTTP caller the router cannot speak for."""

    def test_the_empty_key_is_not_a_system_context(self) -> None:
        repo = _FakeJobRepo([_UNOWNED])
        service = ImportService(repo)

        with pytest.raises(NotFoundError):
            service.get_job("job_legacy", tenant_key="")

    def test_none_still_is_the_system_context(self) -> None:
        """The control. A scope that also refused the seeders would be a regression."""
        repo = _FakeJobRepo([_UNOWNED])
        service = ImportService(repo)

        assert service.get_job("job_legacy", tenant_key=None) is _UNOWNED
        assert service.list_jobs(tenant_key=None)[1] == 1
        assert repo.list_calls == [None]
