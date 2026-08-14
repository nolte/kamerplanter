"""Who may mutate the global botanical-family catalogue (#1120).

`BotanicalFamily` is global reference data: the model carries no `tenant_key`,
so there is not even an ownership boundary to fall back on. Every other global
catalogue surface has been gated since #1109 — "only a platform admin may modify
the global cultivar catalogue", enforced through `SpeciesService` — but
`create_family` / `update_family` / `delete_family` applied **no role check at
all**. Any authenticated member of any tenant, including a `viewer`, could
create, rename or delete a family every other tenant reads.

Confirmed pre-existing during the #1091 work (issue-orchestrate A-5 and the A-9
security review both flagged it); the `X-Active-Tenant` resolver those routes
gained answers *which* tenant the caller acts in, which is a different question
from *may* they write.

## What the tests hold the routes to

The same rule the cultivar catalogue states, in the same words: a platform admin
may curate the shared catalogue, and nobody else may. Both directions are
pinned, because a gate that refused everyone would satisfy the negative half on
its own and break curation.

## Real vs doubled

**Real**: the botanical-families router, the error handler that shapes the 403,
and `get_is_platform_admin`'s decision as the route consumes it. **Doubled**:
the family repository and the platform-admin lookup — the collaborators that
would otherwise be ArangoDB. The repository is a recorder, so "the route
refused" is provable as *no write reached it*, not merely as a status code.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.botanical_families.router import router as families_router
from app.common import auth as auth_mod
from app.common.dependencies import get_family_repo
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError

_FAMILY = {"name": "Rosaceae", "common_name": "Rosengewächse"}


class _RecordingFamilyRepo:
    """Records every write, so a refusal is provable as an absent call."""

    def __init__(self) -> None:
        self.created: list[Any] = []
        self.updated: list[tuple[str, Any]] = []
        self.deleted: list[str] = []

    # ── writes ──
    def create_family(self, family: Any) -> Any:
        self.created.append(family)
        return family

    def update_family(self, key: str, family: Any) -> Any:
        self.updated.append((key, family))
        return family

    def delete_family(self, key: str) -> bool:
        self.deleted.append(key)
        return True

    # ── the read the single-row response builder needs ──
    def get_species_count_by_family(self, key: str, *, tenant_key: str) -> int:
        return 0

    @property
    def writes(self) -> int:
        return len(self.created) + len(self.updated) + len(self.deleted)


def _client(repo: _RecordingFamilyRepo, *, platform_admin: bool) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(families_router, prefix="/api/v1")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_family_repo] = lambda: repo
    app.dependency_overrides[auth_mod.get_is_platform_admin] = lambda: platform_admin
    app.dependency_overrides[auth_mod.get_active_tenant_key] = lambda: ""
    return TestClient(app)


@pytest.fixture
def repo() -> _RecordingFamilyRepo:
    return _RecordingFamilyRepo()


class TestANonAdminMayNotCurateTheSharedCatalogue:
    """The gap: a viewer of any tenant could write reference data for everyone."""

    def test_create_is_refused(self, repo: _RecordingFamilyRepo) -> None:
        response = _client(repo, platform_admin=False).post("/api/v1/botanical-families", json=_FAMILY)

        assert response.status_code == 403, response.text
        assert repo.writes == 0, "the refusal must happen before the repository is touched"

    def test_update_is_refused(self, repo: _RecordingFamilyRepo) -> None:
        response = _client(repo, platform_admin=False).put("/api/v1/botanical-families/rosaceae", json=_FAMILY)

        assert response.status_code == 403, response.text
        assert repo.writes == 0

    def test_delete_is_refused(self, repo: _RecordingFamilyRepo) -> None:
        response = _client(repo, platform_admin=False).delete("/api/v1/botanical-families/rosaceae")

        assert response.status_code == 403, response.text
        assert repo.writes == 0

    def test_the_refusal_names_the_rule_the_caller_broke(self, repo: _RecordingFamilyRepo) -> None:
        """Same wording as the cultivar catalogue's, so the two cannot drift apart.

        A 403 whose message is generic leaves the caller guessing whether the
        answer is "not this tenant" or "not this role"; the global catalogue has
        one rule and it is worth naming.
        """
        response = _client(repo, platform_admin=False).post("/api/v1/botanical-families", json=_FAMILY)

        assert "platform admin" in response.text.lower()
        assert "botanical famil" in response.text.lower()


class TestAPlatformAdminStillCurates:
    """The half that keeps the gate from being a blanket refusal."""

    def test_create_reaches_the_repository(self, repo: _RecordingFamilyRepo) -> None:
        response = _client(repo, platform_admin=True).post("/api/v1/botanical-families", json=_FAMILY)

        assert response.status_code == 201, response.text
        assert len(repo.created) == 1

    def test_update_reaches_the_repository(self, repo: _RecordingFamilyRepo) -> None:
        response = _client(repo, platform_admin=True).put("/api/v1/botanical-families/rosaceae", json=_FAMILY)

        assert response.status_code == 200, response.text
        assert repo.updated == [("rosaceae", repo.updated[0][1])]

    def test_delete_reaches_the_repository(self, repo: _RecordingFamilyRepo) -> None:
        response = _client(repo, platform_admin=True).delete("/api/v1/botanical-families/rosaceae")

        assert response.status_code == 204, response.text
        assert repo.deleted == ["rosaceae"]
