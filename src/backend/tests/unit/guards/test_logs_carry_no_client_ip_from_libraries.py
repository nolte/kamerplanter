"""A third-party logger does not write the full client address (#2054, NFR-011 R-03/L-4).

``slowapi`` logs ``ratelimit <limit> (<limit_key>) exceeded at endpoint: <scope>`` at
WARNING on every 429, and ``limit_key`` is the resolved client address. The
``slowapi`` logger propagates to the root handler, whose redaction masks e-mail
addresses and URL parts but — deliberately, an infrastructure address in a
connection error is what an operator needs — not IP addresses. Measured before the
fix: a 429 for ``203.0.113.77`` wrote that address verbatim.

Driven through the real thing: the project's own limiter (``build_rate_limiter`` with
the sign-in router's key function), slowapi's own exceeded handler, a real route and a
``TestClient`` whose peer address is the probe address, under the API's logging setup.
"""

from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.auth.router import _rate_limit_key
from app.common.log_privacy import loggable_ip
from app.common.rate_limit import build_rate_limiter
from app.config import logging as logging_config
from tests.unit.guards.test_log_redaction_has_no_residual_gaps import _late_handler
from tests.unit.guards.test_logs_carry_no_secrets_runtime import (  # noqa: F401  (fixture, used via usefixtures)
    _configure,
    isolated_logging,
)

PEER_V4 = "203.0.113.77"
PEER_V6 = "2001:db8:abcd:12:aaaa:bbbb:cccc:dddd"


def _exceeded_line(peer: str) -> str:
    limiter = build_rate_limiter(_rate_limit_key, storage_url="memory://")
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    @app.get("/probe")
    @limiter.limit("1/minute")
    async def probe(request: Request) -> dict[str, bool]:
        return {"ok": True}

    late = _late_handler("slowapi")
    with TestClient(app, client=(peer, 50000)) as client:
        assert client.get("/probe").status_code == 200
        assert client.get("/probe").status_code == 429
    return late.stream.getvalue()


@pytest.mark.usefixtures("isolated_logging")
@pytest.mark.parametrize("process", ["api", "worker"])
@pytest.mark.parametrize("peer", [PEER_V4, PEER_V6])
def test_a_429_does_not_log_the_full_client_address(process: str, peer: str) -> None:
    _configure(process)

    text = _exceeded_line(peer)

    assert "exceeded at endpoint" in text, text
    assert peer not in text, text
    assert loggable_ip(peer) in text, text


@pytest.mark.usefixtures("isolated_logging")
def test_a_key_that_is_no_address_is_not_logged_either() -> None:
    _configure("api")
    late = _late_handler("slowapi")

    logging.getLogger("slowapi").warning(
        "ratelimit %s (%s) exceeded at endpoint: %s", "5 per 1 minute", "user:acct-2054", "/x"
    )

    text = late.stream.getvalue()
    assert "exceeded at endpoint" in text, text
    assert "acct-2054" not in text, text


@pytest.mark.usefixtures("isolated_logging")
def test_the_other_slowapi_lines_are_untouched() -> None:
    _configure("api")
    late = _late_handler("slowapi")

    logging.getLogger("slowapi").warning("Rate limit storage unreachable - falling back to in-memory storage")

    assert "falling back to in-memory storage" in late.stream.getvalue()


def test_the_filter_is_installed_once() -> None:
    logging_config.harden_library_loggers()
    logging_config.harden_library_loggers()
    filters = [f for f in logging.getLogger("slowapi").filters if type(f).__name__ == "_ClientAddressFilter"]
    assert len(filters) == 1
