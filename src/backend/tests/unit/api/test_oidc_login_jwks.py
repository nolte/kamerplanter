"""#1987 items 3 and 4 — the login's key fetch is cached and bounded, and ``nbf`` / ``iat`` are checked.

The real auth router, ``AuthService`` and ``OAuthEngine`` run; only the network and DNS are doubled by
:class:`tests.support.oidc_idp.FakeIdp`. The key cache lives in process memory, one per worker — a
second worker fetches on its own, which costs one extra request per worker per TTL and shares no
state, so nothing here needs a lock across processes.

What each test pins:

* every login used to do a discovery GET and a key GET: an IdP outage, or a throttle, was a login outage;
* an unknown ``kid`` causes **one** refetch and no more than one per interval and configuration, so
  forging key ids cannot turn the login into a request generator against the provider;
* a key set larger than any real one is refused rather than buffered, and one unimportable key is skipped;
* a ``jwks_uri`` the provider's discovery document supplies is a URL the server dials, so it goes through
  :mod:`app.common.url_safety` (never the metadata address; a private address only on the provider's own host);
* a failure is remembered for seconds, not for the TTL;
* ``nbf`` is checked with the login skew, and an ``iat`` far in the past is refused.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
import structlog

from app.api.v1.auth.router import limiter
from app.domain.engines import jwks_cache
from tests.support.oidc_idp import FakeIdp
from tests.unit.api.test_oauth_login_id_token import _login, _refused, _signed_in, _world


@pytest.fixture(autouse=True)
def _public_base_url(monkeypatch: pytest.MonkeyPatch):
    from app.config.settings import settings

    monkeypatch.setattr(settings, "app_base_url", "https://kamerplanter.example")


@pytest.fixture(autouse=True)
def _limiter_off(monkeypatch: pytest.MonkeyPatch):
    limiter.reset()
    monkeypatch.setattr(limiter, "enabled", False)
    yield
    limiter.reset()


@pytest.fixture
def idp(monkeypatch: pytest.MonkeyPatch) -> FakeIdp:
    provider = FakeIdp()
    provider.install(monkeypatch)
    return provider


def _reason(idp: FakeIdp, **claims: Any) -> tuple[str | None, bool]:
    """Run one login; return the logged refusal reason (if any) and whether it signed in."""
    world = _world(idp)
    with structlog.testing.capture_logs() as logs:
        callback = _login(world, idp, **claims)
    reasons = [entry["reason"] for entry in logs if entry["event"] == "oauth_login_refused"]
    return (reasons[0] if reasons else None), _signed_in(world, callback)


# ── the cache ────────────────────────────────────────────────────────────────


def test_the_second_login_reuses_the_keys_and_the_discovery_it_resolved(idp: FakeIdp) -> None:
    first = _world(idp)
    assert _signed_in(first, _login(first, idp))
    second = _world(idp)

    assert _signed_in(second, _login(second, idp))

    assert idp.jwks_requests == 1
    assert len(idp.discovery_requests) == 1


def _signs_in(idp: FakeIdp, **claims: Any) -> bool:
    """One login in a world of its own (the harness records one session per world)."""
    world = _world(idp)
    return _signed_in(world, _login(world, idp, **claims))


def test_the_keys_are_fetched_again_once_the_ttl_has_passed(idp: FakeIdp) -> None:
    assert _signs_in(idp)

    idp.advance(jwks_cache.JWKS_TTL_SECONDS - 1)
    assert _signs_in(idp)
    assert idp.jwks_requests == 1

    idp.advance(2)
    assert _signs_in(idp)
    assert idp.jwks_requests == 2


def test_a_rotated_key_is_picked_up_with_one_refetch_once_the_interval_allows(idp: FakeIdp) -> None:
    assert _signs_in(idp)
    idp.rotate("idp-key-2")
    idp.advance(jwks_cache.JWKS_REFETCH_MIN_INTERVAL_SECONDS + 1)

    assert _signs_in(idp)

    assert idp.jwks_requests == 2


def test_forged_key_ids_cannot_force_a_fetch_per_login(idp: FakeIdp) -> None:
    """The bound on the refetch: an attacker naming fresh ``kid``s costs the provider one request per interval."""
    assert _signs_in(idp)
    assert idp.jwks_requests == 1
    idp.forge_with = "attacker-key"

    for attempt in range(10):
        idp.token_header_kid = f"made-up-{attempt}"
        assert not _signs_in(idp)
    assert idp.jwks_requests == 1  # inside the interval: no refetch at all

    idp.advance(jwks_cache.JWKS_REFETCH_MIN_INTERVAL_SECONDS + 1)
    for attempt in range(10):
        idp.token_header_kid = f"made-up-later-{attempt}"
        assert not _signs_in(idp)
    assert idp.jwks_requests == 2  # one refetch for the whole batch


def test_a_failure_is_remembered_for_the_negative_ttl_only(idp: FakeIdp) -> None:
    idp.jwks_status = 503
    assert not _signs_in(idp)
    assert idp.jwks_requests == 1
    idp.jwks_status = 200

    # Still inside the negative TTL: refused without asking the provider again.
    assert not _signs_in(idp)
    assert idp.jwks_requests == 1

    idp.advance(jwks_cache.JWKS_NEGATIVE_TTL_SECONDS + 1)
    assert _signs_in(idp)
    assert idp.jwks_requests == 2


def test_the_negative_ttl_is_far_shorter_than_the_positive_one() -> None:
    assert jwks_cache.JWKS_NEGATIVE_TTL_SECONDS * 5 <= jwks_cache.JWKS_TTL_SECONDS


# ── the response ─────────────────────────────────────────────────────────────


def test_a_key_set_larger_than_the_cap_is_refused(idp: FakeIdp) -> None:
    idp.jwks_padding = jwks_cache.JWKS_MAX_BYTES + 1

    reason, signed_in = _reason(idp)

    assert (reason, signed_in) == ("jwks_unavailable", False)


def test_a_key_set_just_inside_the_cap_is_accepted(idp: FakeIdp) -> None:
    idp.jwks_padding = jwks_cache.JWKS_MAX_BYTES - len(str(idp.jwks())) - 200

    reason, signed_in = _reason(idp)

    assert (reason, signed_in) == (None, True)


def test_an_oversized_discovery_document_is_refused(idp: FakeIdp) -> None:
    idp.discovery_padding = jwks_cache.JWKS_MAX_BYTES + 1

    reason, signed_in = _reason(idp)

    assert (reason, signed_in) == ("jwks_unavailable", False)


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param({"kty": "quantum", "kid": "q"}, id="unknown key type"),
        pytest.param({"kid": "no-type"}, id="no key type"),
        pytest.param({"kty": "RSA", "n": "!!", "e": "AQAB", "kid": "broken"}, id="malformed RSA key"),
        pytest.param({"kty": "oct", "k": "AAAA", "kid": "symmetric"}, id="symmetric key"),
        pytest.param("not-an-object", id="not an object"),
    ],
)
def test_one_unusable_key_in_the_set_is_skipped_not_fatal(idp: FakeIdp, bad: Any) -> None:
    idp.bad_jwks_entries = [bad]

    reason, signed_in = _reason(idp)

    assert (reason, signed_in) == (None, True)


def test_a_set_with_no_usable_key_refuses_the_login(idp: FakeIdp) -> None:
    idp.bad_jwks_entries = [{"kty": "quantum", "kid": "q"}]
    idp.published_kids = []

    reason, signed_in = _reason(idp)

    assert (reason, signed_in) == ("jwks_unavailable", False)


# ── the address of the key endpoint ──────────────────────────────────────────


@pytest.mark.parametrize(
    "jwks_uri",
    [
        pytest.param("https://169.254.169.254/jwks", id="cloud metadata address"),
        pytest.param("https://[fd00:ec2::254]/jwks", id="cloud metadata, IPv6"),
        pytest.param("http://idp-a.example/jwks", id="plain http"),
        pytest.param("https://keys.internal.example/jwks", id="another host that resolves to a private address"),
    ],
)
def test_a_key_endpoint_the_discovery_document_points_at_internally_is_never_dialled(
    idp: FakeIdp, jwks_uri: str
) -> None:
    idp.discovery_extra = {"jwks_uri": jwks_uri}
    idp.dns = {"keys.internal.example": "10.0.0.5"}

    reason, signed_in = _reason(idp)

    assert (reason, signed_in) == ("jwks_unavailable", False)
    assert idp.jwks_requests == 0


def test_a_self_hosted_provider_on_a_private_address_may_publish_keys_on_its_own_host(idp: FakeIdp) -> None:
    idp.dns = {"idp-a.example": "10.0.0.5"}

    reason, signed_in = _reason(idp)

    assert (reason, signed_in) == (None, True)


# ── nbf and iat ──────────────────────────────────────────────────────────────


def test_a_token_that_is_not_valid_yet_signs_nobody_in(idp: FakeIdp) -> None:
    reason, signed_in = _reason(idp, nbf=int(time.time()) + 3600)

    assert (reason, signed_in) == ("nbf", False)


@pytest.mark.parametrize("offset", [-3600, -1, 0, 10])
def test_nbf_inside_the_skew_is_accepted(idp: FakeIdp, offset: int) -> None:
    reason, signed_in = _reason(idp, nbf=int(time.time()) + offset)

    assert (reason, signed_in) == (None, True)


@pytest.mark.parametrize("nbf", ["tomorrow", None, [1], True, float("inf")])
def test_a_malformed_nbf_is_refused_rather_than_ignored(idp: FakeIdp, nbf: Any) -> None:
    reason, signed_in = _reason(idp, nbf=nbf)

    assert (reason, signed_in) == ("nbf", False)


def test_a_token_without_nbf_is_fine(idp: FakeIdp) -> None:
    assert _reason(idp) == (None, True)


def test_an_iat_far_in_the_past_is_refused(idp: FakeIdp) -> None:
    reason, signed_in = _reason(idp, iat=int(time.time()) - 7200, exp=int(time.time()) + 600)

    assert (reason, signed_in) == ("iat", False)


@pytest.mark.parametrize("age", [0, 30, 300])
def test_a_recent_iat_is_accepted(idp: FakeIdp, age: int) -> None:
    reason, signed_in = _reason(idp, iat=int(time.time()) - age)

    assert (reason, signed_in) == (None, True)


# ── what the security review of #1987 found ──────────────────────────────────


@pytest.mark.parametrize(
    "setup",
    [
        pytest.param(lambda idp: setattr(idp, "jwks_raw", "[" * 200_000), id="a document of nested brackets"),
        pytest.param(
            lambda idp: setattr(idp, "discovery_extra", {"jwks_uri": "https://idp-a.example:99999/jwks"}),
            id="a port out of range",
        ),
    ],
)
def test_a_failure_of_any_kind_is_cached_like_every_other(idp: FakeIdp, setup: Any) -> None:
    """An exception outside the enumerated ones used to skip the negative cache: every login fetched again."""
    setup(idp)

    assert _reason(idp) == ("jwks_unavailable", False)
    assert _reason(idp) == ("jwks_unavailable", False)

    assert len(idp.discovery_requests) <= 1
    assert idp.jwks_requests <= 1


def test_a_response_that_dribbles_in_is_cut_off_at_the_deadline(idp: FakeIdp, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.domain.engines import oauth_engine

    clock = {"now": 0.0}

    def monotonic() -> float:
        clock["now"] += 1.0  # every look at the clock is a second
        return clock["now"]

    monkeypatch.setattr(oauth_engine.time, "monotonic", monotonic)
    idp.jwks_dribble = True

    assert _reason(idp) == ("jwks_unavailable", False)


def test_the_key_request_asks_for_an_uncompressed_body(idp: FakeIdp) -> None:
    """The cap counts decoded bytes, and a decoder inflates a whole raw chunk at once."""
    assert _reason(idp) == (None, True)

    assert [h["accept-encoding"] for h in idp.jwks_request_headers] == ["identity"]


def test_a_provider_claim_of_the_wrong_type_is_logged_by_type_only(idp: FakeIdp) -> None:
    world = _world(idp, userinfo=True)
    idp.userinfo = {"sub": SUB, "email": 123456789012, "email_verified": True}

    with structlog.testing.capture_logs() as logs:
        callback = _login(world, idp)

    _refused(world, callback)
    rendered = str(logs)
    assert "123456789012" not in rendered
    assert [e["reason"] for e in logs if e["event"] == "oauth_endpoint_refused"] == ["ValidationError"]


SUB = "sub-a"
