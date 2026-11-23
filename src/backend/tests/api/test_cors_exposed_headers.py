"""The CORS layer exposes the response headers the SPA reads (#2934).

A cross-origin SPA sees a response header only when it is CORS-safelisted or
listed in ``Access-Control-Expose-Headers``. ``Retry-After`` is neither by
default: without the entry, a refused manual weather fetch (429) could not say
when a new one is possible in a deployment where the frontend is served from
another origin. The plan-export headers are pinned in
``test_garden_plan_export_api.py``; this file pins the header list itself.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_cors_exposes_retry_after_to_an_allowed_origin() -> None:
    response = TestClient(app).get("/api/v1/health/live", headers={"Origin": "http://localhost:5173"})

    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    exposed = {h.strip().lower() for h in response.headers.get("access-control-expose-headers", "").split(",")}
    assert "retry-after" in exposed
