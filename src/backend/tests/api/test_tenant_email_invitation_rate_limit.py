"""``POST /api/v1/tenants/{slug}/invitations/email`` is rate-limited per account (#2162 review W-1).

Since #2162 every call mails an address the caller names and does not have to own, and any account holds
``management`` in a tenant it founds. The per-minute burst is ``settings.rate_limit_invitation_email``,
keyed on the account (``user_rate_limit_key``); the daily ceiling is the service's
(``tests/integration/test_email_invitation_delivery_reach.py``).
"""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.common.auth import get_current_tenant, get_current_user
from app.common.dependencies import get_tenant_service
from app.common.enums import AdminScope, TenantRole
from app.config.settings import settings
from app.domain.models.invitation import InvitationLink
from app.domain.models.tenant_context import TenantContext
from app.domain.models.user import User


def _allowed_calls() -> int:
    return int(settings.rate_limit_invitation_email.split("/")[0])


@pytest.fixture
def service() -> MagicMock:
    service = MagicMock()
    service.create_email_invitation.return_value = InvitationLink(
        invitation_key="i1",
        token="tok",
        expires_at=datetime.now(UTC) + timedelta(days=7),
        accept_url="https://app.test/invitations/accept?token=tok",
        delivered=True,
    )
    return service


@pytest.fixture
def client(service: MagicMock) -> Iterator[TestClient]:
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        app.dependency_overrides[get_tenant_service] = lambda: service
        app.dependency_overrides[get_current_user] = lambda: User(
            _key="u-lead", email="lead@example.com", display_name="Lead", is_active=True
        )
        app.dependency_overrides[get_current_tenant] = lambda: TenantContext(
            tenant_key="t1",
            tenant_slug="garden",
            user_key="u-lead",
            role=TenantRole.LEAD,
            admin_scopes=[AdminScope.MANAGEMENT],
        )
        try:
            yield TestClient(app, raise_server_exceptions=False)
        finally:
            for dependency in (get_tenant_service, get_current_user, get_current_tenant):
                app.dependency_overrides.pop(dependency, None)


def _invite(client: TestClient, n: int):  # noqa: ANN202 - httpx Response
    return client.post(
        "/api/v1/tenants/garden/invitations/email", json={"email": f"f{n}@example.com", "role": "viewer"}
    )


def test_the_burst_is_granted_then_refused_without_reaching_the_service(client: TestClient, service: MagicMock) -> None:
    granted = [_invite(client, n) for n in range(_allowed_calls())]

    refused = _invite(client, 99)

    assert {r.status_code for r in granted} == {201}
    assert refused.status_code == 429
    assert service.create_email_invitation.call_count == _allowed_calls()


def test_the_limit_is_stricter_than_the_interactive_auth_budget() -> None:
    per_hour = {"minute": 60, "hour": 1, "day": 1 / 24}
    count, unit = settings.rate_limit_invitation_email.split("/")
    auth_count, auth_unit = settings.rate_limit_auth.split("/")

    assert int(count) * per_hour[unit] < int(auth_count) * per_hour[auth_unit]
