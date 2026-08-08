"""API tests for #997 — ``PATCH /admin/platform/tenants/{key}`` must reach the
database through the service layer, not from the router.

**Why the double is an in-memory ArangoDB and not a mocked repository.** The
request is driven through the *real* :class:`ArangoTenantRepository`, the real
:class:`TenantEngine` and the real :class:`TenantService`; only the
``StandardDatabase`` underneath them is doubled, and it keeps its documents in a
plain ``dict``. So a rejection observed here is the production guard firing, and
a ``200`` observed here means the value genuinely reached storage — which is
what every negative test below asserts on (``store["t-1"]["name"]``), rather
than on a call count.

#996 rejected its own first red run because the failure came from a
``MagicMock`` result document that never became a model — red for the wrong
reason, and evidence of nothing. That shape is avoided here: the double returns
real, valid tenant documents on every path, so the only thing that can reject a
payload is a real validator.
"""

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from app.api.v1.admin.platform import router as mod
from app.common.auth import require_platform_admin
from app.common.dependencies import get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.common.error_handlers import app_error_handler, validation_error_handler
from app.common.exceptions import KamerplanterError
from app.data_access.arango.tenant_repository import ArangoTenantRepository
from app.domain.engines.invitation_engine import InvitationEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.engines.tenant_engine import TenantEngine
from app.domain.models.membership import MemberInfo
from app.domain.services.tenant_service import TenantService

TENANT_KEY = "t-1"
ORIGINAL_NAME = "Community Garden"
ORIGINAL_SLUG = "community-garden"

PLATFORM_KEY = "platform"
PLATFORM_NAME = "Platform"
PLATFORM_SLUG = "platform"


def _tenant_doc() -> dict[str, Any]:
    """A valid, complete stored tenant document."""
    return {
        "_key": TENANT_KEY,
        "_id": f"tenants/{TENANT_KEY}",
        "name": ORIGINAL_NAME,
        "slug": ORIGINAL_SLUG,
        "tenant_type": "organization",
        "description": "The old description",
        "owner_user_key": "u-owner",
        "is_active": True,
        "is_platform": False,
        "max_members": 50,
        "settings": {},
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


def _platform_tenant_doc() -> dict[str, Any]:
    """The system ``platform`` tenant — ``is_platform`` is ``True``."""
    return {
        "_key": PLATFORM_KEY,
        "_id": f"tenants/{PLATFORM_KEY}",
        "name": PLATFORM_NAME,
        "slug": PLATFORM_SLUG,
        "tenant_type": "organization",
        "description": "System platform tenant",
        "owner_user_key": "u-owner",
        "is_active": True,
        "is_platform": True,
        "max_members": 50,
        "settings": {},
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


class _FakeCollection:
    """The subset of ``StandardCollection`` this flow touches, over a dict store."""

    def __init__(self, store: dict[str, dict[str, Any]]) -> None:
        self._store = store

    def get(self, key: str) -> dict[str, Any] | None:
        doc = self._store.get(key)
        return dict(doc) if doc is not None else None

    def has(self, key: str) -> bool:
        return key in self._store

    def update(
        self,
        document: dict[str, Any],
        return_new: bool = False,
        keep_none: bool = True,
    ) -> dict[str, Any]:
        key = document["_key"]
        stored = self._store[key]
        patch = {field: value for field, value in document.items() if field != "_key"}
        if not keep_none:
            patch = {field: value for field, value in patch.items() if value is not None}
        stored.update(patch)
        return {"new": dict(stored)} if return_new else {"_key": key}


class _FakeAql:
    """Answers the two AQL shapes this flow can emit."""

    def __init__(self, store: dict[str, dict[str, Any]], member_count: int) -> None:
        self._store = store
        self._member_count = member_count

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        if "RETURN doc" in query:
            # AQLBuilder list query — the repository's get_by_slug lookup.
            wanted = bind_vars.get("v0")
            return iter([dict(doc) for doc in self._store.values() if doc.get("slug") == wanted])
        # The router's own ``COLLECT WITH COUNT`` member-count probe.
        return iter([self._member_count])


class _FakeDb:
    def __init__(self, store: dict[str, dict[str, Any]], member_count: int) -> None:
        self._store = store
        self.aql = _FakeAql(store, member_count)

    def collection(self, _name: str) -> _FakeCollection:
        return _FakeCollection(self._store)


def _members(count: int) -> list[MemberInfo]:
    return [
        MemberInfo(
            key=f"m-{index}",
            user_key=f"u-{index}",
            display_name=f"Member {index}",
            email=f"member{index}@example.test",
            role=TenantRole.VIEWER,
            admin_scopes=[AdminScope.MANAGEMENT] if index == 0 else [],
            is_active=True,
            joined_at=None,
        )
        for index in range(count)
    ]


@pytest.fixture
def store() -> dict[str, dict[str, Any]]:
    return {TENANT_KEY: _tenant_doc()}


@pytest.fixture
def client(
    store: dict[str, dict[str, Any]],
) -> TestClient:
    member_count = 2
    db = _FakeDb(store, member_count)

    membership_repo = MagicMock()
    membership_repo.list_by_tenant.return_value = _members(member_count)

    service = TenantService(
        tenant_repo=ArangoTenantRepository(db),  # type: ignore[arg-type]
        membership_repo=membership_repo,
        invitation_repo=MagicMock(),
        assignment_repo=MagicMock(),
        tenant_engine=TenantEngine(),
        membership_engine=MembershipEngine(),
        invitation_engine=InvitationEngine(),
    )

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]
    app.dependency_overrides[require_platform_admin] = lambda: SimpleNamespace(key="admin-1")
    app.dependency_overrides[get_tenant_service] = lambda: service
    return TestClient(app)


def _patch(client: TestClient, payload: dict[str, Any]):
    return client.patch(f"/api/v1/admin/platform/tenants/{TENANT_KEY}", json=payload)


# ── #997: values the domain forbids must not be persisted ────────────────────


class TestInvalidValuesAreRejected:
    """``AdminTenantUpdate`` constrains ``name`` less than the domain does.

    It declares a bare ``str | None`` where ``TenantUpdateRequest`` declares
    ``min_length=1, max_length=200`` — and ``TenantEngine.validate_tenant_name``
    additionally requires two non-space characters. Writing from the router put
    the endpoint outside all three, so these payloads were stored verbatim.
    """

    def test_rejects_an_empty_name_instead_of_persisting_it(self, client, store):
        response = _patch(client, {"name": ""})

        assert response.status_code == 422
        assert store[TENANT_KEY]["name"] == ORIGINAL_NAME

    def test_rejects_a_one_character_name(self, client, store):
        response = _patch(client, {"name": "A"})

        assert response.status_code == 422
        assert store[TENANT_KEY]["name"] == ORIGINAL_NAME

    def test_rejects_a_name_over_the_length_limit(self, client, store):
        response = _patch(client, {"name": "x" * 201})

        assert response.status_code == 422
        assert store[TENANT_KEY]["name"] == ORIGINAL_NAME

    def test_rejects_a_whitespace_only_name(self, client, store):
        response = _patch(client, {"name": "   "})

        assert response.status_code == 422
        assert store[TENANT_KEY]["name"] == ORIGINAL_NAME


class TestRoutesThroughTheServiceLayer:
    """NFR-001 — the router must not reach Persistence itself."""

    def test_router_module_holds_no_database_handle(self, client, store):
        """With every path routed through a service (#1019), the router module has
        no ``get_db`` symbol to reach Persistence through — the structural
        counterpart to the ``check_layer_imports`` gate, which refuses the import."""
        response = _patch(client, {"description": "A new description"})

        assert response.status_code == 200
        assert not hasattr(mod, "get_db")

    def test_rename_rederives_the_slug_like_the_tenant_scoped_path(self, client, store):
        """``PATCH /t/{slug}`` re-derives the slug on rename; this path did not.

        Going through :meth:`TenantService.update_tenant` closes that
        divergence, so a tenant renamed by a platform admin no longer keeps a
        slug that contradicts its name.
        """
        response = _patch(client, {"name": "Rooftop Garden"})

        assert response.status_code == 200
        assert response.json()["slug"] == "rooftop-garden"
        assert store[TENANT_KEY]["slug"] == "rooftop-garden"


# ── Existing platform-admin behaviour: green before and after ────────────────


class TestExistingBehaviourIsPreserved:
    def test_updates_name_description_and_max_members(self, client, store):
        response = _patch(
            client,
            {"name": "Rooftop Garden", "description": "A new description", "max_members": 12},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Rooftop Garden"
        assert body["description"] == "A new description"
        assert body["max_members"] == 12
        assert store[TENANT_KEY]["name"] == "Rooftop Garden"
        assert store[TENANT_KEY]["max_members"] == 12

    def test_toggles_the_platform_admin_only_is_active_field(self, client, store):
        """``is_active`` is the one field ``TenantUpdateRequest`` does not carry.

        It has to keep working, or the fix would be a refusal that passes by
        blocking the very thing this endpoint exists for.
        """
        response = _patch(client, {"is_active": False})

        assert response.status_code == 200
        assert response.json()["is_active"] is False
        assert store[TENANT_KEY]["is_active"] is False

    def test_response_carries_the_live_member_count(self, client):
        response = _patch(client, {"description": "A new description"})

        assert response.status_code == 200
        assert response.json()["member_count"] == 2

    def test_empty_payload_leaves_the_tenant_untouched(self, client, store):
        response = _patch(client, {})

        assert response.status_code == 200
        assert response.json()["name"] == ORIGINAL_NAME
        assert store[TENANT_KEY] == _tenant_doc()

    def test_unknown_tenant_returns_404(self, client, store):
        response = client.patch(
            "/api/v1/admin/platform/tenants/ghost",
            json={"description": "A new description"},
        )

        assert response.status_code == 404
        assert store[TENANT_KEY] == _tenant_doc()

    def test_schema_level_constraint_still_rejects_max_members_zero(self, client, store):
        response = _patch(client, {"max_members": 0})

        assert response.status_code == 422
        assert store[TENANT_KEY]["max_members"] == 50


# ── #1021: the platform tenant cannot be deactivated ─────────────────────────


class TestPlatformTenantCannotBeDeactivated:
    """``delete_tenant`` refuses the platform tenant (403); ``update_tenant`` did
    not, so ``{"is_active": false}`` on it went through.

    The guard lives in :meth:`TenantService.update_tenant`, so both entry points
    are covered — the platform-admin path here and the tenant-scoped
    ``PATCH /t/{slug}`` (which never carries ``is_active`` today, but would be
    guarded if it ever did). It refuses with the same 403 shape ``delete_tenant``
    already uses.
    """

    def test_deactivating_the_platform_tenant_is_refused(self, client, store):
        store[PLATFORM_KEY] = _platform_tenant_doc()

        response = client.patch(
            f"/api/v1/admin/platform/tenants/{PLATFORM_KEY}",
            json={"is_active": False},
        )

        assert response.status_code == 403
        assert store[PLATFORM_KEY]["is_active"] is True

    def test_an_ordinary_tenant_stays_deactivable(self, client, store):
        """The half that catches a guard refusing everyone."""
        response = _patch(client, {"is_active": False})

        assert response.status_code == 200
        assert response.json()["is_active"] is False
        assert store[TENANT_KEY]["is_active"] is False

    def test_platform_tenant_non_deactivation_updates_still_pass(self, client, store):
        """The guard is scoped to deactivation — a rename must still work."""
        store[PLATFORM_KEY] = _platform_tenant_doc()

        response = client.patch(
            f"/api/v1/admin/platform/tenants/{PLATFORM_KEY}",
            json={"description": "Renamed platform description"},
        )

        assert response.status_code == 200
        assert store[PLATFORM_KEY]["description"] == "Renamed platform description"
        assert store[PLATFORM_KEY]["is_active"] is True
