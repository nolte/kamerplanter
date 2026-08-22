"""Tests for the chart-image freshness guard (``scripts/ci/check_digest_freshness.py``).

**Why this file exists.** The guard shipped with no tests at all, and was
structurally unable to alert: it measured ``now - created(current registry
build)``, i.e. *how old the newest build is*, and compared that against the
grace window. In a repository that publishes near-daily the newest build is
always hours old, so the comparison could never trip — however far behind the
chart pin was. On 2026-08-16 the chart had pinned ``sha256:db4e7f1b…`` since
2026-08-12 while GHCR served ``sha256:e2b0aec4…``; the scheduled run reported
"All chart image digests are current — nothing to report" (#1210).

:class:`TestDriftDetection` reconstructs exactly that constellation. It is the
test the fix must turn green, and it fails against the pre-#1210 script.

**What is under test.** The decision logic, driven against a constructed
in-memory registry — never against ghcr.io. A test that reached the real
registry would answer a question about today's deployment state, not about the
guard, and would go red on the next publish.

**The double is deliberately not more permissive than ghcr.io**
(:class:`FakeRegistry`): every ``/v2/`` request must carry a bearer token and an
explicit timeout, manifests are addressed either by a tag the registry knows or
by a digest it actually stores (anything else is a 404, as upstream), and the
``docker-content-digest`` of a digest-addressed request is that digest — because
every digest here is the SHA-256 of the bytes served, exactly as a registry
computes it. Image indexes carry the buildx attestation entry
(``platform: unknown/unknown``) that the real ones carry, so the platform filter
in ``_created_at`` is exercised rather than assumed away.

**Why here.** The script lives outside the backend package (it runs on a bare
CI runner), but ``pytest tests/unit/`` is the tier that actually runs, so the
test lives here and loads the script by path — the same arrangement as
``test_workflow_gate_integrity_check.py``. Traces to #1210 (no TC-ID: a
source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import sys
import urllib.error
import urllib.request
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from tests.support.repo_scripts import find_repo_root

REGISTRY_HOST = "ghcr.io"
BACKEND_IMAGE = "ghcr.io/nolte/kamerplanter-backend"

#: The 2026-08-16 incident, in numbers: the pin had been superseded for close to
#: four days while the build the channel served was under an hour old.
INCIDENT_PIN_AGE_DAYS = 3.95
INCIDENT_HEAD_AGE_DAYS = 0.04


def _load_freshness_script() -> ModuleType:
    """Execute ``scripts/ci/check_digest_freshness.py`` and return it as a module.

    ``tests.support.repo_scripts.load_repo_script`` only reaches
    ``scripts/<stem>.py``; this one lives under ``scripts/ci/``. Its repo-root
    marker walk is reused rather than re-implemented, so a moved test file still
    finds the checkout.
    """
    repo_root = find_repo_root(Path(__file__).resolve())
    if repo_root is None:  # pragma: no cover — only outside a full checkout
        pytest.skip("checkout root not found; scripts/ci/ is unreachable", allow_module_level=True)

    path = repo_root / "scripts" / "ci" / "check_digest_freshness.py"
    if not path.is_file():  # pragma: no cover — only on a partial checkout
        pytest.skip(f"{path} does not exist", allow_module_level=True)

    spec = importlib.util.spec_from_file_location("_repo_script_check_digest_freshness", path)
    if spec is None or spec.loader is None:  # pragma: no cover — defensive
        pytest.skip(f"{path} cannot be loaded as a Python module", allow_module_level=True)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


freshness = _load_freshness_script()


def _canonical(payload: dict[str, Any]) -> bytes:
    """Serialise a manifest/blob to the exact bytes the fake registry serves."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def _digest_of(payload: dict[str, Any]) -> str:
    """Content-address a payload the way a registry does."""
    return f"sha256:{hashlib.sha256(_canonical(payload)).hexdigest()}"


class _Response(io.BytesIO):
    """A urlopen-shaped response: a readable body plus response headers."""

    def __init__(self, body: bytes, headers: dict[str, str] | None = None) -> None:
        super().__init__(body)
        self.headers = headers or {}


class FakeRegistry:
    """The slice of the OCI distribution API this script speaks, in memory.

    Modelled on the responses ghcr.io actually returns for
    ``ghcr.io/nolte/kamerplanter-*`` (measured 2026-08-16), and never looser:
    an unknown tag, an unknown digest and an unauthenticated ``/v2/`` request
    are refused here exactly as they are refused there.
    """

    def __init__(self) -> None:
        self.manifests: dict[tuple[str, str], dict[str, Any]] = {}
        self.blobs: dict[tuple[str, str], dict[str, Any]] = {}
        self.tags: dict[tuple[str, str], str] = {}
        #: (path, reference) -> HTTP status, for the fail-loud cases.
        self.forced_errors: dict[tuple[str, str], int] = {}
        self.calls: list[str] = []

    # ── seeding ──────────────────────────────────────────────────────────
    def publish(
        self,
        repository: str,
        *,
        created: datetime | None,
        tags: tuple[str, ...] = (),
    ) -> str:
        """Store one multi-arch build and return its index digest.

        Args:
            repository: Full image reference, e.g. ``ghcr.io/nolte/kamerplanter-backend``.
            created: Build timestamp, or None to model a config blob without one.
            tags: Channel/commit tags pointing at this build.

        Returns:
            The digest of the image index — what a chart pin refers to.
        """
        path = repository.removeprefix(f"{REGISTRY_HOST}/")

        config: dict[str, Any] = {"architecture": "amd64", "os": "linux"}
        if created is not None:
            # Nanosecond precision, as containerd writes it — the script has to
            # trim it back to what fromisoformat accepts.
            config["created"] = created.strftime("%Y-%m-%dT%H:%M:%S.") + f"{created.microsecond:06d}226224757Z"
        config_digest = _digest_of(config)
        self.blobs[(path, config_digest)] = config

        image = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "config": {
                "mediaType": "application/vnd.oci.image.config.v1+json",
                "digest": config_digest,
                "size": len(_canonical(config)),
            },
            "layers": [],
        }
        image_digest = _digest_of(image)
        self.manifests[(path, image_digest)] = image

        # The buildx attestation manifest that rides along in every index we
        # publish. Its config carries no `created`; a platform filter that let
        # it through would fail loud here instead of quietly reading a wrong
        # timestamp.
        attestation = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "config": {
                "mediaType": "application/vnd.oci.image.config.v1+json",
                "digest": _digest_of({"attestation": image_digest}),
                "size": 233,
            },
            "layers": [],
        }
        attestation_digest = _digest_of(attestation)
        self.manifests[(path, attestation_digest)] = attestation
        self.blobs[(path, attestation["config"]["digest"])] = {"attestation": image_digest}

        index = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "manifests": [
                {
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "digest": image_digest,
                    "size": len(_canonical(image)),
                    "platform": {"architecture": "amd64", "os": "linux"},
                },
                {
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "digest": attestation_digest,
                    "size": len(_canonical(attestation)),
                    "annotations": {
                        "vnd.docker.reference.digest": image_digest,
                        "vnd.docker.reference.type": "attestation-manifest",
                    },
                    "platform": {"architecture": "unknown", "os": "unknown"},
                },
            ],
        }
        index_digest = _digest_of(index)
        self.manifests[(path, index_digest)] = index
        for tag in tags:
            self.tags[(path, tag)] = index_digest
        return index_digest

    # ── serving ──────────────────────────────────────────────────────────
    def urlopen(self, request: urllib.request.Request, timeout: float | None = None) -> _Response:
        """Stand in for :func:`urllib.request.urlopen`."""
        assert timeout is not None, "every registry call must carry an explicit timeout"
        url = request.full_url
        self.calls.append(url)

        token_match = re.fullmatch(rf"https://{REGISTRY_HOST}/token\?scope=repository:(?P<path>[^:]+):pull&.*", url)
        if token_match:
            return _Response(json.dumps({"token": f"fake-token-for-{token_match.group('path')}"}).encode())

        api_match = re.fullmatch(
            rf"https://{REGISTRY_HOST}/v2/(?P<path>.+?)/(?P<kind>manifests|blobs)/(?P<reference>.+)",
            url,
        )
        assert api_match is not None, f"unexpected registry URL: {url}"
        path, kind, reference = api_match.group("path"), api_match.group("kind"), api_match.group("reference")

        if request.get_header("Authorization") != f"Bearer fake-token-for-{path}":
            raise self._http_error(url, 401)
        forced = self.forced_errors.get((path, reference))
        if forced is not None:
            raise self._http_error(url, forced)

        if kind == "blobs":
            blob = self.blobs.get((path, reference))
            if blob is None:
                raise self._http_error(url, 404)
            return _Response(_canonical(blob))

        assert "application/vnd.oci.image.index.v1+json" in (request.get_header("Accept") or ""), (
            "a manifest request must accept the index media type or the registry "
            "answers with something other than the multi-arch index"
        )
        digest = reference if reference.startswith("sha256:") else self.tags.get((path, reference))
        manifest = self.manifests.get((path, digest or ""))
        if manifest is None:
            raise self._http_error(url, 404)
        return _Response(_canonical(manifest), {"docker-content-digest": digest or ""})

    @staticmethod
    def _http_error(url: str, code: int) -> urllib.error.HTTPError:
        return urllib.error.HTTPError(url, code, "fake registry error", {}, None)  # type: ignore[arg-type]


@pytest.fixture(autouse=True)
def registry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[FakeRegistry]:
    """Install the fake registry and run every case in an isolated cwd.

    The cwd move matters: ``main()`` writes ``freshness-report.json`` relative to
    it, and its absence is half of the fail-loud contract under test.
    """
    fake = FakeRegistry()
    monkeypatch.setattr(urllib.request, "urlopen", fake.urlopen)
    monkeypatch.setattr(freshness, "_token_cache", {})
    monkeypatch.chdir(tmp_path)
    yield fake


def _run(pins: list[dict[str, str]], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> int:
    """Write *pins* as the workflow's ``pins.json`` and invoke ``main()``."""
    pins_file = tmp_path / "pins.json"
    pins_file.write_text(json.dumps(pins), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check_digest_freshness.py", str(pins_file)])
    return int(freshness.main())


def _report(tmp_path: Path) -> dict[str, Any]:
    """Read the report ``main()`` wrote, as the workflow's github-script step does."""
    return json.loads((tmp_path / freshness.REPORT_PATH).read_text(encoding="utf-8"))


def _incident(registry: FakeRegistry, *, pin_age_days: float, head_age_days: float) -> list[dict[str, str]]:
    """Publish a superseded pin and a newer channel head; return the chart pins."""
    now = datetime.now(UTC)
    pinned = registry.publish(
        BACKEND_IMAGE,
        created=now - timedelta(days=pin_age_days),
        tags=("8df878b",),
    )
    registry.publish(
        BACKEND_IMAGE,
        created=now - timedelta(days=head_age_days),
        tags=("latest", "37cbc06"),
    )
    return [{"repository": BACKEND_IMAGE, "tag": f"latest@{pinned}"}]


class TestDriftDetection:
    """The 2026-08-16 constellation, which the guard reported clean (#1210)."""

    def test_a_pin_superseded_for_longer_than_the_grace_window_is_drift(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Pin superseded ~4 days ago, channel head an hour old ⇒ alert.

        Against the pre-#1210 script this is red: it read the age of the *head*
        (0.04 d), found it inside the 3-day window, and filed the pin as "within
        grace" — the structural reason the alert could never fire.
        """
        pins = _incident(registry, pin_age_days=INCIDENT_PIN_AGE_DAYS, head_age_days=INCIDENT_HEAD_AGE_DAYS)

        assert _run(pins, monkeypatch, tmp_path) == 0

        report = _report(tmp_path)
        assert report["within_grace"] == []
        assert len(report["drift"]) == 1
        entry = report["drift"][0]
        assert entry["repository"] == BACKEND_IMAGE
        assert entry["channel"] == "latest"
        assert entry["pinned"] == pins[0]["tag"].split("@", 1)[1]
        assert entry["current"] != entry["pinned"]
        assert entry["age_days"] == pytest.approx(INCIDENT_PIN_AGE_DAYS, abs=0.05)
        assert entry["age_days"] >= report["threshold_days"]
        assert any(f"/manifests/{entry['pinned']}" in call for call in registry.calls), (
            "the pinned build must be resolved against the registry by digest — "
            "the age the verdict rests on comes from that manifest, not the head's"
        )

    def test_the_grace_window_is_measured_against_the_pin_not_the_head(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A head published minutes ago must not shorten the reported divergence.

        The head age is what the old code measured; pinning it separately keeps a
        future refactor from quietly reverting to it, since a report anchored on
        the head would read ~0 days here.
        """
        pins = _incident(registry, pin_age_days=9.0, head_age_days=0.002)

        _run(pins, monkeypatch, tmp_path)

        entry = _report(tmp_path)["drift"][0]
        assert entry["age_days"] == pytest.approx(9.0, abs=0.05)

    def test_duplicate_pins_of_one_image_are_checked_once(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """values.yaml names the backend three times with one digest (#987)."""
        pins = _incident(registry, pin_age_days=INCIDENT_PIN_AGE_DAYS, head_age_days=INCIDENT_HEAD_AGE_DAYS)

        _run(pins * 3, monkeypatch, tmp_path)

        report = _report(tmp_path)
        assert report["checked"] == 1
        assert len(report["drift"]) == 1


class TestNoFalsePositive:
    """A current pin must stay quiet, whatever the age of the build behind it."""

    def test_a_pin_matching_the_channel_head_is_not_reported(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Same digest ⇒ no drift, no grace entry — even at ten days old.

        The age deliberately exceeds the window: the alert is about *divergence*,
        and a rule that fired on the pin's age alone would misread a quiet week
        as a stalled write-back.
        """
        digest = registry.publish(
            BACKEND_IMAGE,
            created=datetime.now(UTC) - timedelta(days=10),
            tags=("latest", "37cbc06"),
        )
        pins = [{"repository": BACKEND_IMAGE, "tag": f"latest@{digest}"}]

        assert _run(pins, monkeypatch, tmp_path) == 0

        report = _report(tmp_path)
        assert report["drift"] == []
        assert report["within_grace"] == []
        assert report["checked"] == 1

    def test_a_third_party_image_is_out_of_scope(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Only ``ghcr.io/nolte/kamerplanter-*`` pins are ours to age."""
        pins = _incident(registry, pin_age_days=INCIDENT_PIN_AGE_DAYS, head_age_days=INCIDENT_HEAD_AGE_DAYS)
        pins.append({"repository": "docker.io/arangodb/arangodb", "tag": "3.11.14"})

        _run(pins, monkeypatch, tmp_path)

        assert _report(tmp_path)["checked"] == 1


class TestGraceWindow:
    """Divergence younger than the window is recorded, not alerted."""

    def test_a_recently_superseded_pin_stays_within_grace(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """One day behind ⇒ no alert, but a visible ``within_grace`` entry.

        This is the normal publish → Renovate PR → automerge cycle in flight; the
        guard must not page anyone for it.
        """
        pins = _incident(registry, pin_age_days=1.0, head_age_days=0.05)

        assert _run(pins, monkeypatch, tmp_path) == 0

        report = _report(tmp_path)
        assert report["drift"] == []
        assert len(report["within_grace"]) == 1
        entry = report["within_grace"][0]
        assert entry["age_days"] == pytest.approx(1.0, abs=0.05)
        assert entry["age_days"] < report["threshold_days"]

    def test_the_window_is_read_from_the_environment(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The same divergence is alertable or not depending on the override.

        The workflow exposes ``threshold_days`` as a dispatch input; a threshold
        the script did not actually consult would leave that input decorative.
        """
        pins = _incident(registry, pin_age_days=INCIDENT_PIN_AGE_DAYS, head_age_days=INCIDENT_HEAD_AGE_DAYS)
        monkeypatch.setenv("DRIFT_THRESHOLD_DAYS", "30")

        _run(pins, monkeypatch, tmp_path)

        report = _report(tmp_path)
        assert report["threshold_days"] == 30
        assert report["drift"] == []
        assert len(report["within_grace"]) == 1


class TestFailLoud:
    """NFR-018 §2: an undetermined check is red and writes no report."""

    def _assert_undetermined(self, pins: list[dict[str, str]], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        with pytest.raises(freshness.FreshnessError):
            _run(pins, monkeypatch, tmp_path)
        assert not (tmp_path / freshness.REPORT_PATH).exists(), (
            "a report file would let the workflow's github-script step run and "
            "read an undetermined check as a clean one"
        )

    def test_an_unreachable_channel_tag_is_not_a_clean_result(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A 500 on the channel manifest must not read as "no drift"."""
        pins = _incident(registry, pin_age_days=INCIDENT_PIN_AGE_DAYS, head_age_days=INCIDENT_HEAD_AGE_DAYS)
        registry.forced_errors[("nolte/kamerplanter-backend", "latest")] = 500

        self._assert_undetermined(pins, monkeypatch, tmp_path)

    def test_a_pinned_digest_the_registry_no_longer_serves_is_not_a_clean_result(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """A pin that cannot be resolved is worse than drift, not better.

        It means the chart names a build GHCR will not hand out — the deployment
        is broken rather than stalled — so the run goes red and the operator gets
        the run status, not a "clean" report.
        """
        registry.publish(BACKEND_IMAGE, created=datetime.now(UTC), tags=("latest",))
        vanished = f"sha256:{'db4e7f1b' * 8}"
        pins = [{"repository": BACKEND_IMAGE, "tag": f"latest@{vanished}"}]

        self._assert_undetermined(pins, monkeypatch, tmp_path)

    def test_a_config_without_a_created_timestamp_is_not_a_clean_result(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """No timestamp ⇒ no age ⇒ no verdict."""
        pinned = registry.publish(BACKEND_IMAGE, created=None, tags=("8df878b",))
        registry.publish(BACKEND_IMAGE, created=datetime.now(UTC), tags=("latest",))

        self._assert_undetermined([{"repository": BACKEND_IMAGE, "tag": f"latest@{pinned}"}], monkeypatch, tmp_path)

    def test_a_malformed_pin_is_not_a_clean_result(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """An unpinned ``tag: latest`` is the #987 regression, not a pass."""
        self._assert_undetermined([{"repository": BACKEND_IMAGE, "tag": "latest"}], monkeypatch, tmp_path)

    def test_an_empty_pin_set_is_not_a_clean_result(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Checking nothing must never report clean."""
        pins = [{"repository": "docker.io/arangodb/arangodb", "tag": "3.11.14"}]
        self._assert_undetermined(pins, monkeypatch, tmp_path)


class TestReportContract:
    """The fields ``.github/workflows/chart-image-digest-freshness.yml`` reads."""

    def test_the_workflow_readable_fields_are_present(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The github-script step interpolates these by name into the issue body.

        A renamed or dropped field would surface as ``undefined`` in the alert —
        the workflow reads the JSON, so nothing else type-checks this seam.
        """
        pins = _incident(registry, pin_age_days=INCIDENT_PIN_AGE_DAYS, head_age_days=INCIDENT_HEAD_AGE_DAYS)

        _run(pins, monkeypatch, tmp_path)

        report = _report(tmp_path)
        assert isinstance(report["threshold_days"], int)
        entry = report["drift"][0]
        assert {"repository", "channel", "pinned", "current", "age_days"} <= set(entry)
        for field in ("pinned", "current"):
            assert re.fullmatch(r"sha256:[0-9a-f]{64}", entry[field])

    def test_the_reported_timestamps_bracket_the_divergence(
        self, registry: FakeRegistry, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """The report states both bounds, because neither alone is the truth.

        The registry cannot say *when* a channel tag moved, so the divergence is
        known only as an interval: at most since the pinned build was created,
        at least since the head was. The alert quotes both rather than presenting
        an upper bound as a measurement.
        """
        pins = _incident(registry, pin_age_days=INCIDENT_PIN_AGE_DAYS, head_age_days=INCIDENT_HEAD_AGE_DAYS)

        _run(pins, monkeypatch, tmp_path)

        entry = _report(tmp_path)["drift"][0]
        assert entry["current_age_days"] == pytest.approx(INCIDENT_HEAD_AGE_DAYS, abs=0.05)
        assert entry["current_age_days"] <= entry["age_days"]
        pinned_created = datetime.fromisoformat(entry["pinned_created"])
        current_created = datetime.fromisoformat(entry["current_created"])
        assert pinned_created < current_created
