"""One source cannot spend the owner's password-reset budget (#2059).

Until #2059 the reset budget (#2043) counted per address only, and every
request — above the budget too — renewed its one-hour window. One request an
hour kept an address above the budget; the owner then got no link, from
anywhere. Measured on the real route with a fake clock, the per-IP limit of
20/minute modelled as 3 s per request: one source held 1000 (and 1199)
addresses after three setup passes; 100 owners asking from their own address
received **0** links. (At exactly 1200 the window — renewed every 3600 s —
expires on the next request, so 1199 is the ceiling, not the issue's 1200.)

The budget has two stages now, both reserved before any lookup:

1. per address **and** source address: three requests, the window renewed by
   that source's own requests — a source that keeps asking keeps only itself
   out;
2. per address over all sources: ten links, counted and renewed only by
   requests stage 1 admitted — the bound on mail to one inbox.

The request that first crosses a stage logs ``password_reset_budget_exhausted``
with the stage and a keyed digest of the address; never the address, never
the source. There is no admin path that clears a budget (operator decision,
#2059).

Driven through the real route; the source is the ``X-Forwarded-For`` entry
``resolve_client_ip`` reads at the default ``TRUSTED_PROXY_HOPS=0``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from structlog.testing import capture_logs

from app.api.v1.auth.router import limiter
from app.common.decoys import UNAVAILABLE_EMAIL_DIGEST, email_digest
from app.config.settings import settings
from app.data_access.external.step_up_throttle import PASSWORD_RESET_WINDOW_SECONDS, anonymous_budget_fallback
from app.domain.models.user import User
from app.domain.services.auth_service import (
    MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW,
    MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW,
)
from tests.api import test_auth_password_reset_budget as reset_flow

ATTACKER = "203.0.113.66"
OWNER_IP = "192.0.2.10"

_client = contextmanager(reset_flow._client)


class _Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 4, 0, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture
def clock() -> _Clock:
    return _Clock()


@pytest.fixture
def world(clock: _Clock) -> reset_flow._World:
    return reset_flow._World(budget=anonymous_budget_fallback(PASSWORD_RESET_WINDOW_SECONDS, clock=clock))


@pytest.fixture
def client(world: reset_flow._World) -> Iterator[TestClient]:
    with _client(world) as test_client:
        yield test_client


def _post(client: TestClient, clock: _Clock, email: str, source: str) -> int:
    clock.now += timedelta(seconds=3)  # 20/minute: the default per-IP limit of the route
    response = client.post(reset_flow._ROUTE, json={"email": email}, headers={"X-Forwarded-For": source})
    return response.status_code


def test_a_source_holding_the_address_above_its_budget_does_not_lock_the_owner_out(
    world: reset_flow._World, client: TestClient, clock: _Clock
) -> None:
    for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 5):
        _post(client, clock, reset_flow.OWNER, ATTACKER)
    assert world.mail.count(reset_flow.OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW

    assert _post(client, clock, reset_flow.OWNER, OWNER_IP) == 200

    assert world.mail.count(reset_flow.OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 1


def test_one_source_holding_many_addresses_at_its_full_rate_locks_none_of_their_owners(
    world: reset_flow._World, client: TestClient, clock: _Clock
) -> None:
    """The measured attack at reduced scale: setup passes, then one request per address and hour."""
    limiter.enabled = False  # the per-IP limit is modelled by the clock; conftest re-enables it
    victims = [f"victim-{i}@example.org" for i in range(60)]
    for i, victim in enumerate(victims):
        world.repo.users[victim] = User(
            _key=str(3_000_000 + i), email=victim, display_name="V", password_hash=reset_flow._PASSWORD_HASH
        )
    for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 2):
        for victim in victims:
            _post(client, clock, victim, ATTACKER)
    before = len(world.mail.sent)

    for victim in victims[::6]:
        _post(client, clock, victim, OWNER_IP)

    assert len(world.mail.sent) - before == len(victims[::6])


def test_one_inbox_gets_no_more_than_the_overall_budget_from_many_sources(
    world: reset_flow._World, client: TestClient, clock: _Clock
) -> None:
    sources = [f"198.51.100.{i}" for i in range(1, 8)]
    for source in sources:
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW):
            _post(client, clock, reset_flow.OWNER, source)

    assert len(sources) * MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW > MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW
    assert world.mail.count(reset_flow.OWNER) == MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW


def test_requests_the_source_stage_refuses_do_not_spend_the_overall_budget(
    world: reset_flow._World, client: TestClient, clock: _Clock
) -> None:
    limiter.enabled = False
    for _ in range(200):
        _post(client, clock, reset_flow.OWNER, ATTACKER)

    for source in ("192.0.2.1", "192.0.2.2"):
        _post(client, clock, reset_flow.OWNER, source)

    assert world.mail.count(reset_flow.OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 2


def test_the_overall_budget_refills_an_hour_after_the_last_admitted_request(
    world: reset_flow._World, client: TestClient, clock: _Clock
) -> None:
    for i in range(4):
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW):
            _post(client, clock, reset_flow.OWNER, f"198.51.100.{i}")
    assert world.mail.count(reset_flow.OWNER) == MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW

    clock.now += timedelta(seconds=PASSWORD_RESET_WINDOW_SECONDS + 1)
    _post(client, clock, reset_flow.OWNER, OWNER_IP)

    assert world.mail.count(reset_flow.OWNER) == MAX_PASSWORD_RESETS_PER_ADDRESS_PER_WINDOW + 1


def test_crossing_a_stage_logs_one_digest_and_no_address(
    client: TestClient, clock: _Clock, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Without a salt the digest is the constant "unavailable" for every address,
    # and the comparison below would hold for any address at all.
    monkeypatch.setattr(settings, "log_pseudonym_salt", "a-log-pseudonym-salt-of-sufficient-length-2059")
    assert email_digest(reset_flow.OWNER) not in {UNAVAILABLE_EMAIL_DIGEST, email_digest(reset_flow.SECOND)}

    with capture_logs() as logs:
        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 3):
            _post(client, clock, reset_flow.OWNER, ATTACKER)
        for i in range(4):
            for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW):
                _post(client, clock, reset_flow.OWNER, f"198.51.100.{i}")

    events = [entry for entry in logs if entry["event"] == "password_reset_budget_exhausted"]
    assert [entry["stage"] for entry in events] == ["address_source", "address"], events
    assert {entry["email_digest"] for entry in events} == {email_digest(reset_flow.OWNER)}
    rendered = repr(events)
    assert reset_flow.OWNER not in rendered
    assert ATTACKER not in rendered
