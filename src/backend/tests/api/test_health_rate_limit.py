"""`GET /api/health` is bounded per client IP (#1210, SEC-003).

The gap, as measured: `app/api/v1/auth/router.py` builds the one process-wide
`Limiter` **without** `default_limits`, and SlowAPI then bounds only the routes
that carry a `@limiter.limit` decorator. `/api/health` carried none. It is
unauthenticated by design — major negotiation (#1124) happens before a client has
a token — and it does real work on every call: it walks the entire router graph
for `supported_majors` and, where those integrations are enabled, performs
**synchronous** probes into TimescaleDB and the knowledge service. That last part
is the amplification that matters: an unauthenticated caller could drive load into
internal services one cheap request at a time.

Why the route is decorated instead of the limiter being given `default_limits`:
a default applies to *every* route in the application at once, silently re-pricing
surfaces nobody looked at as part of this change. The blast radius of a global
default is the whole API; the blast radius of a decorator is this endpoint.

**What is deliberately NOT limited.** The Kubernetes liveness and readiness
probes hit `/api/v1/health/live` and `/api/v1/health/ready`
(`helm/kamerplanter/values.yaml`), not this route. Throttling a kubelet would
restart healthy pods — a self-inflicted outage in the name of hardening — so the
budget here must never be assumed to cover them, and
`test_the_cluster_probe_routes_are_not_the_limited_one` fails if the two ever
converge onto one path.

The budget is read from `settings.rate_limit_health` rather than hard-coded: a
test that spells out "60" would go red on an operator's tuning instead of on a
removed limit, which is the opposite of what it is for.

Isolation: `tests/api/conftest.py::reset_rate_limiter` hands every test a full
budget and takes it back afterwards (#989), so spending it here — which a
rate-limit test must do — cannot make a later module fail.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config.settings import settings
from app.main import app

ENDPOINT = "/api/health"


def _budget() -> int:
    """Calls granted per window, derived from the setting rather than repeated."""
    return int(settings.rate_limit_health.split("/")[0])


def _spend(client: TestClient, count: int) -> list[int]:
    return [client.get(ENDPOINT).status_code for _ in range(count)]


def test_the_budget_is_generous_enough_for_real_clients() -> None:
    """A limit tight enough to fire on legitimate polling would be a worse defect.

    A Home Assistant integration polls on the order of once a minute and several
    clients can share one NAT address; an operator during an incident adds a
    handful of manual calls. Anything below a few dozen a minute would turn this
    hardening into an outage for the very consumers the endpoint exists for.
    """
    assert _budget() >= 30, f"rate_limit_health={settings.rate_limit_health!r} can fire on ordinary polling"


def test_the_endpoint_serves_a_full_budget_before_refusing() -> None:
    """The limit bounds abuse without breaking the normal case.

    Asserted as "all of them succeed", not "the first one does": a limiter
    misconfigured to a tiny budget would satisfy the 429 assertion below while
    making the endpoint useless.
    """
    client = TestClient(app)

    assert _spend(client, _budget()) == [200] * _budget()


def test_exceeding_the_budget_returns_429() -> None:
    """The load-bearing assertion — without it, nothing here proves a limit exists.

    Every request in this test comes from the same `TestClient` IP and the same
    path, i.e. one bucket, which is exactly the shape of the flood being bounded.
    """
    client = TestClient(app)
    _spend(client, _budget())

    response = client.get(ENDPOINT)

    assert response.status_code == 429, response.text


def test_the_refusal_does_not_leak_the_payload() -> None:
    """A 429 must not still answer the question it refused to answer.

    If the limiter ran *after* the handler — or if a future refactor moved it into
    a middleware that annotates rather than short-circuits — the body would still
    carry `supported_majors` and, on an opted-in instance, the build revision. The
    limit would then bound nothing at all while looking enforced.
    """
    client = TestClient(app)
    _spend(client, _budget())

    body = client.get(ENDPOINT).text

    assert "supported_majors" not in body
    assert "build_revision" not in body


def test_a_spent_public_budget_does_not_take_the_liveness_probe_down() -> None:
    """The kubelet's path must survive a flood on the public one.

    `helm/kamerplanter/values.yaml` points liveness at `/api/v1/health/live`. If
    that probe ever shared this budget — because the chart was repointed, or
    because a later "just add `default_limits`" refactor bounded every route at
    once — a burst of anonymous traffic would start failing liveness checks and
    Kubernetes would restart healthy pods. Hardening that causes the outage it was
    meant to prevent.

    Asserted behaviourally, after the public budget is provably spent: a structural
    "these two strings differ" check would pass just as well while both routes hung
    off one global limit.
    """
    client = TestClient(app)
    _spend(client, _budget())
    assert client.get(ENDPOINT).status_code == 429, "precondition: the public budget must be spent"

    probe = client.get("/api/v1/health/live")

    assert probe.status_code == 200, probe.text
    assert probe.json()["status"] == "alive"
