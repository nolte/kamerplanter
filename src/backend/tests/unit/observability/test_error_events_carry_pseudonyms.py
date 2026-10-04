"""An error event names account and tenant by pseudonym, never by key (#2129, MT-033).

Before #2129 nothing set the event's ``user`` block: an issue in the tracker could
not be attributed to a tenant or told apart from the same error in another
tenant, and the scrubber's allow-list for ``user.id``/``user.tenant`` guarded a
block that never existed.

The measurement drives the real stack in a fresh process, as
``test_error_tracking_redacts_paths.py`` does: the API's process entry with
``SENTRY_DSN`` set (the real ``init_error_tracking`` call and ``before_send``
hook), the real SDK ASGI integration, the real ``get_current_user`` and
``get_current_tenant`` dependencies (only their auth provider and tenant service
are doubles), a request that raises, and a transport stub that keeps what would
have been sent.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

import pytest

from app.common.log_privacy import log_subject, log_tenant
from app.config.settings import settings
from tests.unit.guards.test_privacy_logs_carry_no_plaintext_subject import BACKEND_ROOT

# Assembled at run time: no credential-shaped literal in the source.
USER_KEY = "-".join(("owner", "2129"))
TENANT_KEY = "-".join(("tenant", "2129"))
SALT = "event-user-probe-" * 3

_PROBE = r"""
import json, os
from types import SimpleNamespace
import app.main
import sentry_sdk
from fastapi import APIRouter, Depends
from starlette.testclient import TestClient
from app.common import auth as auth_mod
from app.common.dependencies import get_auth_provider, get_tenant_service
from app.common.enums import TenantRole
from app.domain.models.user import User

events = []

class Stub(sentry_sdk.transport.Transport):
    def capture_envelope(self, envelope):
        for item in envelope.items:
            if item.headers.get("type") == "event":
                events.append(item.payload.json)

client = sentry_sdk.get_client()
assert client.is_active(), "the process entry did not enable error tracking"
client.transport = Stub(client.options)

class AuthProvider:
    def resolve_user(self, authorization, *, client_ip):
        return User(_key=os.environ["PROBE_USER"], email="owner@example.org", display_name="Owner")
    def resolve_user_optional(self, authorization, *, client_ip):
        return self.resolve_user(authorization, client_ip=client_ip)

class TenantService:
    def get_tenant_by_slug(self, slug):
        return SimpleNamespace(key=os.environ["PROBE_TENANT"], slug=slug)
    def get_membership(self, user_key, tenant_key):
        return SimpleNamespace(role=TenantRole.LEAD, admin_scopes=[], is_active=True)

app.main.app.dependency_overrides[get_auth_provider] = AuthProvider
app.main.app.dependency_overrides[get_tenant_service] = TenantService
exec(os.environ.get("PROBE_SETUP", ""))

router = APIRouter()

@router.get("/api/v1/t/{tenant_slug}/probe-2129")
def in_tenant(ctx = Depends(auth_mod.get_current_tenant)):
    raise RuntimeError("tenant request failed")

@router.get("/api/v1/probe-2129-anonymous")
def anonymous():
    raise RuntimeError("anonymous request failed")

app.main.app.include_router(router)
http = TestClient(app.main.app, raise_server_exceptions=False)
http.get("/api/v1/t/garden-2129/probe-2129")
http.get("/api/v1/probe-2129-anonymous")
sentry_sdk.flush()
print("EVENTS=" + json.dumps(events))
"""


def run_probe(setup: str = "") -> list[dict[str, Any]]:
    """The events the real API process reports for one tenant request and one anonymous request."""
    result = subprocess.run(
        [sys.executable, "-W", "ignore", "-c", _PROBE],
        cwd=BACKEND_ROOT,
        env={
            **os.environ,
            "PYTHONPATH": str(BACKEND_ROOT),
            "SENTRY_DSN": "https://public@tracker.invalid/1",
            "SENTRY_ENVIRONMENT": "e2e",
            "LOG_PSEUDONYM_SALT": SALT,
            "PROBE_USER": USER_KEY,
            "PROBE_TENANT": TENANT_KEY,
            "PROBE_SETUP": setup,
        },
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    lines = [line for line in result.stdout.splitlines() if line.startswith("EVENTS=")]
    assert lines, result.stdout + result.stderr
    events = json.loads(lines[-1].removeprefix("EVENTS="))
    assert events, result.stderr
    return events


def _by_route(events: list[dict[str, Any]], marker: str) -> list[dict[str, Any]]:
    found = [event for event in events if marker in str(event.get("transaction"))]
    assert found, [event.get("transaction") for event in events]
    return found


@pytest.fixture(scope="module")
def pseudonyms() -> dict[str, str]:
    original = settings.log_pseudonym_salt
    settings.log_pseudonym_salt = SALT
    try:
        return {"id": str(log_subject(USER_KEY)), "tenant": str(log_tenant(TENANT_KEY))}
    finally:
        settings.log_pseudonym_salt = original


#: #2136: the user block needs the request's ``error_tracking`` consent. The probe
#: replaces only the consent *lookup* (the store), never the decision path.
CONSENT_GRANTED = (
    "import app.observability.event_user as event_user\n"
    "event_user.has_consent = lambda user_key, purpose: purpose == 'error_tracking'\n"
)
CONSENT_REVOKED = (
    "import app.observability.event_user as event_user\nevent_user.has_consent = lambda user_key, purpose: False\n"
)


@pytest.fixture(scope="module")
def captured() -> list[dict[str, Any]]:
    return run_probe(CONSENT_GRANTED)


@pytest.fixture(scope="module")
def captured_without_consent() -> list[dict[str, Any]]:
    return run_probe(CONSENT_REVOKED)


def test_an_event_of_a_tenant_request_names_account_and_tenant_by_pseudonym(
    captured: list[dict[str, Any]], pseudonyms: dict[str, str]
) -> None:
    for event in _by_route(captured, "{tenant_slug}/probe-2129"):
        assert event.get("user") == pseudonyms, event.get("user")


def test_no_event_carries_a_raw_key(captured: list[dict[str, Any]]) -> None:
    for event in captured:
        text = json.dumps(event)
        assert USER_KEY not in text
        assert TENANT_KEY not in text


def test_an_event_without_an_authenticated_principal_carries_no_user(captured: list[dict[str, Any]]) -> None:
    for event in _by_route(captured, "probe-2129-anonymous"):
        assert "user" not in event or not event["user"], event.get("user")


def test_without_error_tracking_consent_the_event_names_nobody(captured_without_consent: list[dict[str, Any]]) -> None:
    """#2136 (MT-040): a revoked ``error_tracking`` consent yields events without a ``user`` block."""
    for event in _by_route(captured_without_consent, "{tenant_slug}/probe-2129"):
        assert "user" not in event or not event["user"], event.get("user")
        text = json.dumps(event)
        assert USER_KEY not in text
        assert TENANT_KEY not in text
