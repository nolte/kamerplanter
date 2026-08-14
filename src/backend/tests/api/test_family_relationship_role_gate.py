"""Who may write the botanical-family relationship graph (#1156).

`POST /family-relationships/pest-risk`, `/compatible` and `/incompatible` write
graph edges between **botanical families** — global reference data with no
`tenant_key`, read by every tenant. The router was gated by `get_current_user`
and nothing else, so any authenticated member, a `viewer` included, could declare
that two families share a pest risk or are incompatible neighbours, and every
other tenant's companion-planting and crop-rotation recommendations changed with
it. REQ-001 §4 lists these as platform-admin writes; the routes never enforced it.

Same failure class as #1120 on an adjacent surface, found by that PR's own review.

## Real vs doubled

**Real**: the family-relationships router, the dependency graph FastAPI resolves
for it, the shared refusal from `catalogue_authorization`, and the error handler
that shapes the 403. **Doubled**: the graph repository, as a recorder — so "the
route refused" is provable as *no edge was written*, not merely as a status code.
A gate that answered 403 after writing would pass a status-only assertion.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.family_relationships.router import router as relationships_router
from app.common import auth as auth_mod
from app.common.dependencies import get_graph_repo
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError

#: (route, body) for each mutating endpoint, so a fourth one added without a gate
#: shows up as an untested route rather than as silence.
_WRITES = [
    (
        "/pest-risk",
        {
            "a_family_key": "fam_solanaceae",
            "b_family_key": "fam_rosaceae",
            "shared_pests": ["aphid"],
            "shared_diseases": [],
            "risk_level": "high",
        },
    ),
    (
        "/compatible",
        {
            "a_family_key": "fam_solanaceae",
            "b_family_key": "fam_apiaceae",
            "benefit_type": "pest_deterrent",
            "compatibility_score": 0.9,
            "notes": "",
        },
    ),
    (
        "/incompatible",
        {
            "a_family_key": "fam_solanaceae",
            "b_family_key": "fam_solanaceae",
            "reason": "shared soil pathogens",
            "severity": "high",
        },
    ),
]


class _RecordingGraphRepo:
    """Records every edge write, so a refusal is provable as an absent call."""

    def __init__(self) -> None:
        self.writes: list[tuple[str, tuple[Any, ...]]] = []

    def set_pest_risk(self, *args: Any) -> None:
        self.writes.append(("set_pest_risk", args))

    def set_family_compatible(self, *args: Any) -> None:
        self.writes.append(("set_family_compatible", args))

    def set_family_incompatible(self, *args: Any) -> None:
        self.writes.append(("set_family_incompatible", args))

    # ── reads, so the GET routes stay exercisable ──
    def get_pest_risks(self, family_key: str) -> list[dict]:
        return []

    def get_family_compatible(self, family_key: str) -> list[dict]:
        return []

    def get_family_incompatible(self, family_key: str) -> list[dict]:
        return []


def _client(repo: _RecordingGraphRepo, *, platform_admin: bool) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]
    app.include_router(relationships_router, prefix="/api/v1")
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="user_1")
    app.dependency_overrides[get_graph_repo] = lambda: repo
    app.dependency_overrides[auth_mod.get_is_platform_admin] = lambda: platform_admin
    return TestClient(app)


@pytest.fixture
def repo() -> _RecordingGraphRepo:
    return _RecordingGraphRepo()


@pytest.mark.parametrize(("route", "body"), _WRITES, ids=[r for r, _ in _WRITES])
class TestANonAdminMayNotRewriteTheSharedGraph:
    def test_the_write_is_refused(self, repo: _RecordingGraphRepo, route: str, body: dict) -> None:
        response = _client(repo, platform_admin=False).post(f"/api/v1/family-relationships{route}", json=body)

        assert response.status_code == 403, response.text

    def test_no_edge_reaches_the_repository(self, repo: _RecordingGraphRepo, route: str, body: dict) -> None:
        """The assertion that a status code alone cannot make.

        A gate placed *after* the write would answer 403 and still have changed
        every tenant's recommendations.
        """
        _client(repo, platform_admin=False).post(f"/api/v1/family-relationships{route}", json=body)

        assert repo.writes == []


@pytest.mark.parametrize(("route", "body"), _WRITES, ids=[r for r, _ in _WRITES])
class TestAPlatformAdminStillCurates:
    """The half that keeps the gate from being a blanket refusal.

    Without these, a router that rejected everyone would satisfy every negative
    assertion above — and would break the curation REQ-001 §4 provides for.
    """

    def test_the_write_reaches_the_repository(self, repo: _RecordingGraphRepo, route: str, body: dict) -> None:
        response = _client(repo, platform_admin=True).post(f"/api/v1/family-relationships{route}", json=body)

        assert response.status_code == 201, response.text
        assert len(repo.writes) == 1


class TestReadsStayOpen:
    """The gate belongs on the three writes; every member may still read the graph."""

    @pytest.mark.parametrize("suffix", ["pest-risks", "compatible", "incompatible"])
    def test_a_non_admin_may_read(self, repo: _RecordingGraphRepo, suffix: str) -> None:
        response = _client(repo, platform_admin=False).get(
            f"/api/v1/family-relationships/families/fam_solanaceae/{suffix}"
        )

        assert response.status_code == 200, response.text


class TestTheRefusalNamesTheRule:
    def test_it_says_platform_admin(self, repo: _RecordingGraphRepo) -> None:
        """Worded from the shared refusal, so the four global surfaces cannot drift."""
        response = _client(repo, platform_admin=False).post(
            "/api/v1/family-relationships/pest-risk", json=_WRITES[0][1]
        )

        assert "platform admin" in response.text.lower()
