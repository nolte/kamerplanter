"""Tests for the hop-4 delivery check (``scripts/ci/check_deployed_build.py``).

**What is under test.** Whether the script can tell "the pod runs the pinned
bytes" from "it does not" from "I could not find out" — and, above all, whether
the *third* case can ever be mistaken for the first. Issue #1210 exists because a
merged fix sat undelivered for days while every check in the repository was
green; a check built for that incident that could itself report green on nothing
would be the same defect one level up (NFR-018 §2, cluster G of the 2026-08-08
audit).

**Nothing here touches the network.** Every registry and HTTP response is
injected through the script's ``open_url`` seam, keyed by the exact URL the
script builds — so a change that sends the request somewhere else fails these
tests rather than silently passing them.

**:class:`TestTheMeasuredIncident` is the one that matters.** It replays the real
2026-08-17 inputs, measured from the registry and from git: pinned digest
``sha256:e2b0aec…`` carrying revision ``37cbc06f…``, created 2026-08-16T14:28:39Z,
against an instance still on ``ca08b271d`` (2026-08-14, before #1180 added
``supported_majors`` — the symptom by which the stall was actually noticed). A
check that would not have caught the incident it was built for is worthless, so
that is asserted directly rather than inferred. The same class also pins the
honest limit of the 24h grace window: on the morning the operator noticed, the
pin was 16.6h old and the verdict is ``within_grace`` by design, so the alert
would have come one scheduled run later.

**The three instance answers** (:class:`TestTheInstanceHasThreeAnswers`) are the
subtle part of the contract. ``build_revision`` is gated behind
``HEALTH_EXPOSE_BUILD_REVISION`` (default off), so an absent key means "this
instance declines to say" — which is NOT drift and must never be reported as it —
while ``"unknown"`` means "willing to say, but nothing stamped a build in". Both
are red, for different reasons, with different messages.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI gate, and the
script lives outside the backend package, so it is loaded by path — the same
arrangement as ``test_workflow_gate_integrity_check.py``.

Traces to #1210 (no TC-ID: a delivery-chain gate is not a user-facing case).
"""

from __future__ import annotations

import io
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import TracebackType
from typing import Any

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("ci/check_deployed_build")


# --- Measured constants -------------------------------------------------------
#
# Every value below was read off the real registry / the real git history on
# 2026-08-17 and is quoted verbatim, so the replay is a replay and not a
# plausible-looking invention.

PINNED_DIGEST = "sha256:e2b0aec41662febf6e5baa4dba29ddb1f5572bf5fa9feca9c244f255c2413c98"
PLATFORM_DIGEST = "sha256:dbf67a87f9d8d9c490be5170a23e81ed014e1b890235c7f81b5387bb086e84fe"
CONFIG_DIGEST = "sha256:" + "1c" * 32
PINNED_REVISION = "37cbc06fcf0c7d69c07f7abbd3d485cb241070da"
PINNED_CREATED = "2026-08-16T14:28:39.211Z"
#: The image config's own timestamp carries NINE fractional digits, which
#: ``datetime.fromisoformat`` rejects — the reason parse_timestamp truncates.
CONFIG_CREATED = "2026-08-16T14:29:21.350293337Z"

#: What the instance was actually running: a 2026-08-14 build, i.e. before
#: #1180 (46878ea26, 2026-08-15) added ``supported_majors`` — whose absence is
#: how the stall was noticed at all.
STALE_REVISION = "ca08b271dfe327786a64f17baa302335c4bc6c33"

INSTANCE_URL = "https://kamerplanter.example.test"

REGISTRY_ROOT = "https://ghcr.io/v2/nolte/kamerplanter-backend"
TOKEN_URL = "https://ghcr.io/token?scope=repository:nolte/kamerplanter-backend:pull&service=ghcr.io"
INDEX_URL = f"{REGISTRY_ROOT}/manifests/{PINNED_DIGEST}"
PLATFORM_URL = f"{REGISTRY_ROOT}/manifests/{PLATFORM_DIGEST}"
BLOB_URL = f"{REGISTRY_ROOT}/blobs/{CONFIG_DIGEST}"
HEALTH_URL = f"{INSTANCE_URL}/api/health"

#: The first scheduled run after the operator noticed (07:00 UTC, 2026-08-17).
MORNING_OF_DISCOVERY = datetime(2026, 8, 17, 7, 0, tzinfo=UTC)
#: The next one, by which the pin is 40.6h old.
NEXT_MORNING = datetime(2026, 8, 18, 7, 0, tzinfo=UTC)


class _Response(io.BytesIO):
    """A urlopen-shaped context manager over a fixed JSON body."""

    def __enter__(self) -> _Response:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> None:
        self.close()


class FakeOpener:
    """An ``urlopen`` stand-in that answers by exact URL.

    Keying on the full URL is the point: it makes the tests assert *where* the
    script looks, not merely that it parses whatever it is handed. An
    unregistered URL fails the test rather than returning something plausible.
    """

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.requested: list[str] = []

    def __call__(self, request: Any, timeout: float | None = None) -> _Response:
        url = request.full_url
        self.requested.append(url)
        assert timeout is not None, f"{url} was requested without an explicit timeout"
        if url not in self.routes:
            raise AssertionError(f"unexpected request to {url}")
        answer = self.routes[url]
        if isinstance(answer, Exception):
            raise answer
        return _Response(json.dumps(answer).encode())


def image_config(*, stamped: str | None = PINNED_REVISION, created: str = CONFIG_CREATED) -> dict[str, Any]:
    """An image config blob, optionally carrying the BUILD_REVISION stamp."""
    env = ["PATH=/usr/local/bin", "PYTHON_VERSION=3.14.7"]
    if stamped is not None:
        env.append(f"BUILD_REVISION={stamped}")
    return {
        "created": created,
        "config": {
            "Env": env,
            "Labels": {
                "org.opencontainers.image.revision": PINNED_REVISION,
                "org.opencontainers.image.created": PINNED_CREATED,
            },
        },
    }


def image_index(*, annotations: dict[str, Any] | None = None) -> dict[str, Any]:
    """An OCI image index in the shape GHCR actually serves for this image.

    Includes the attestation manifest (platform ``unknown/unknown``) that must be
    skipped — it has no config blob, so picking it would break the resolution.
    """
    return {
        "schemaVersion": 2,
        "mediaType": "application/vnd.oci.image.index.v1+json",
        "manifests": [
            {"digest": PLATFORM_DIGEST, "platform": {"os": "linux", "architecture": "amd64"}},
            {
                "digest": "sha256:" + "ff" * 32,
                "annotations": {"vnd.docker.reference.type": "attestation-manifest"},
                "platform": {"os": "unknown", "architecture": "unknown"},
            },
        ],
        "annotations": {
            "org.opencontainers.image.revision": PINNED_REVISION,
            "org.opencontainers.image.created": PINNED_CREATED,
        }
        if annotations is None
        else annotations,
    }


def health_payload(**overrides: Any) -> dict[str, Any]:
    """A ``/api/health`` payload in the shape the endpoint actually returns."""
    payload: dict[str, Any] = {
        "status": "healthy",
        "version": "1.0.0",
        "mode": "full",
        "supported_majors": [1],
        "build_revision": PINNED_REVISION,
    }
    payload.update(overrides)
    return payload


def registry_routes(*, index: dict[str, Any] | None = None, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """The three registry responses one full resolution needs."""
    return {
        TOKEN_URL: {"token": "pull-token"},
        INDEX_URL: index if index is not None else image_index(),
        PLATFORM_URL: {"config": {"digest": CONFIG_DIGEST}},
        BLOB_URL: config if config is not None else image_config(),
    }


def pinned_image(*, created: str = PINNED_CREATED, stamped: str | None = PINNED_REVISION) -> Any:
    """A resolved :class:`PinnedImage`, for the pure decision tests."""
    return checker.PinnedImage(
        repository=checker.BACKEND_REPOSITORY,
        channel="latest",
        digest=PINNED_DIGEST,
        revision=PINNED_REVISION,
        created=checker.parse_timestamp(created),
        stamped_revision=stamped,
    )


@pytest.fixture
def pins_file(tmp_path: Path) -> Path:
    """The pins.json the workflow's yq step produces, backend pinned three times."""
    path = tmp_path / "pins.json"
    path.write_text(
        json.dumps(
            [
                {"repository": checker.BACKEND_REPOSITORY, "tag": f"latest@{PINNED_DIGEST}"},
                {"repository": checker.BACKEND_REPOSITORY, "tag": f"latest@{PINNED_DIGEST}"},
                {
                    "repository": "ghcr.io/nolte/kamerplanter-frontend",
                    "tag": "latest@sha256:" + "ab" * 32,
                },
            ]
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def deployed_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Run in a clean directory with the instance URL configured."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DEPLOYED_INSTANCE_URL", INSTANCE_URL)
    monkeypatch.delenv("DRIFT_THRESHOLD_HOURS", raising=False)
    monkeypatch.delenv("GHCR_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


class TestTheMeasuredIncident:
    """The falsification that matters: would this have caught #1210?

    A check that cannot demonstrate it would have caught the incident it was
    built for has proven nothing. These are the real measured inputs.
    """

    def test_the_incident_yields_the_drift_verdict(self) -> None:
        """Pinned 37cbc06f, instance on the 2026-08-14 build, pin 40.6h old."""
        verdict = checker.decide(
            pinned_image(),
            STALE_REVISION,
            now=NEXT_MORNING,
            threshold_hours=checker.DEFAULT_THRESHOLD_HOURS,
        )

        assert verdict.name == checker.VERDICT_DRIFT
        assert verdict.alerting is True
        # Both revisions must be nameable from the verdict — an alert that does
        # not say what is running against what is pinned is not actionable.
        assert STALE_REVISION[:12] in verdict.headline
        assert PINNED_REVISION[:12] in verdict.headline

    def test_the_drift_alert_names_both_revisions_in_full(
        self, pins_file: Path, deployed_env: None, tmp_path: Path
    ) -> None:
        """The report the issue is built from carries the untruncated SHAs."""
        opener = FakeOpener(
            {
                **registry_routes(),
                HEALTH_URL: health_payload(build_revision=STALE_REVISION),
            }
        )

        assert checker.main([str(pins_file)], open_url=opener, now=NEXT_MORNING) == checker.EXIT_OK

        report = json.loads((tmp_path / checker.REPORT_PATH).read_text(encoding="utf-8"))
        assert report["verdict"] == checker.VERDICT_DRIFT
        assert report["alerting"] is True
        assert report["pinned"]["revision"] == PINNED_REVISION
        assert report["instance"]["revision"] == STALE_REVISION
        assert report["age_hours"] == pytest.approx(40.5, abs=0.2)

    def test_on_the_morning_of_discovery_the_pin_was_still_inside_the_grace_window(
        self,
    ) -> None:
        """The honest limit of a 24h pin-anchored window, asserted not glossed.

        The chart was re-pinned at 2026-08-16T15:24; by the 07:00 run the next
        day that pin was 16.6h old. Alerting then would fire after every Renovate
        merge, so the verdict is ``within_grace`` and the alert arrives one
        scheduled run later. Recorded here so the latency is a known property
        rather than a surprise during the next incident.
        """
        verdict = checker.decide(
            pinned_image(),
            STALE_REVISION,
            now=MORNING_OF_DISCOVERY,
            threshold_hours=checker.DEFAULT_THRESHOLD_HOURS,
        )

        assert verdict.name == checker.VERDICT_WITHIN_GRACE
        assert verdict.alerting is False
        assert verdict.age_hours == pytest.approx(16.6, abs=0.2)

    def test_an_undisclosed_instance_is_not_reported_as_drift(
        self, pins_file: Path, deployed_env: None, tmp_path: Path
    ) -> None:
        """The fourth replay case: a missing key must never become an alert.

        An instance with HEALTH_EXPOSE_BUILD_REVISION off says nothing about its
        deployment. Reporting that as drift would put a false accusation in the
        tracker and teach everyone to distrust the real ones.
        """
        payload = health_payload()
        del payload["build_revision"]
        opener = FakeOpener({**registry_routes(), HEALTH_URL: payload})

        # Raised as its own type, so "declines to disclose" cannot be silently
        # folded into "unknown" or into any comparison verdict.
        with pytest.raises(checker.BuildRevisionNotDisclosedError):
            checker.main([str(pins_file)], open_url=opener, now=NEXT_MORNING)

        assert checker.run([str(pins_file)], open_url=opener, now=NEXT_MORNING) == (checker.EXIT_UNDETERMINED)
        assert not (tmp_path / checker.REPORT_PATH).exists()


class TestTheInstanceHasThreeAnswers:
    """Absent key, ``"unknown"`` and a real SHA mean three different things."""

    def test_a_full_sha_is_the_answer(self) -> None:
        opener = FakeOpener({HEALTH_URL: health_payload(build_revision=STALE_REVISION)})

        assert checker.read_instance_revision(INSTANCE_URL, open_url=opener) == STALE_REVISION
        assert opener.requested == [HEALTH_URL]

    def test_an_absent_key_is_its_own_error_naming_the_setting(self) -> None:
        """Not disclosed: nothing is wrong with the deployment, and it must say so."""
        payload = health_payload()
        del payload["build_revision"]
        opener = FakeOpener({HEALTH_URL: payload})

        with pytest.raises(checker.BuildRevisionNotDisclosedError) as caught:
            checker.read_instance_revision(INSTANCE_URL, open_url=opener)

        message = str(caught.value)
        assert checker.DISCLOSURE_SETTING in message
        # The distinction the security review turned on: this is not drift, and
        # the message must not let a reader conclude that it is.
        assert "NOT drift" in message

    def test_unknown_is_a_different_error_from_an_absent_key(self) -> None:
        """Willing to disclose, but nothing stamped a build in."""
        opener = FakeOpener({HEALTH_URL: health_payload(build_revision="unknown")})

        with pytest.raises(checker.BuildRevisionUnknownError) as caught:
            checker.read_instance_revision(INSTANCE_URL, open_url=opener)

        assert checker.BUILD_REVISION_ENV in str(caught.value)
        # The two states are distinguishable by type, not only by wording.
        assert not isinstance(caught.value, checker.BuildRevisionNotDisclosedError)

    def test_an_abbreviated_revision_is_refused_rather_than_truncated(self) -> None:
        """The endpoint accepts 7-40 hex; only 40 can be compared in full.

        Inventing a truncation rule here is exactly the kind of quiet convention
        that makes two values look equal when they are not.
        """
        opener = FakeOpener({HEALTH_URL: health_payload(build_revision=PINNED_REVISION[:7])})

        with pytest.raises(checker.DeployedBuildError, match="truncation rule"):
            checker.read_instance_revision(INSTANCE_URL, open_url=opener)

    def test_a_reply_without_status_is_not_a_kamerplanter_instance(self) -> None:
        """Guards a mis-set URL from producing a soft verdict off someone else's JSON."""
        opener = FakeOpener({HEALTH_URL: {"build_revision": PINNED_REVISION}})

        with pytest.raises(checker.DeployedBuildError, match="health payload"):
            checker.read_instance_revision(INSTANCE_URL, open_url=opener)

    @pytest.mark.parametrize("suffix", ["", "/"])
    def test_the_health_url_is_built_from_the_base_url(self, suffix: str) -> None:
        assert checker.health_url(f"{INSTANCE_URL}{suffix}") == HEALTH_URL


class TestPinnedImageResolution:
    """Turning a pinned digest into "which commit are these bytes?"."""

    def test_the_revision_and_creation_time_come_off_the_index(self) -> None:
        opener = FakeOpener(registry_routes())
        reader = checker.RegistryReader("nolte/kamerplanter-backend", open_url=opener)

        pinned = checker.read_pinned_image(reader, checker.BACKEND_REPOSITORY, "latest", PINNED_DIGEST)

        assert pinned.revision == PINNED_REVISION
        assert pinned.created == datetime(2026, 8, 16, 14, 28, 39, 211000, tzinfo=UTC)
        assert pinned.stamped is True
        # The attestation manifest must not have been followed: it has no config.
        assert PLATFORM_URL in opener.requested

    def test_it_falls_back_to_the_config_labels(self) -> None:
        """A differently-published image must not make the check undeterminable."""
        opener = FakeOpener(registry_routes(index=image_index(annotations={})))
        reader = checker.RegistryReader("nolte/kamerplanter-backend", open_url=opener)

        pinned = checker.read_pinned_image(reader, checker.BACKEND_REPOSITORY, "latest", PINNED_DIGEST)

        assert pinned.revision == PINNED_REVISION

    def test_an_unstamped_image_is_detected_as_such(self) -> None:
        """The real pinned image carries no BUILD_REVISION — that is measurable."""
        opener = FakeOpener(registry_routes(config=image_config(stamped=None)))
        reader = checker.RegistryReader("nolte/kamerplanter-backend", open_url=opener)

        pinned = checker.read_pinned_image(reader, checker.BACKEND_REPOSITORY, "latest", PINNED_DIGEST)

        assert pinned.stamped is False

    def test_an_image_that_contradicts_itself_is_refused(self) -> None:
        """Annotation and baked-in stamp disagreeing makes the comparison arbitrary."""
        opener = FakeOpener(registry_routes(config=image_config(stamped=STALE_REVISION)))
        reader = checker.RegistryReader("nolte/kamerplanter-backend", open_url=opener)

        with pytest.raises(checker.DeployedBuildError, match="describes itself twice"):
            checker.read_pinned_image(reader, checker.BACKEND_REPOSITORY, "latest", PINNED_DIGEST)

    def test_a_missing_revision_annotation_is_refused(self) -> None:
        config = image_config()
        config["config"]["Labels"] = {"org.opencontainers.image.created": PINNED_CREATED}
        opener = FakeOpener(registry_routes(index=image_index(annotations={}), config=config))
        reader = checker.RegistryReader("nolte/kamerplanter-backend", open_url=opener)

        with pytest.raises(checker.DeployedBuildError, match="cannot say which commit"):
            checker.read_pinned_image(reader, checker.BACKEND_REPOSITORY, "latest", PINNED_DIGEST)

    def test_a_manifest_without_a_config_is_refused(self) -> None:
        routes = registry_routes()
        routes[PLATFORM_URL] = {"schemaVersion": 2}
        reader = checker.RegistryReader("nolte/kamerplanter-backend", open_url=FakeOpener(routes))

        with pytest.raises(checker.DeployedBuildError, match="no config digest"):
            checker.read_pinned_image(reader, checker.BACKEND_REPOSITORY, "latest", PINNED_DIGEST)

    def test_nine_fractional_digits_parse(self) -> None:
        """The pinned image config really carries nanoseconds; fromisoformat rejects them."""
        assert checker.parse_timestamp(CONFIG_CREATED).year == 2026

    def test_an_unparseable_timestamp_is_refused(self) -> None:
        with pytest.raises(checker.DeployedBuildError, match="unparseable timestamp"):
            checker.parse_timestamp("yesterday")


class TestDecide:
    """The pure comparison, across the grace boundary."""

    def test_equal_revisions_close_the_chain(self) -> None:
        verdict = checker.decide(pinned_image(), PINNED_REVISION, now=NEXT_MORNING, threshold_hours=24)

        assert verdict.name == checker.VERDICT_MATCH
        assert verdict.alerting is False

    def test_a_mismatch_inside_the_window_is_not_alerted(self) -> None:
        verdict = checker.decide(pinned_image(), STALE_REVISION, now=MORNING_OF_DISCOVERY, threshold_hours=24)

        assert verdict.name == checker.VERDICT_WITHIN_GRACE
        assert verdict.alerting is False

    def test_the_boundary_belongs_to_drift(self) -> None:
        """Exactly at the threshold the grace is over — no silent extra hour."""
        pinned = pinned_image()

        just_inside = checker.decide(
            pinned,
            STALE_REVISION,
            now=pinned.created + timedelta(hours=24) - timedelta(seconds=1),
            threshold_hours=24,
        )
        exactly_at = checker.decide(
            pinned, STALE_REVISION, now=pinned.created + timedelta(hours=24), threshold_hours=24
        )

        assert just_inside.name == checker.VERDICT_WITHIN_GRACE
        assert exactly_at.name == checker.VERDICT_DRIFT

    def test_a_widened_window_suppresses_the_alert(self) -> None:
        """DRIFT_THRESHOLD_HOURS is a real knob, not decoration."""
        verdict = checker.decide(pinned_image(), STALE_REVISION, now=NEXT_MORNING, threshold_hours=72)

        assert verdict.name == checker.VERDICT_WITHIN_GRACE


class TestFailLoudNeverWritesAReport:
    """NFR-018 §2: an undetermined check goes red and stays out of the tracker.

    The workflow's issue step is gated on the report file existing, so "no report
    written" is what actually keeps a transient failure from opening an issue.
    Each case therefore asserts BOTH halves: non-zero exit and no report.
    """

    def _assert_red_and_silent(self, pins: Path, tmp_path: Path, opener: Any) -> None:
        exit_code = checker.run([str(pins)], open_url=opener, now=NEXT_MORNING)
        assert exit_code == checker.EXIT_UNDETERMINED
        assert not (tmp_path / checker.REPORT_PATH).exists()

    def test_an_unset_instance_url(
        self, pins_file: Path, deployed_env: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("DEPLOYED_INSTANCE_URL")
        # No routes at all: reaching the network would itself be the failure.
        self._assert_red_and_silent(pins_file, tmp_path, FakeOpener({}))

    def test_a_blank_instance_url(
        self, pins_file: Path, deployed_env: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEPLOYED_INSTANCE_URL", "   ")
        self._assert_red_and_silent(pins_file, tmp_path, FakeOpener({}))

    def test_a_non_http_instance_url(
        self, pins_file: Path, deployed_env: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DEPLOYED_INSTANCE_URL", "kamerplanter.example.test")
        self._assert_red_and_silent(pins_file, tmp_path, FakeOpener({}))

    def test_an_unreachable_instance(self, pins_file: Path, deployed_env: None, tmp_path: Path) -> None:
        import urllib.error

        opener = FakeOpener({**registry_routes(), HEALTH_URL: urllib.error.URLError("connection refused")})
        self._assert_red_and_silent(pins_file, tmp_path, opener)

    def test_an_instance_answering_an_http_error(self, pins_file: Path, deployed_env: None, tmp_path: Path) -> None:
        import urllib.error

        error = urllib.error.HTTPError(HEALTH_URL, 502, "Bad Gateway", {}, None)  # type: ignore[arg-type]
        self._assert_red_and_silent(pins_file, tmp_path, FakeOpener({**registry_routes(), HEALTH_URL: error}))

    def test_a_missing_revision_annotation(self, pins_file: Path, deployed_env: None, tmp_path: Path) -> None:
        config = image_config()
        config["config"]["Labels"] = {}
        opener = FakeOpener(
            {
                **registry_routes(index=image_index(annotations={}), config=config),
                HEALTH_URL: health_payload(),
            }
        )
        self._assert_red_and_silent(pins_file, tmp_path, opener)

    def test_an_unparseable_manifest(self, pins_file: Path, deployed_env: None, tmp_path: Path) -> None:
        routes = registry_routes()
        routes[INDEX_URL] = ["not", "an", "object"]
        self._assert_red_and_silent(pins_file, tmp_path, FakeOpener(routes))

    def test_a_registry_that_refuses_a_pull_token(self, pins_file: Path, deployed_env: None, tmp_path: Path) -> None:
        routes = registry_routes()
        routes[TOKEN_URL] = {}
        self._assert_red_and_silent(pins_file, tmp_path, FakeOpener(routes))

    def test_pins_without_the_backend_image(self, deployed_env: None, tmp_path: Path) -> None:
        """A check that examined nothing must not report clean."""
        pins = tmp_path / "pins.json"
        pins.write_text(
            json.dumps([{"repository": "ghcr.io/nolte/kamerplanter-frontend", "tag": "latest@sha256:" + "ab" * 32}]),
            encoding="utf-8",
        )
        self._assert_red_and_silent(pins, tmp_path, FakeOpener({}))

    def test_a_backend_pinned_at_two_different_builds(self, deployed_env: None, tmp_path: Path) -> None:
        """There is then no single "pinned build" to compare against."""
        pins = tmp_path / "pins.json"
        pins.write_text(
            json.dumps(
                [
                    {"repository": checker.BACKEND_REPOSITORY, "tag": f"latest@{PINNED_DIGEST}"},
                    {
                        "repository": checker.BACKEND_REPOSITORY,
                        "tag": "latest@sha256:" + "cd" * 32,
                    },
                ]
            ),
            encoding="utf-8",
        )
        self._assert_red_and_silent(pins, tmp_path, FakeOpener({}))

    def test_an_unpinned_backend_tag(self, deployed_env: None, tmp_path: Path) -> None:
        pins = tmp_path / "pins.json"
        pins.write_text(
            json.dumps([{"repository": checker.BACKEND_REPOSITORY, "tag": "latest"}]),
            encoding="utf-8",
        )
        self._assert_red_and_silent(pins, tmp_path, FakeOpener({}))

    def test_a_nonsense_threshold(
        self, pins_file: Path, deployed_env: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("DRIFT_THRESHOLD_HOURS", "soon")
        self._assert_red_and_silent(pins_file, tmp_path, FakeOpener({}))

    def test_unknown_from_an_instance_running_unstamped_bytes_explains_itself(
        self, pins_file: Path, deployed_env: None, tmp_path: Path
    ) -> None:
        """Red, but actionable: it names why no deployment could have answered.

        This is the bootstrap window — the pinned image predates the stamp — and
        the difference between a baffling red and a to-do is that sentence.
        """
        opener = FakeOpener(
            {
                **registry_routes(config=image_config(stamped=None)),
                HEALTH_URL: health_payload(build_revision="unknown"),
            }
        )

        with pytest.raises(checker.BuildRevisionUnknownError, match="has to be published and pinned"):
            checker.main([str(pins_file)], open_url=opener, now=NEXT_MORNING)

        assert not (tmp_path / checker.REPORT_PATH).exists()


class TestDeterminedRunsWriteTheReport:
    """The green paths, end to end through ``main`` with every response injected."""

    def test_a_match_writes_a_non_alerting_report(self, pins_file: Path, deployed_env: None, tmp_path: Path) -> None:
        opener = FakeOpener({**registry_routes(), HEALTH_URL: health_payload()})

        assert checker.main([str(pins_file)], open_url=opener, now=NEXT_MORNING) == checker.EXIT_OK

        report = json.loads((tmp_path / checker.REPORT_PATH).read_text(encoding="utf-8"))
        assert report["verdict"] == checker.VERDICT_MATCH
        assert report["alerting"] is False
        assert report["instance_url"] == INSTANCE_URL
        assert report["threshold_hours"] == checker.DEFAULT_THRESHOLD_HOURS

    def test_the_threshold_override_reaches_the_verdict(
        self, pins_file: Path, deployed_env: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """workflow_dispatch's threshold_hours input must actually do something."""
        monkeypatch.setenv("DRIFT_THRESHOLD_HOURS", "72")
        opener = FakeOpener({**registry_routes(), HEALTH_URL: health_payload(build_revision=STALE_REVISION)})

        assert checker.main([str(pins_file)], open_url=opener, now=NEXT_MORNING) == checker.EXIT_OK

        report = json.loads((tmp_path / checker.REPORT_PATH).read_text(encoding="utf-8"))
        assert report["verdict"] == checker.VERDICT_WITHIN_GRACE
        assert report["threshold_hours"] == 72

    def test_the_report_carries_everything_the_issue_body_renders(
        self, pins_file: Path, deployed_env: None, tmp_path: Path
    ) -> None:
        """Pins the contract between the script and the workflow's github-script step."""
        opener = FakeOpener({**registry_routes(), HEALTH_URL: health_payload(build_revision=STALE_REVISION)})
        checker.main([str(pins_file)], open_url=opener, now=NEXT_MORNING)

        report = json.loads((tmp_path / checker.REPORT_PATH).read_text(encoding="utf-8"))
        assert set(report) >= {
            "verdict",
            "alerting",
            "headline",
            "explanation",
            "threshold_hours",
            "age_hours",
            "instance_url",
            "pinned",
            "instance",
        }
        assert set(report["pinned"]) >= {
            "repository",
            "channel",
            "digest",
            "revision",
            "created",
            "stamped",
        }
        assert report["instance"]["revision"] == STALE_REVISION

    def test_wrong_argument_count_is_a_usage_error(self) -> None:
        assert checker.main([], open_url=FakeOpener({})) == checker.EXIT_USAGE
