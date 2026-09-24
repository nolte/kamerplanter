"""#1461 — the repaired safe methods answer without writing a row.

Four of the ten writing ``GET``s the #1443 detector reported were *auto-create
singletons*: the handler read a per-user (or per-site) document, found none, and
created one while answering. The repair is the same in each case — the read
returns the value it would have returned anyway, and the first **write** creates
the row.

`tests/unit/api/test_write_route_gates.py` already refuses the class
statically: the detector walks the call graph and any read that reaches a
persistence write turns the sweep red. This file is the behavioural half, asked
of the mounted route rather than of the AST, and it asks it the way the issue
does: **count the documents**. A repair that removed the call but left some other
write behind would still be green in a test that only checked the response body.

The doubles here are repositories, not services: the services under test are the
production ones, so a write they perform lands in the double's document store and
shows up in the count. A double of the *service* would have made every assertion
below vacuous.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.common.auth import get_current_tenant
from app.common.enums import TenantRole
from app.domain.models.tenant_context import TenantContext

TENANT_SLUG = "test-slug"
USER_KEY = "user-1"


def _ctx() -> TenantContext:
    return TenantContext(tenant_key="t-1", tenant_slug=TENANT_SLUG, user_key=USER_KEY, role=TenantRole.GROWER)


class _CountingSingletonRepo:
    """A per-user singleton collection that starts empty and counts every write.

    Mirrors the raw-dict interface the two services drive
    (``find_by_field``/``create``/``update``/``update_fields``), because that is
    the boundary they own. ``documents`` is the collection count the tests assert
    on — the thing the issue is about.
    """

    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []
        self.writes = 0

    def find_by_field(self, field: str, value: Any) -> list[dict[str, Any]]:
        return [dict(doc) for doc in self.documents if doc.get(field) == value]

    def create(self, model: Any) -> dict[str, Any]:
        self.writes += 1
        doc = {"_key": f"doc-{len(self.documents) + 1}", **model.model_dump(mode="json", exclude={"key"})}
        self.documents.append(doc)
        return dict(doc)

    def update(self, key: str, model: Any) -> dict[str, Any]:
        self.writes += 1
        doc = next(d for d in self.documents if d["_key"] == key)
        doc.update(model.model_dump(mode="json", exclude={"key"}))
        return dict(doc)

    def update_fields(self, key: str, fields: dict[str, Any]) -> dict[str, Any]:
        self.writes += 1
        doc = next(d for d in self.documents if d["_key"] == key)
        doc.update(fields)
        return dict(doc)


# ── GET /t/{slug}/user-preferences (finding 8) ───────────────────────────────


def _preference_service(repo: _CountingSingletonRepo):
    """The real service, really constructed, with only its repository doubled.

    `__new__` was the shortcut here, and review SCR-011 is right that it is the
    wrong one: it skips `__init__`, so a constructor that grew a second collection
    or a derived field would leave these tests exercising an object the
    application never builds. Passing a `MagicMock` database lets `__init__` run —
    it only uses `db` to construct a `BaseArangoRepository` — and the counting
    double then replaces that one attribute.
    """
    from app.domain.services.user_preference_service import UserPreferenceService

    service = UserPreferenceService(MagicMock())
    service._repo = repo  # type: ignore[assignment]
    return service


def _preferences_client(repo: _CountingSingletonRepo) -> TestClient:
    from app.api.v1.user_preferences.tenant_router import router
    from app.common.dependencies import get_user_preference_service

    app = FastAPI()
    app.include_router(router, prefix=f"/api/v1/t/{TENANT_SLUG}")
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_user_preference_service] = lambda: _preference_service(repo)
    return TestClient(app)


def test_reading_preferences_answers_the_defaults_and_writes_nothing():
    repo = _CountingSingletonRepo()

    response = _preferences_client(repo).get(f"/api/v1/t/{TENANT_SLUG}/user-preferences")

    assert response.status_code == 200
    body = response.json()
    assert body["user_key"] == USER_KEY
    assert body["experience_level"] == "beginner"
    assert body["key"] == "", "a key means a row was written"
    assert repo.documents == [], "the read created a user_preferences document"
    assert repo.writes == 0


def test_the_first_patch_materialises_the_row():
    """The other half — without it the test above could pass on a broken write path."""
    repo = _CountingSingletonRepo()
    client = _preferences_client(repo)

    response = client.patch(f"/api/v1/t/{TENANT_SLUG}/user-preferences", json={"theme": "dark"})

    assert response.status_code == 200
    assert response.json()["theme"] == "dark"
    assert len(repo.documents) == 1
    # And the read now sees it, with a key.
    assert client.get(f"/api/v1/t/{TENANT_SLUG}/user-preferences").json()["key"] == repo.documents[0]["_key"]


def test_repeated_reads_stay_at_zero_documents():
    """The shape the finding actually had: one row per cold reader, not one in total."""
    repo = _CountingSingletonRepo()
    client = _preferences_client(repo)

    for _ in range(3):
        assert client.get(f"/api/v1/t/{TENANT_SLUG}/user-preferences").status_code == 200

    assert repo.documents == []


# ── GET /t/{slug}/dashboard/widgets/catalog (finding 9) ──────────────────────


def test_reading_the_widget_catalog_writes_nothing(monkeypatch: pytest.MonkeyPatch):
    """Finding 9 was never its own write: it inherited the preferences auto-create.

    The catalogue itself is a code constant (``dashboard_widget_catalog``) and is
    not seeded anywhere — measured on 2026-09-17, against the analysis note that
    expected a seed. The only write on the route was the one above, so repairing
    the preferences read repairs this one, and this test is what says so.
    """
    import app.api.v1.dashboard.tenant_router as dashboard_tenant_router
    from app.common.dependencies import get_user_preference_service

    monkeypatch.setattr(dashboard_tenant_router.settings, "kamerplanter_mode", "full")
    repo = _CountingSingletonRepo()

    app = FastAPI()
    app.include_router(dashboard_tenant_router.router, prefix=f"/api/v1/t/{TENANT_SLUG}")
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_user_preference_service] = lambda: _preference_service(repo)

    response = TestClient(app).get(f"/api/v1/t/{TENANT_SLUG}/dashboard/widgets/catalog")

    assert response.status_code == 200
    assert len(response.json()["widgets"]) > 5
    assert repo.documents == []


# ── GET /t/{slug}/onboarding/state (finding 7) ───────────────────────────────


def _onboarding_service(repo: _CountingSingletonRepo):
    """The real service, really constructed — see :func:`_preference_service`."""
    from tests.support.onboarding_wiring import build_onboarding_service

    service = build_onboarding_service(MagicMock())
    service._repo = repo  # type: ignore[assignment]
    return service


def _onboarding_client(repo: _CountingSingletonRepo) -> TestClient:
    from app.api.v1.onboarding.tenant_router import router
    from app.common.dependencies import get_onboarding_service

    app = FastAPI()
    app.include_router(router, prefix=f"/api/v1/t/{TENANT_SLUG}")
    app.dependency_overrides[get_current_tenant] = _ctx
    app.dependency_overrides[get_onboarding_service] = lambda: _onboarding_service(repo)
    return TestClient(app)


def test_reading_the_onboarding_state_answers_the_initial_state_and_writes_nothing():
    repo = _CountingSingletonRepo()

    response = _onboarding_client(repo).get(f"/api/v1/t/{TENANT_SLUG}/onboarding/state")

    assert response.status_code == 200
    body = response.json()
    assert body["user_key"] == USER_KEY
    assert body["completed"] is False
    assert body["wizard_step"] == 0
    assert body["key"] == "", "a key means a row was written"
    assert repo.documents == [], "the read created an onboarding_states document"


def test_the_first_progress_patch_materialises_the_state():
    """The other half, so the assertion above is not satisfied by a broken route."""
    repo = _CountingSingletonRepo()
    client = _onboarding_client(repo)

    response = client.patch(f"/api/v1/t/{TENANT_SLUG}/onboarding/state", json={"wizard_step": 2})

    assert response.status_code == 200
    assert response.json()["wizard_step"] == 2
    assert len(repo.documents) == 1
