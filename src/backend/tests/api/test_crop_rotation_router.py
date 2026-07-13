"""API tests for the crop-rotation counts endpoint (#550).

``GET /crop-rotation/counts`` returns the whole-catalogue aggregate keyed by
family_key that badges the "Von Familie" dropdown with per-family successor
counts. It is fed by a single batch AQL (no N+1) in the graph repository; here we
only pin the router contract: the endpoint delegates to
``graph.get_rotation_successor_counts`` and returns the map verbatim, including
families with a zero-successor entry absent from the map.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.crop_rotation.router import router as crop_rotation_router
from app.common.auth import get_current_user
from app.common.dependencies import get_graph_repo


def _user() -> SimpleNamespace:
    return SimpleNamespace(key="user_1")


def _build_app(graph: MagicMock) -> FastAPI:
    app = FastAPI()
    app.include_router(crop_rotation_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[get_graph_repo] = lambda: graph
    return app


def test_counts_endpoint_returns_per_family_counts() -> None:
    graph = MagicMock()
    graph.get_rotation_successor_counts.return_value = {
        "solanaceae": 3,
        "fabaceae": 1,
        "brassicaceae": 2,
    }
    client = TestClient(_build_app(graph))

    resp = client.get("/api/v1/crop-rotation/counts")

    assert resp.status_code == 200
    assert resp.json() == {"solanaceae": 3, "fabaceae": 1, "brassicaceae": 2}
    graph.get_rotation_successor_counts.assert_called_once_with()


def test_counts_endpoint_returns_empty_map_when_no_rotation_edges() -> None:
    graph = MagicMock()
    graph.get_rotation_successor_counts.return_value = {}
    client = TestClient(_build_app(graph))

    resp = client.get("/api/v1/crop-rotation/counts")

    assert resp.status_code == 200
    assert resp.json() == {}


def test_successors_endpoint_passes_through_common_name_and_category() -> None:
    """GET /successors surfaces common_name_de + rotation_category from the family
    vertex so the UI can lead with a layperson name and humanise the code (#567)."""
    graph = MagicMock()
    graph.get_rotation_successors.return_value = [
        {
            "family": {
                "_key": "fabaceae",
                "name": "Fabaceae",
                "common_name_de": "Hülsenfrüchtler",
                "common_name_en": "Legumes",
                "rotation_category": "legume",
            },
            "wait_years": 2,
            "benefit_score": 0.9,
            "benefit_reason": "nitrogen_fixation",
        }
    ]
    client = TestClient(_build_app(graph))

    resp = client.get("/api/v1/crop-rotation/families/solanaceae/successors")

    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["family_key"] == "fabaceae"
    assert row["common_name_de"] == "Hülsenfrüchtler"
    assert row["rotation_category"] == "legume"
    assert row["benefit_reason"] == "nitrogen_fixation"
    assert row["wait_years"] == 2
