"""``GET /api/v1/privacy/export/{key}/download`` must be rate-limited (#1666).

Every call streams a complete copy of an account's personal data. Its sibling
write routes carry a limit (``request_email_change``, ``confirm_email_change``);
this one carried none. See ``settings.rate_limit_export_download`` for the
number and its derivation.
"""

from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_user
from app.common.dependencies import get_privacy_service
from app.config.settings import settings
from app.domain.models.privacy import DataExportRequest

_PER_HOUR = {"minute": 60, "hour": 1, "day": 1 / 24}


def _per_hour(budget: str) -> float:
    count, unit = budget.split("/")
    return int(count) * _PER_HOUR[unit]


def _allowed_calls() -> int:
    return int(settings.rate_limit_export_download.split("/")[0])


async def _bytes() -> AsyncIterator[bytes]:
    yield b'{"ok": true}'


@pytest.fixture
def service() -> MagicMock:
    service = MagicMock()

    async def _open(user_key: str, export_key: str):
        return DataExportRequest(key=export_key, user_key=user_key, status="completed"), _bytes()

    service.open_export_bundle = AsyncMock(side_effect=_open)
    return service


@pytest.fixture
def client(service: MagicMock) -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        user = MagicMock()
        user.key = "u-1"
        # A session principal: a MagicMock would answer any attribute, including
        # the API-key tenant scope, and read as a scoped key (#1851).
        user.api_key_tenant_scope = None
        app.dependency_overrides[get_privacy_service] = lambda: service
        app.dependency_overrides[get_current_user] = lambda: user
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            app.dependency_overrides.pop(get_privacy_service, None)
            app.dependency_overrides.pop(get_current_user, None)


def _download(client: TestClient, key: str = "exp-1"):  # noqa: ANN202 - httpx Response
    return client.get(f"/api/v1/privacy/export/{key}/download")


class TestExportDownloadIsRateLimited:
    def test_the_budget_is_granted_then_refused(self, client: TestClient) -> None:
        allowed = [_download(client) for _ in range(_allowed_calls())]
        refused = _download(client)

        assert {response.status_code for response in allowed} == {200}
        assert allowed[0].content == b'{"ok": true}'
        assert refused.status_code == 429

    def test_a_refused_call_never_opens_the_bundle(self, client: TestClient, service: MagicMock) -> None:
        for _ in range(_allowed_calls()):
            _download(client)
        assert service.open_export_bundle.await_count == _allowed_calls()

        refused = _download(client)

        assert refused.status_code == 429
        assert service.open_export_bundle.await_count == _allowed_calls()

    def test_the_budget_is_the_configured_one(self) -> None:
        from app.api.v1.privacy import router as privacy_router

        assert privacy_router.settings.rate_limit_export_download == settings.rate_limit_export_download

    def test_it_is_sized_between_the_mail_budget_and_the_interactive_one(self) -> None:
        """A download is a deliberate act a few times per export, not an interactive retry surface."""
        download = _per_hour(settings.rate_limit_export_download)

        assert download > _per_hour(settings.rate_limit_email_change)
        assert download < _per_hour(settings.rate_limit_auth)
