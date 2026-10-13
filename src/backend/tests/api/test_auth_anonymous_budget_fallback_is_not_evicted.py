"""The in-process tier of the anonymous mail budgets is not evicted by a flood (#2058).

While Valkey is unreachable the per-address budgets of
``POST /auth/password-reset/request`` (#2043) and ``POST /auth/resend-verification``
(#2037) count in a bounded in-process map. Every submitted address takes an
entry, known or not, and the map evicted its oldest entry (LRU) once full — and
with it that address's spent budget. Measured before the fix through the real
reset route, fake clock, Valkey failing: the victim's 4 requests sent 3 mails;
4096 invented addresses later the victim's next request sent a 4th.

Now these two budgets never evict a live entry: a full map first drops the
entries whose window has passed, and if it is still full a **new** address is
answered as over its budget — silently, the same ``200``/``202``, no mail —
until entries expire. Their capacity is larger than the step-up's, so filling
the map takes four times the addresses.

Driven through the real routes; the capacity is shrunk through the same
factory production builds the two stores with, so the route exercises the
production policy rather than a test double of it.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest

from app.api.v1.auth.router import limiter
from app.data_access.external.step_up_throttle import (
    ANONYMOUS_BUDGET_FALLBACK_CAPACITY,
    DEFAULT_PASSWORD_RESET_STORE,
    DEFAULT_VERIFICATION_RESEND_STORE,
    PASSWORD_RESET_WINDOW_SECONDS,
    VERIFICATION_RESEND_WINDOW_SECONDS,
    MemoryStepUpThrottleStore,
    RedisStepUpThrottleStore,
    anonymous_budget_fallback,
)
from app.domain.services.auth_service import (
    MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW,
    MAX_VERIFICATION_RESENDS_PER_WINDOW,
)
from tests.api import test_auth_password_reset_budget as reset_flow
from tests.api import test_auth_resend_verification as resend_flow

#: Small enough to fill through the route in a test, same policy as production.
_CAPACITY = 8

_reset_client = contextmanager(reset_flow._client)
_resend_client = contextmanager(resend_flow._client)


class _Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@pytest.fixture(autouse=True)
def _many_sources() -> None:
    """The flood needs many source addresses; the per-IP limit is not what is tested here."""
    limiter.enabled = False  # tests/api/conftest.py turns it back on


def _flood(post: Callable[[str], object], clock: _Clock, count: int) -> None:
    for i in range(count):
        clock.now += timedelta(seconds=1)
        post(f"filler-{i}@example.net")


def test_the_reset_budget_of_a_victim_survives_a_flood_during_an_outage() -> None:
    clock = _Clock()
    fallback = anonymous_budget_fallback(PASSWORD_RESET_WINDOW_SECONDS, capacity=_CAPACITY, clock=clock)
    world = reset_flow._World(
        budget=RedisStepUpThrottleStore(
            reset_flow._BrokenRedis(), ttl_seconds=PASSWORD_RESET_WINDOW_SECONDS, fallback=fallback
        )
    )
    with _reset_client(world) as client:

        def post(email: str) -> object:
            return client.post(reset_flow._ROUTE, json={"email": email})

        for _ in range(MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW + 1):
            post(reset_flow.OWNER)
        assert world.mail.count(reset_flow.OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW

        _flood(post, clock, _CAPACITY * 2)
        answer = post(reset_flow.OWNER)

    assert answer.status_code == 200  # type: ignore[attr-defined]
    assert world.mail.count(reset_flow.OWNER) == MAX_PASSWORD_RESET_REQUESTS_PER_WINDOW, (
        "the flood evicted the spent budget"
    )


def test_the_resend_budget_of_a_victim_survives_a_flood_during_an_outage() -> None:
    clock = _Clock()
    fallback = anonymous_budget_fallback(VERIFICATION_RESEND_WINDOW_SECONDS, capacity=_CAPACITY, clock=clock)
    world = resend_flow._World()
    world.budget = RedisStepUpThrottleStore(
        reset_flow._BrokenRedis(), ttl_seconds=VERIFICATION_RESEND_WINDOW_SECONDS, fallback=fallback
    )
    with _resend_client(world) as client:

        def post(email: str) -> object:
            return client.post(resend_flow._ROUTE, json={"email": email})

        for _ in range(MAX_VERIFICATION_RESENDS_PER_WINDOW + 1):
            post(resend_flow.UNVERIFIED)
        sent = len(world.mail.sent)
        assert sent == MAX_VERIFICATION_RESENDS_PER_WINDOW

        _flood(post, clock, _CAPACITY * 2)
        answer = post(resend_flow.UNVERIFIED)

    assert answer.status_code == 202  # type: ignore[attr-defined]
    assert len(world.mail.sent) == sent, "the flood evicted the spent budget"


def test_a_full_map_admits_new_addresses_again_once_entries_expire() -> None:
    """Refusing new subjects is bounded by the window, not permanent."""
    clock = _Clock()
    fallback = anonymous_budget_fallback(PASSWORD_RESET_WINDOW_SECONDS, capacity=_CAPACITY, clock=clock)
    world = reset_flow._World(
        budget=RedisStepUpThrottleStore(
            reset_flow._BrokenRedis(), ttl_seconds=PASSWORD_RESET_WINDOW_SECONDS, fallback=fallback
        )
    )
    with _reset_client(world) as client:

        def post(email: str) -> object:
            return client.post(reset_flow._ROUTE, json={"email": email})

        _flood(post, clock, _CAPACITY)
        post(reset_flow.SECOND)
        refused_while_full = world.mail.count(reset_flow.SECOND)

        clock.now += timedelta(seconds=PASSWORD_RESET_WINDOW_SECONDS + 1)
        post(reset_flow.SECOND)

    assert refused_while_full == 0, "a new address was admitted into a full map"
    assert world.mail.count(reset_flow.SECOND) == 1


@pytest.mark.parametrize(
    "store",
    [DEFAULT_PASSWORD_RESET_STORE, DEFAULT_VERIFICATION_RESEND_STORE],
    ids=["password_reset", "verification_resend"],
)
def test_the_wired_anonymous_budgets_use_the_non_evicting_policy(store: MemoryStepUpThrottleStore) -> None:
    assert store.refuses_new_subjects_when_full
    assert store.capacity == ANONYMOUS_BUDGET_FALLBACK_CAPACITY
