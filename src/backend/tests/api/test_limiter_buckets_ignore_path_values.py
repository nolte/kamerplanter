"""A rate limit counts per route, not per caller-chosen path value (#2052).

slowapi's default ``key_style="url"`` builds each bucket from the **request
path**. On a route with a path parameter every distinct value was its own
bucket, and the value is the caller's to choose — unauthenticated ones
included. Measured before the fix on ``GET /public/glossary/term/{slug}``
(30/minute): 31 requests with one slug → 30 × 200, 1 × 429; 31 requests with 31
slugs → 31 × 200 and 31 storage keys. A ``%20`` suffix on the same slug was a
fresh bucket as well. Against the shared Valkey of #2045 every value also wrote
a key next to the Celery broker.

The limiter is built with ``key_style="endpoint"`` now: one bucket per client
address and route function, whatever the path says.

These tests drive the real application routes. The class — every limited
route, whichever path parameters it has — is held by
``tests/unit/guards/test_limited_routes_count_per_endpoint.py``.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.v1.glossar.deps import get_glossary_service
from app.api.v1.glossar.public_router import _TERM_RATE_LIMIT
from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_notification_service, get_privacy_service
from app.common.enums import TenantRole
from app.config.settings import settings
from app.domain.models.glossary_term import GlossaryTermAnswer
from app.domain.models.privacy import DataExportRequest
from app.domain.models.tenant_context import TenantContext


def _budget(limit: str) -> int:
    """Calls granted per window, read off the configured limit rather than repeated."""
    return int(limit.split("/")[0])


def _answer(slug: str) -> GlossaryTermAnswer:
    return GlossaryTermAnswer(
        slug=slug,
        label="VPD",
        long_label="Vapor Pressure Deficit",
        category="umwelt",
        answer_text="VPD ist ...",
        expertise_level="beginner",
        language="de",
        is_fallback=True,
    )


@pytest.fixture
def app_client() -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

    glossary = MagicMock()
    glossary.get_term.side_effect = lambda slug, **_: _answer(slug)

    notifications = MagicMock()
    notifications.send_test = AsyncMock(return_value={"status": "delivered", "success": True, "error": None})

    privacy = MagicMock()

    async def _bytes():  # noqa: ANN202 - async generator
        yield b"{}"

    async def _open(user_key: str, export_key: str):  # noqa: ANN202 - tuple of model and stream
        return DataExportRequest(key=export_key, user_key=user_key, status="completed"), _bytes()

    privacy.open_export_bundle = AsyncMock(side_effect=_open)

    user = MagicMock()
    user.key = "u-1"
    user.api_key_tenant_scope = None

    def _ctx() -> TenantContext:
        return TenantContext(tenant_key="tenant-a", tenant_slug="any", user_key="u-1", role=TenantRole.GROWER)

    app.dependency_overrides[get_glossary_service] = lambda: glossary
    app.dependency_overrides[get_notification_service] = lambda: notifications
    app.dependency_overrides[get_privacy_service] = lambda: privacy
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_tenant] = _ctx
    # tests/api/conftest.py restores the overrides and resets the limiter.
    yield TestClient(app, raise_server_exceptions=False)


def test_distinct_slugs_share_one_glossary_bucket(app_client: TestClient) -> None:
    budget = _budget(_TERM_RATE_LIMIT)

    statuses = [app_client.get(f"/api/v1/public/glossary/term/term-{i}").status_code for i in range(budget + 1)]

    assert statuses[:budget] == [200] * budget, "precondition: the budget is granted"
    assert statuses[budget] == 429, "a fresh slug opened a fresh bucket"


def test_an_encoded_variant_of_the_path_is_the_same_bucket(app_client: TestClient) -> None:
    budget = _budget(_TERM_RATE_LIMIT)
    for _ in range(budget):
        app_client.get("/api/v1/public/glossary/term/vpd")

    assert app_client.get("/api/v1/public/glossary/term/vpd%20").status_code == 429


def test_distinct_export_keys_share_one_download_bucket(app_client: TestClient) -> None:
    budget = _budget(settings.rate_limit_export_download)

    statuses = [app_client.get(f"/api/v1/privacy/export/exp-{i}/download").status_code for i in range(budget + 1)]

    assert statuses[:budget] == [200] * budget
    assert statuses[budget] == 429


def test_distinct_tenant_slugs_share_one_test_notification_bucket(app_client: TestClient) -> None:
    """Decided in #2052: the test-notification budget is per client address, across tenants.

    It was documented as per address all along (``settings.rate_limit_notification_test``);
    the per-slug bucket was an artefact of ``key_style="url"``, and a member of
    several tenants — or a caller who varies the slug — got the budget once per slug.
    """
    budget = _budget(settings.rate_limit_notification_test)

    statuses = [
        app_client.post(f"/api/v1/t/garden-{i}/notifications/test", json={"channel_key": "email"}).status_code
        for i in range(budget + 1)
    ]

    assert statuses[:budget] == [200] * budget
    assert statuses[budget] == 429
