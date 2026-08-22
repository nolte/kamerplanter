"""`GET /api/health` reports which build is running — or admits it does not know (#1210).

**The problem this closes.** The endpoint's only build-ish field was ``version``,
served from ``settings.app_version``: the string ``"1.0.0"``, unchanged since the
initial commit, matching none of the releases the project actually published
(v0.0.1 → v0.2.0). An operator with a fix merged two days ago could not ask a
running instance whether it contained that fix. #1210 itself had to answer that
question by reproducing a 500.

**The load-bearing test is the negative one.** ``version`` proves that a
confidently-wrong build identity survives for years without anyone noticing,
because a wrong answer looks exactly like a right one. So the property worth
pinning is not "the fields exist" — it is that an *unstamped* process says
``"unknown"`` and never produces a plausible-looking value.
:class:`TestAnUnstampedBuildAdmitsIt` is that falsification; without it,
:class:`TestAStampedBuildIsReported` would pass just as happily against an
implementation that fell back to ``app_version`` or to a baked-in SHA.

The delivery leg — CI actually passing the values into the image environment —
is pinned separately in ``tests/unit/test_build_identity_delivery_chain.py``,
because every test in this file stays green when that leg is missing.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings, settings
from app.main import app

#: What an image stamp looks like, so the tests use realistic inputs rather than
#: values the production path could never see.
_A_REAL_SHA = "37cbc06fcf0c7d69c07f7abbd3d485cb241070da"
_A_REAL_TIMESTAMP = "2026-08-16T14:28:39.211Z"


@pytest.fixture
def stamp(monkeypatch: pytest.MonkeyPatch):
    """Set the build stamp on the settings singleton the endpoint reads."""

    def _stamp(commit: str, timestamp: str) -> None:
        monkeypatch.setattr(settings, "build_commit", commit)
        monkeypatch.setattr(settings, "build_timestamp", timestamp)

    return _stamp


def _health() -> dict:
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200, response.text
    return response.json()


class TestAStampedBuildIsReported:
    """A published image passes its identity through to the endpoint."""

    def test_the_commit_and_build_time_reach_the_response(self, stamp) -> None:
        stamp(_A_REAL_SHA, _A_REAL_TIMESTAMP)

        body = _health()

        assert body["commit"] == _A_REAL_SHA
        assert body["built_at"] == _A_REAL_TIMESTAMP

    def test_the_two_fields_are_not_crossed(self, stamp) -> None:
        """Distinguishable values, because two swapped fields would satisfy any
        assertion that only checked "both are present and non-empty"."""
        stamp("commit-value", "timestamp-value")

        body = _health()

        assert body["commit"] == "commit-value"
        assert body["built_at"] == "timestamp-value"

    def test_the_value_is_read_per_request_not_frozen_at_import(self, stamp) -> None:
        """The endpoint must read the stamp when asked. A value captured into a
        module-level constant at import time would pass the test above and then
        report the wrong build for the lifetime of a reloaded process."""
        stamp("first-sha", _A_REAL_TIMESTAMP)
        assert _health()["commit"] == "first-sha"

        stamp("second-sha", _A_REAL_TIMESTAMP)
        assert _health()["commit"] == "second-sha"


class TestAnUnstampedBuildAdmitsIt:
    """The falsification: no stamp must produce no claim.

    A local checkout, a compose run and this very test suite all reach the
    endpoint with nothing set. Each of them must be visibly unidentified.
    """

    def test_a_missing_stamp_is_reported_as_unknown(self, stamp) -> None:
        stamp("", "")

        body = _health()

        assert body["commit"] == "unknown"
        assert body["built_at"] == "unknown"

    def test_a_missing_stamp_never_falls_back_to_the_app_version(self, stamp) -> None:
        """``app_version`` is the constant that caused #1210. Reusing it as a
        build identity would reproduce the original defect under a new name."""
        stamp("", "")

        body = _health()

        assert body["commit"] != settings.app_version
        assert body["built_at"] != settings.app_version
        assert "1.0.0" not in (body["commit"], body["built_at"])

    def test_a_missing_stamp_never_invents_a_commit_shaped_value(self, stamp) -> None:
        """An operator acts on a SHA without re-checking it. Anything that *looks*
        like one must therefore have come from a real build."""
        stamp("", "")

        commit = _health()["commit"]

        assert re.fullmatch(r"[0-9a-f]{7,40}", commit) is None, (
            f"unstamped build reported {commit!r}, which reads as a real commit SHA"
        )

    def test_a_blank_stamp_counts_as_missing(self, stamp) -> None:
        """A build arg that expanded to whitespace is an absent stamp, not a build
        identified by a space — ``ENV BUILD_COMMIT=${BUILD_COMMIT}`` with an unset
        arg is exactly how that arrives."""
        stamp("   ", "\n")

        body = _health()

        assert body["commit"] == "unknown"
        assert body["built_at"] == "unknown"

    def test_the_source_tree_declares_no_default_stamp(self) -> None:
        """Nothing checked into the tree may carry a build identity. A default here
        would be claimed by every deployment that never got stamped — which is the
        precise shape of the ``app_version = "1.0.0"`` defect."""
        assert Settings.model_fields["build_commit"].default == ""
        assert Settings.model_fields["build_timestamp"].default == ""


class TestTheStampComesFromTheContainerEnvironment:
    """AK 2: the value travels image → environment → settings, not source → settings."""

    def test_the_environment_variables_are_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BUILD_COMMIT", _A_REAL_SHA)
        monkeypatch.setenv("BUILD_TIMESTAMP", _A_REAL_TIMESTAMP)

        assert Settings().build_identity() == {"commit": _A_REAL_SHA, "built_at": _A_REAL_TIMESTAMP}

    def test_an_absent_environment_leaves_the_build_unidentified(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("BUILD_COMMIT", raising=False)
        monkeypatch.delenv("BUILD_TIMESTAMP", raising=False)

        assert Settings().build_identity() == {"commit": "unknown", "built_at": "unknown"}


class TestTheExistingContractIsUntouched:
    """AK 1/AK 5: the HA integration and the #1124 major negotiation read this body."""

    def test_the_established_fields_keep_their_names_and_values(self, stamp) -> None:
        stamp(_A_REAL_SHA, _A_REAL_TIMESTAMP)

        body = _health()

        assert body["status"] == "healthy"
        assert body["version"] == settings.app_version
        assert body["mode"] == settings.kamerplanter_mode
        assert body["supported_majors"] == [1]

    def test_the_endpoint_stays_unauthenticated(self) -> None:
        """Build identity must be askable before there is a token — that is the
        moment an operator is diagnosing a deployment."""
        response = TestClient(app).get("/api/health")

        assert response.status_code == 200
        assert {"commit", "built_at"} <= response.json().keys()

    def test_no_configuration_or_path_detail_is_disclosed(self, stamp) -> None:
        """The endpoint is public. A public repository's commit SHA is public too;
        anything describing *this deployment* is not."""
        stamp(_A_REAL_SHA, _A_REAL_TIMESTAMP)

        body = _health()

        assert body.keys() <= {
            "status",
            "version",
            "commit",
            "built_at",
            "mode",
            "supported_majors",
            "timescaledb",
            "knowledge_service",
        }, f"unexpected field(s) on the public health endpoint: {sorted(body)}"
