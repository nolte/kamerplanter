"""Tests for the stale-upstream alarm (``scripts/ci/check_stale_image_upstreams.py``).

**What is under test.** The inventory, the verdict and the fail-loud contract,
driven against *constructed* registry answers. The registry access and the clock
are injected, so nothing here touches the network — a test that asked Docker Hub
"when was nginx last pushed?" would answer something different every day.

**The falsification that matters** lives in :class:`TestTheIncident`: the real
numbers of #3060. ``nginxinc/nginx-unprivileged`` received its last tag push on
2026-10-19T05:04:46Z while ``nginx/nginx-unprivileged`` was pushed on
2026-11-18. Both directions are pinned, including the uncomfortable one: with
the default 45-day window the alarm had NOT fired on the day the incident was
found by other means. That is a measured property of the window and is asserted
rather than hidden behind a threshold chosen to flatter the check.

**The transport is tested against a replaced opener** (:class:`TestTheTransport`):
what ``http_fetch`` raises for each kind of failure and how often it tries. The
readers decide what a status MEANS, so their tests hand the fake registry the
same :class:`HttpStatusError` the transport raises — never the conclusion.

**The real checkout is read too** (:class:`TestTheRealCheckout`), because an
inventory that silently finds nothing is the failure mode this check must not
have: the unit tests on a constructed tree cannot notice the walker missing the
directory the Dockerfiles actually live in.

Placement follows ``test_release_lag_check.py``: the script lives outside the
backend package and is loaded by path through ``tests.support.repo_scripts``.

Traces to issue #3060 (no TC-ID: a CI alarm is not a user-facing case).
"""

from __future__ import annotations

import email.message
import http.client
import http.server
import json
import subprocess
import sys
import threading
import urllib.error
from collections.abc import Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support import renovate_config
from tests.support.repo_scripts import find_repo_root, load_repo_script

checker = load_repo_script("ci/check_stale_image_upstreams")

_DIGEST = "a" * 64
_HUB = "https://hub.docker.com/v2/repositories/{}/tags?page_size=5&ordering=last_updated"


def _hub_answer(pushed: str, tag: str = "1.0") -> dict[str, Any]:
    return {"count": 1, "results": [{"name": tag, "tag_last_pushed": pushed, "last_updated": pushed}]}


class _Registry:
    """A fake ``fetch``: URL -> answer, an exception instance, or (body, headers)."""

    def __init__(self, answers: dict[str, Any]) -> None:
        self.answers = answers
        self.requested: list[tuple[str, dict[str, str]]] = []

    def __call__(self, url: str, headers: Mapping[str, str]) -> tuple[Any, Mapping[str, str]]:
        self.requested.append((url, dict(headers)))
        if url not in self.answers:
            raise AssertionError(f"unexpected request: {url}")
        answer = self.answers[url]
        if isinstance(answer, Exception):
            raise answer
        if isinstance(answer, tuple):
            return answer
        return answer, {}


def _status(code: int, url: str = "https://registry.invalid/") -> Exception:
    """What the transport raises for an HTTP error status."""
    return checker.HttpStatusError(url, code)


def _image(name: str) -> Any:
    return checker.Image(name=name, references=("src/frontend/Dockerfile:50",))


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


@pytest.fixture
def no_exceptions(monkeypatch) -> None:
    """Empty exception tables for a CONSTRUCTED inventory.

    ``build_report`` reports an override whose image nothing pins, so the real
    table would add findings to every test that builds its own image list. The
    real table is checked against the real checkout in ``TestTheRealCheckout``,
    which deliberately does not use this fixture.
    """
    monkeypatch.setattr(checker, "THRESHOLD_OVERRIDES_DAYS", {})
    monkeypatch.setattr(checker, "ACKNOWLEDGED_NOT_CHECKABLE", {})


@pytest.mark.usefixtures("no_exceptions")
class TestTheIncident:
    """#3060, with the dates the registries reported."""

    OLD = _HUB.format("nginxinc/nginx-unprivileged")
    NEW = _HUB.format("nginx/nginx-unprivileged")
    LAST_PUSH_OLD = "2026-10-19T05:04:46.065679Z"

    def _report(self, name: str, now: str) -> dict[str, Any]:
        registry = _Registry(
            {
                self.OLD: _hub_answer(self.LAST_PUSH_OLD, "alpine3.24-perl"),
                self.NEW: _hub_answer("2026-11-18T20:19:46.608506Z", "alpine3.24-perl"),
            }
        )
        return checker.build_report([_image(name)], registry, now=_at(now))

    def test_the_abandoned_repository_fires_once_the_window_has_passed(self) -> None:
        report = self._report("nginxinc/nginx-unprivileged", "2026-12-03T09:20:00")

        assert report["alert"] is True
        assert report["images"][0]["status"] == "stale"
        assert len(report["findings"]) == 1
        finding = report["findings"][0]
        assert "nginxinc/nginx-unprivileged" in finding
        assert "2026-10-19" in finding
        assert "src/frontend/Dockerfile:50" in finding

    def test_the_last_scheduled_run_before_that_is_still_quiet(self) -> None:
        report = self._report("nginxinc/nginx-unprivileged", "2026-12-02T09:20:00")

        assert report["alert"] is False

    def test_it_had_not_fired_on_the_day_the_incident_was_found(self) -> None:
        """Day 31 of silence is inside the 45-day window: the measured limit of the default."""
        report = self._report("nginxinc/nginx-unprivileged", "2026-11-19T09:20:00")

        assert report["alert"] is False
        assert report["images"][0]["age_days"] == pytest.approx(31.2, abs=0.1)

    def test_the_repository_upstream_moved_to_is_fresh(self) -> None:
        report = self._report("nginx/nginx-unprivileged", "2026-12-03T09:20:00")

        assert report["alert"] is False
        assert report["findings"] == []
        assert report["images"][0]["status"] == "fresh"


@pytest.mark.usefixtures("no_exceptions")
class TestTheVerdict:
    def test_an_empty_inventory_is_undetermined_not_clean(self) -> None:
        with pytest.raises(checker.UndeterminedError, match="inventory is empty"):
            checker.build_report([], _Registry({}), now=_at("2026-11-20T09:20:00"))

    def test_an_unreachable_registry_is_undetermined_not_stale(self) -> None:
        registry = _Registry({_HUB.format("library/python"): checker.UndeterminedError("HTTP 429")})

        with pytest.raises(checker.UndeterminedError, match="429"):
            checker.build_report([_image("python")], registry, now=_at("2026-11-20T09:20:00"))

    def test_a_repository_the_registry_does_not_know_is_a_finding(self) -> None:
        registry = _Registry({_HUB.format("gone/image"): _status(404)})

        report = checker.build_report([_image("gone/image")], registry, now=_at("2026-11-20T09:20:00"))

        assert report["alert"] is True
        assert report["images"][0]["status"] == "not found"
        assert "removed or renamed" in report["findings"][0]

    @pytest.mark.parametrize("code", [401, 403, 429, 500, 503])
    def test_any_other_status_on_the_hub_tags_call_is_undetermined(self, code: int) -> None:
        registry = _Registry({_HUB.format("library/python"): _status(code)})

        with pytest.raises(checker.UndeterminedError, match=str(code)):
            checker.build_report([_image("python")], registry, now=_at("2026-11-20T09:20:00"))

    def test_a_hub_tag_name_outside_the_tag_grammar_never_reaches_the_report(self) -> None:
        answer = {
            "results": [
                {"name": "x` | [click](https://evil.invalid) | `", "tag_last_pushed": "2026-11-19T00:00:00Z"},
                {"name": "1.0", "tag_last_pushed": "2026-11-01T00:00:00Z"},
            ]
        }
        registry = _Registry({_HUB.format("library/python"): answer})

        report = checker.build_report([_image("python")], registry, now=_at("2026-11-20T09:20:00"))

        assert report["images"][0]["signal"] == "tag `1.0` pushed"
        assert "evil.invalid" not in json.dumps(report)

    def test_a_registry_without_a_reader_is_reported_not_passed(self) -> None:
        report = checker.build_report([_image("quay.io/some/image")], _Registry({}), now=_at("2026-11-20T09:20:00"))

        assert report["alert"] is True
        assert report["images"][0]["status"] == "not checkable"
        assert "quay.io" in report["findings"][0]

    def test_an_acknowledged_uncheckable_image_is_listed_without_alerting(self, monkeypatch) -> None:
        monkeypatch.setattr(checker, "ACKNOWLEDGED_NOT_CHECKABLE", {"quay.io/some/image": "no anonymous API"})

        report = checker.build_report([_image("quay.io/some/image")], _Registry({}), now=_at("2026-11-20T09:20:00"))

        assert report["alert"] is False
        assert report["images"][0]["status"] == "not checkable (acknowledged)"

    def test_an_override_widens_the_window_for_its_image_only(self, monkeypatch) -> None:
        monkeypatch.setattr(checker, "THRESHOLD_OVERRIDES_DAYS", {"curlimages/curl": (120, "releases rarely")})
        registry = _Registry(
            {
                _HUB.format("curlimages/curl"): _hub_answer("2026-09-01T00:00:00Z"),
                _HUB.format("library/python"): _hub_answer("2026-09-01T00:00:00Z"),
            }
        )

        report = checker.build_report(
            [_image("curlimages/curl"), _image("python")], registry, now=_at("2026-11-20T09:20:00")
        )

        assert {entry["image"]: entry["status"] for entry in report["images"]} == {
            "curlimages/curl": "fresh",
            "python": "stale",
        }

    def test_an_override_for_an_image_nothing_pins_is_a_finding(self, monkeypatch) -> None:
        monkeypatch.setattr(checker, "THRESHOLD_OVERRIDES_DAYS", {"left/behind": (365, "was slow")})
        registry = _Registry({_HUB.format("library/python"): _hub_answer("2026-11-19T00:00:00Z")})

        report = checker.build_report([_image("python")], registry, now=_at("2026-11-20T09:20:00"))

        assert report["alert"] is True
        assert "left/behind" in report["findings"][0]

    def test_the_newest_of_several_tags_counts(self) -> None:
        answer = {
            "results": [
                {"name": "old", "tag_last_pushed": "2026-01-01T00:00:00Z"},
                {"name": "new", "tag_last_pushed": "2026-11-19T00:00:00Z"},
            ]
        }
        registry = _Registry({_HUB.format("library/python"): answer})

        report = checker.build_report([_image("python")], registry, now=_at("2026-11-20T09:20:00"))

        assert report["images"][0]["signal"] == "tag `new` pushed"
        assert report["alert"] is False

    def test_a_hub_repository_without_tags_is_a_finding(self) -> None:
        registry = _Registry({_HUB.format("library/python"): {"results": []}})

        report = checker.build_report([_image("python")], registry, now=_at("2026-11-20T09:20:00"))

        assert report["images"][0]["status"] == "not checkable"
        assert report["alert"] is True


@pytest.mark.usefixtures("no_exceptions")
class TestGhcr:
    """ghcr.io has no push date; the newest tags' image ``created`` is read instead."""

    ROOT = "https://ghcr.io"

    def _answers(self, created: str) -> dict[str, Any]:
        repo = "hadolint/hadolint"
        return {
            f"{self.ROOT}/token?scope=repository:{repo}:pull": {"token": "anonymous"},
            f"{self.ROOT}/v2/{repo}/tags/list?n=1000": (
                {"tags": ["v1.0.0", "latest"]},
                {"Link": f'</v2/{repo}/tags/list?last=latest&n=1000>; rel="next"'},
            ),
            f"{self.ROOT}/v2/{repo}/tags/list?last=latest&n=1000": {"tags": ["v2.15.1", "sha256-" + "b" * 64 + ".att"]},
            f"{self.ROOT}/v2/{repo}/manifests/v1.0.0": {"config": {"digest": "sha256:old"}},
            f"{self.ROOT}/v2/{repo}/manifests/latest": {"config": {"digest": "sha256:new"}},
            f"{self.ROOT}/v2/{repo}/manifests/v2.15.1": {
                "manifests": [
                    {"digest": "sha256:attestation", "platform": {"os": "unknown", "architecture": "unknown"}},
                    {"digest": "sha256:amd64", "platform": {"os": "linux", "architecture": "amd64"}},
                ]
            },
            f"{self.ROOT}/v2/{repo}/manifests/sha256:amd64": {"config": {"digest": "sha256:new"}},
            f"{self.ROOT}/v2/{repo}/blobs/sha256:old": {"created": "2020-01-01T00:00:00Z"},
            f"{self.ROOT}/v2/{repo}/blobs/sha256:new": {"created": created},
        }

    def test_the_newest_build_across_pages_decides(self) -> None:
        registry = _Registry(self._answers("2026-11-17T09:18:51.836390964Z"))

        report = checker.build_report([_image("ghcr.io/hadolint/hadolint")], registry, now=_at("2026-11-20T09:20:00"))

        entry = report["images"][0]
        assert entry["status"] == "fresh"
        assert entry["newest_activity"].startswith("2026-11-17")
        assert "built" in entry["signal"]
        # The attestation tag is never asked for: it has no image config.
        assert not any("sha256-" in url for url, _ in registry.requested)

    def test_only_the_token_endpoint_is_called_without_the_token(self) -> None:
        registry = _Registry(self._answers("2026-11-17T09:18:51Z"))

        checker.build_report([_image("ghcr.io/hadolint/hadolint")], registry, now=_at("2026-11-20T09:20:00"))

        without = [url for url, headers in registry.requested if "Authorization" not in headers]
        assert without == [f"{self.ROOT}/token?scope=repository:hadolint/hadolint:pull"]

    def test_an_old_build_is_stale_past_its_window(self) -> None:
        registry = _Registry(self._answers("2026-07-31T09:56:42.436828635Z"))

        report = checker.build_report([_image("ghcr.io/hadolint/hadolint")], registry, now=_at("2026-11-20T09:20:00"))

        assert report["images"][0]["status"] == "stale"

    def test_epoch_stamped_builds_are_not_checkable_rather_than_ancient(self) -> None:
        answers = self._answers("1970-01-01T00:00:00Z")
        answers[f"{self.ROOT}/v2/hadolint/hadolint/blobs/sha256:old"] = {"created": "1970-01-01T00:00:00Z"}

        report = checker.build_report(
            [_image("ghcr.io/hadolint/hadolint")], _Registry(answers), now=_at("2026-11-20T09:20:00")
        )

        assert report["images"][0]["status"] == "not checkable"
        assert report["alert"] is True

    def _report(self, answers: dict[str, Any]) -> tuple[dict[str, Any], _Registry]:
        registry = _Registry(answers)
        report = checker.build_report([_image("ghcr.io/hadolint/hadolint")], registry, now=_at("2026-11-20T09:20:00"))
        return report, registry

    @pytest.mark.parametrize("code", [401, 403, 404])
    def test_a_refused_token_call_means_the_repository_is_gone(self, code: int) -> None:
        report, _ = self._report({f"{self.ROOT}/token?scope=repository:hadolint/hadolint:pull": _status(code)})

        assert report["images"][0]["status"] == "not found"
        assert "removed or renamed" in report["findings"][0]

    @pytest.mark.parametrize("code", [401, 403, 404])
    def test_a_refused_first_listing_means_the_repository_is_gone(self, code: int) -> None:
        answers = self._answers("2026-11-17T09:18:51Z")
        answers[f"{self.ROOT}/v2/hadolint/hadolint/tags/list?n=1000"] = _status(code)

        report, _ = self._report(answers)

        assert report["images"][0]["status"] == "not found"

    def test_a_later_listing_page_that_fails_is_undetermined_not_gone(self) -> None:
        answers = self._answers("2026-11-17T09:18:51Z")
        answers[f"{self.ROOT}/v2/hadolint/hadolint/tags/list?last=latest&n=1000"] = _status(404)

        with pytest.raises(checker.UndeterminedError, match="404"):
            self._report(answers)

    def test_one_tag_whose_manifest_is_gone_is_skipped_not_a_missing_repository(self) -> None:
        """After a successful listing a 404 speaks about one tag (#3060 review, W2)."""
        answers = self._answers("2026-11-17T09:18:51Z")
        answers[f"{self.ROOT}/v2/hadolint/hadolint/manifests/v2.15.1"] = _status(404)

        report, _ = self._report(answers)

        entry = report["images"][0]
        assert entry["status"] == "fresh"
        assert entry["signal"] == "image `latest` built"
        assert report["findings"] == []

    def test_one_tag_whose_blob_is_gone_is_skipped_too(self) -> None:
        answers = self._answers("2026-11-17T09:18:51Z")
        answers[f"{self.ROOT}/v2/hadolint/hadolint/blobs/sha256:old"] = _status(404)

        report, _ = self._report(answers)

        assert report["images"][0]["status"] == "fresh"

    def test_every_sampled_tag_gone_is_not_checkable_not_a_missing_repository(self) -> None:
        answers = self._answers("2026-11-17T09:18:51Z")
        for tag in ("v1.0.0", "latest", "v2.15.1"):
            answers[f"{self.ROOT}/v2/hadolint/hadolint/manifests/{tag}"] = _status(404)

        report, _ = self._report(answers)

        assert report["images"][0]["status"] == "not checkable"
        assert "removed or renamed" not in report["findings"][0]
        assert "3 answered HTTP 404" in report["findings"][0]

    @pytest.mark.parametrize("code", [401, 403])
    @pytest.mark.parametrize("call", ["manifests/latest", "blobs/sha256:new"])
    def test_a_refusal_after_a_successful_listing_is_undetermined(self, call: str, code: int) -> None:
        answers = self._answers("2026-11-17T09:18:51Z")
        answers[f"{self.ROOT}/v2/hadolint/hadolint/{call}"] = _status(code)

        with pytest.raises(checker.UndeterminedError, match=str(code)):
            self._report(answers)

    def test_only_the_newest_tags_and_latest_are_ever_requested(self) -> None:
        """Seven tags in creation order: the four oldest are never asked for (S5)."""
        repo = "hadolint/hadolint"
        tags = ["v1.0", "v1.1", "latest", "v1.2", "v1.3", "v2.0", "v2.1", "v2.2"]
        answers: dict[str, Any] = {
            f"{self.ROOT}/token?scope=repository:{repo}:pull": {"token": "anonymous"},
            f"{self.ROOT}/v2/{repo}/tags/list?n=1000": {"tags": tags},
        }
        for tag in ("latest", "v2.0", "v2.1", "v2.2"):
            answers[f"{self.ROOT}/v2/{repo}/manifests/{tag}"] = {"config": {"digest": f"sha256:{tag}"}}
            answers[f"{self.ROOT}/v2/{repo}/blobs/sha256:{tag}"] = {"created": "2026-11-17T00:00:00Z"}

        report, registry = self._report(answers)

        assert report["images"][0]["status"] == "fresh"
        asked = {url.rsplit("/", 1)[1] for url, _ in registry.requested if "/manifests/" in url}
        assert asked == {"latest", "v2.0", "v2.1", "v2.2"}
        # `_Registry` raises on any URL it has no answer for, so a request for
        # v1.0–v1.3 would already have failed above; this names the contract.
        assert not asked & {"v1.0", "v1.1", "v1.2", "v1.3"}

    def test_a_tag_name_outside_the_tag_grammar_is_never_requested_or_reported(self) -> None:
        repo = "hadolint/hadolint"
        hostile = "v9`|[x](https://evil.invalid)"
        answers = {
            f"{self.ROOT}/token?scope=repository:{repo}:pull": {"token": "anonymous"},
            f"{self.ROOT}/v2/{repo}/tags/list?n=1000": {"tags": ["v1.0", hostile, "../../other/repo/manifests/x"]},
            f"{self.ROOT}/v2/{repo}/manifests/v1.0": {"config": {"digest": "sha256:one"}},
            f"{self.ROOT}/v2/{repo}/blobs/sha256:one": {"created": "2026-11-17T00:00:00Z"},
        }

        report, registry = self._report(answers)

        assert report["images"][0]["signal"] == "image `v1.0` built"
        assert "evil.invalid" not in json.dumps(report)
        assert all("evil" not in url and ".." not in url for url, _ in registry.requested)

    def test_a_config_digest_outside_the_digest_grammar_is_not_requested(self) -> None:
        answers = self._answers("2026-11-17T09:18:51Z")
        answers[f"{self.ROOT}/v2/hadolint/hadolint/manifests/v2.15.1"] = {
            "config": {"digest": "../../../other/repo/blobs/sha256:x"}
        }

        report, registry = self._report(answers)

        assert report["images"][0]["signal"] == "image `latest` built"
        assert all(".." not in url for url, _ in registry.requested)


class TestTheInventory:
    def _tree(self, root: Path) -> None:
        files = {
            "src/frontend/Dockerfile": (
                f"FROM node:26-alpine@sha256:{_DIGEST} AS base\n"
                f"# FROM nginxinc/nginx-unprivileged:1.31-alpine@sha256:{_DIGEST}\n"
                f"FROM nginx/nginx-unprivileged:1.31-alpine@sha256:{_DIGEST} AS prod\n"
                f"COPY --from=ghcr.io/astral-sh/uv:0.13.8@sha256:{_DIGEST} /uv /bin/uv\n"
            ),
            "docker-compose.yml": f"services:\n  db:\n    image: node:26-alpine@sha256:{_DIGEST}\n",
            ".github/workflows/scan.yml": f"env:\n  ZAP_IMAGE: ghcr.io/zaproxy/zaproxy@sha256:{_DIGEST}\n",
            ".github/lane-inputs/scan--job.yaml": f"text: recorded/copy:1@sha256:{_DIGEST}\n",
            ".claude/worktrees/x/Dockerfile": f"FROM stray/worktree:1@sha256:{_DIGEST}\n",
            "src/backend/tests/unit/guards/fixtures/old.yaml": f"image: old/fixture:1@sha256:{_DIGEST}\n",
            "node_modules/pkg/Dockerfile": f"FROM vendored/image:1@sha256:{_DIGEST}\n",
            "helm/kamerplanter/values.yaml": (
                "dependencies:\n  - repository: https://example.invalid/charts/\n"
                "image:\n  repository: ghcr.io/nolte/kamerplanter-backend\n  tag: latest\n"
                'sidecar:\n  image:\n    repository: rclone/rclone\n    tag: "1.76.0"\n'
                # Line 10 onwards: a comment, a blank line and another key
                # between `repository:` and `tag:` (values.yaml has this form).
                "client:\n  image:\n    repository: arangodb\n    # Same tag as the server.\n\n"
                "    pullPolicy: IfNotPresent\n    tag: '{{ .Values.server.tag }}'\n"
                # Line 17 onwards: `tag:` first, in the `tag@digest` form that
                # scripts/ci/pin_chart_image_digests.sh writes.
                f'pinned:\n  image:\n    tag: "2.19.3@sha256:{_DIGEST}"\n    pullPolicy: Always\n'
                "    repository: timescale/timescaledb\n"
                # Line 22 onwards: a separate `registry:` key.
                "mirrored:\n  image:\n    registry: quay.io\n    repository: some/tool\n    tag: v1\n"
                # Line 27 onwards: not an image — no tag, no digest, no `image:` parent.
                "source:\n  repository: some/git-repo\n  branch: main\n"
            ),
            "helm/kamerplanter/values-dev.yaml": "image:\n  repository: kamerplanter-backend\n  tag: latest\n",
        }
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def test_it_reads_digest_pins_and_helm_image_blocks_and_nothing_else(self, tmp_path: Path) -> None:
        self._tree(tmp_path)

        found = {image.name: image.references for image in checker.inventory(tmp_path)}

        assert found == {
            "ghcr.io/astral-sh/uv": ("src/frontend/Dockerfile:4",),
            "ghcr.io/zaproxy/zaproxy": (".github/workflows/scan.yml:2",),
            "nginx/nginx-unprivileged": ("src/frontend/Dockerfile:3",),
            "node": ("docker-compose.yml:3", "src/frontend/Dockerfile:1"),
            "rclone/rclone": ("helm/kamerplanter/values.yaml:8",),
            "arangodb": ("helm/kamerplanter/values.yaml:12",),
            "timescale/timescaledb": ("helm/kamerplanter/values.yaml:21",),
            "quay.io/some/tool": ("helm/kamerplanter/values.yaml:25",),
        }

    def test_a_numeric_tag_on_a_single_component_image_is_a_tag_not_a_port(self, tmp_path: Path) -> None:
        """`postgres:18@sha256:…` is the image `postgres`, not `postgres:18` (W1)."""
        (tmp_path / "docker-compose.yml").write_text(
            f"services:\n  db:\n    image: postgres:18@sha256:{_DIGEST}\n"
            f"  build:\n    image: node:26@sha256:{_DIGEST}\n"
            f"  local:\n    image: localhost:5000/thing:1@sha256:{_DIGEST}\n",
            encoding="utf-8",
        )

        found = {image.name: image.references for image in checker.inventory(tmp_path)}

        assert found == {
            "postgres": ("docker-compose.yml:3",),
            "node": ("docker-compose.yml:5",),
            "localhost:5000/thing": ("docker-compose.yml:7",),
        }
        assert checker.split_registry("postgres") == ("docker.io", "library/postgres")
        assert checker.split_registry("localhost:5000/thing") == ("localhost:5000", "thing")

    def test_a_tag_line_carrying_a_digest_names_no_phantom_image(self, tmp_path: Path) -> None:
        """`tag: "1.76.0@sha256:…"` belongs to its `repository:`; `1.76.0` is not an image (W4)."""
        values = tmp_path / "helm" / "kamerplanter" / "values.yaml"
        values.parent.mkdir(parents=True)
        values.write_text(
            f'sidecar:\n  image:\n    repository: rclone/rclone\n    tag: "1.76.0@sha256:{_DIGEST}"\n',
            encoding="utf-8",
        )

        found = {image.name: image.references for image in checker.inventory(tmp_path)}

        assert found == {"rclone/rclone": ("helm/kamerplanter/values.yaml:3",)}

    @pytest.mark.parametrize(
        ("relative", "content"),
        [
            # No `repository:` in the mapping: nothing says which image the digest pins.
            ("helm/kamerplanter/values.yaml", f'sidecar:\n  image:\n    tag: "1.76.0@sha256:{_DIGEST}"\n'),
            # A templated name: the pin exists but its image cannot be read.
            (
                "helm/kamerplanter/values.yaml",
                f'sidecar:\n  image:\n    repository: "{{{{ .Values.x }}}}"\n    tag: "1@sha256:{_DIGEST}"\n',
            ),
            # Outside the Helm values no reader owns a `tag:` line.
            ("deploy/other.yaml", f'image:\n  repository: rclone/rclone\n  tag: "1.76.0@sha256:{_DIGEST}"\n'),
        ],
    )
    def test_a_digest_on_a_tag_line_nothing_owns_is_undetermined(
        self, tmp_path: Path, relative: str, content: str
    ) -> None:
        path = tmp_path / relative
        path.parent.mkdir(parents=True)
        path.write_text(content, encoding="utf-8")

        with pytest.raises(checker.UndeterminedError, match=r"\.yaml:\d+ carries a sha256 digest"):
            checker.inventory(tmp_path)

    def test_a_helm_repository_that_is_not_an_image_name_is_undetermined(self, tmp_path: Path) -> None:
        """The name is quoted in the alert issue's Markdown, so it is held to the image grammar (S3)."""
        values = tmp_path / "helm" / "kamerplanter" / "values.yaml"
        values.parent.mkdir(parents=True)
        values.write_text('image:\n  repository: "x`|[a](evil.invalid)"\n  tag: v1\n', encoding="utf-8")

        with pytest.raises(checker.UndeterminedError, match="values.yaml:2 names an image repository"):
            checker.inventory(tmp_path)

    def test_a_digest_without_a_readable_image_name_is_undetermined(self, tmp_path: Path) -> None:
        (tmp_path / "Dockerfile").write_text(f"FROM ${{BASE}}@sha256:{_DIGEST}\n", encoding="utf-8")

        with pytest.raises(checker.UndeterminedError, match="Dockerfile:1"):
            checker.inventory(tmp_path)

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("python", ("docker.io", "library/python")),
            ("nginx/nginx-unprivileged", ("docker.io", "nginx/nginx-unprivileged")),
            ("ghcr.io/astral-sh/uv", ("ghcr.io", "astral-sh/uv")),
            ("localhost:5000/thing", ("localhost:5000", "thing")),
            # Docker Hub spelled out is still Docker Hub, `library/` included (S2).
            ("docker.io/python", ("docker.io", "library/python")),
            ("docker.io/library/python", ("docker.io", "library/python")),
            ("index.docker.io/nginx/nginx-unprivileged", ("docker.io", "nginx/nginx-unprivileged")),
            ("registry-1.docker.io/busybox", ("docker.io", "library/busybox")),
        ],
    )
    def test_registry_and_repository_follow_dockers_naming_rule(self, name: str, expected: tuple[str, str]) -> None:
        assert checker.split_registry(name) == expected


@pytest.mark.usefixtures("no_exceptions")
class TestMain:
    def test_a_determined_result_writes_the_report_and_exits_zero(self, tmp_path: Path, capsys) -> None:
        (tmp_path / "Dockerfile").write_text(f"FROM python:3.15-slim@sha256:{_DIGEST}\n", encoding="utf-8")
        registry = _Registry({_HUB.format("library/python"): _hub_answer("2026-01-01T00:00:00Z")})
        report_path = tmp_path / "report.json"

        code = checker.main([str(report_path)], fetch=registry, now=_at("2026-11-20T09:20:00"), repo_root=tmp_path)

        assert code == 0
        assert json.loads(report_path.read_text())["alert"] is True
        printed = capsys.readouterr().out
        assert "Looked at 1 third-party image(s)" in printed
        assert "[stale] python" in printed

    def test_an_empty_checkout_raises_and_writes_no_report(self, tmp_path: Path) -> None:
        report_path = tmp_path / "report.json"

        with pytest.raises(checker.UndeterminedError):
            checker.main([str(report_path)], fetch=_Registry({}), now=_at("2026-11-20T09:20:00"), repo_root=tmp_path)

        assert not report_path.exists()


class _Response:
    """What the opener returns: a context manager with ``read()`` and ``headers``."""

    def __init__(self, body: bytes, headers: dict[str, str] | None = None) -> None:
        self._body = body
        self.headers = headers or {}

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


def _http_error(code: int, retry_after: str | None = None) -> urllib.error.HTTPError:
    headers = email.message.Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return urllib.error.HTTPError("https://registry.invalid/x", code, "status", headers, None)


class TestTheTransport:
    """``http_fetch`` itself: exception class and number of attempts per kind of failure."""

    URL = "https://registry.invalid/v2/some/repo/tags/list"

    @pytest.fixture
    def wire(self, monkeypatch) -> dict[str, Any]:
        """Replace the opener and the clock; ``answers`` is consumed one per attempt."""
        state: dict[str, Any] = {"answers": [], "requests": [], "slept": []}

        def fake_open(request: Any, timeout: float | None = None) -> Any:
            state["requests"].append(request)
            answer = state["answers"].pop(0)
            if isinstance(answer, Exception):
                raise answer
            return answer

        monkeypatch.setattr(checker._OPENER, "open", fake_open)
        monkeypatch.setattr(checker.time, "sleep", state["slept"].append)
        return state

    def test_a_good_answer_is_decoded_and_carries_the_client_name_and_headers(self, wire: dict[str, Any]) -> None:
        wire["answers"] = [_Response(b'{"tags": ["v1"]}', {"Link": "next"})]

        body, headers = checker.http_fetch(self.URL, {"Authorization": "Bearer t"})

        assert body == {"tags": ["v1"]}
        assert headers == {"Link": "next"}
        request = wire["requests"][0]
        assert request.get_header("User-agent") == checker.USER_AGENT
        assert request.get_header("Authorization") == "Bearer t"
        assert wire["slept"] == []

    @pytest.mark.parametrize("code", [400, 401, 403, 404])
    def test_a_definite_status_is_reported_at_once_and_is_not_a_conclusion(
        self, wire: dict[str, Any], code: int
    ) -> None:
        """One attempt, and the STATUS — the transport does not know which call this was (W2)."""
        wire["answers"] = [_http_error(code)]

        with pytest.raises(checker.HttpStatusError) as raised:
            checker.http_fetch(self.URL, {})

        assert raised.value.status == code
        assert isinstance(raised.value, checker.UndeterminedError)
        assert not isinstance(raised.value, checker.RepositoryNotFoundError)
        assert len(wire["requests"]) == 1
        assert wire["slept"] == []

    @pytest.mark.parametrize("code", [429, 500, 503])
    def test_a_transient_status_is_retried_and_then_undetermined(self, wire: dict[str, Any], code: int) -> None:
        wire["answers"] = [_http_error(code)] * checker.HTTP_ATTEMPTS

        with pytest.raises(checker.UndeterminedError, match=str(code)) as raised:
            checker.http_fetch(self.URL, {})

        assert raised.value.status == code
        assert len(wire["requests"]) == checker.HTTP_ATTEMPTS
        assert wire["slept"] == [2.0, 4.0]

    def test_a_transient_status_followed_by_an_answer_succeeds(self, wire: dict[str, Any]) -> None:
        wire["answers"] = [_http_error(503), _Response(b"{}")]

        assert checker.http_fetch(self.URL, {})[0] == {}
        assert len(wire["requests"]) == 2

    @pytest.mark.parametrize(
        "failure",
        [
            urllib.error.URLError("name resolution failed"),
            TimeoutError("timed out"),
            ConnectionResetError("reset by peer"),
            http.client.RemoteDisconnected("closed without response"),
        ],
        ids=lambda failure: type(failure).__name__,
    )
    def test_a_transport_failure_is_retried_and_then_undetermined(
        self, wire: dict[str, Any], failure: Exception
    ) -> None:
        wire["answers"] = [failure] * checker.HTTP_ATTEMPTS

        with pytest.raises(checker.UndeterminedError, match=type(failure).__name__) as raised:
            checker.http_fetch(self.URL, {})

        assert not isinstance(raised.value, checker.HttpStatusError)
        assert len(wire["requests"]) == checker.HTTP_ATTEMPTS

    def test_a_body_cut_off_mid_read_is_retried(self, wire: dict[str, Any]) -> None:
        wire["answers"] = [_Response(http.client.IncompleteRead(b"{"))] * checker.HTTP_ATTEMPTS  # type: ignore[arg-type]

        with pytest.raises(checker.UndeterminedError, match="IncompleteRead"):
            checker.http_fetch(self.URL, {})

        assert len(wire["requests"]) == checker.HTTP_ATTEMPTS

    @pytest.mark.parametrize(
        "body", [b"<html>rate limited</html>", b"", b"\xff\xfe\xfd"], ids=["html", "empty", "bytes"]
    )
    def test_an_undecodable_answer_is_undetermined_without_a_retry(self, wire: dict[str, Any], body: bytes) -> None:
        wire["answers"] = [_Response(body)]

        with pytest.raises(checker.UndeterminedError, match="not decodable JSON"):
            checker.http_fetch(self.URL, {})

        assert len(wire["requests"]) == 1

    @pytest.mark.parametrize(
        ("retry_after", "expected"),
        [
            ("7", 7.0),
            (str(10**6), float(checker.RETRY_AFTER_CAP_SECONDS)),
            # An HTTP date, zero or nonsense: the built-in backoff applies.
            ("Wed, 21 Oct 2026 07:28:00 GMT", 2.0),
            ("0", 2.0),
            (None, 2.0),
        ],
    )
    def test_retry_after_is_honoured_up_to_the_cap(
        self, wire: dict[str, Any], retry_after: str | None, expected: float
    ) -> None:
        wire["answers"] = [_http_error(429, retry_after), _Response(b"{}")]

        checker.http_fetch(self.URL, {})

        assert wire["slept"] == [expected]


class TestRedirects:
    """A registry token is sent to the registry and to nobody it redirects to."""

    @pytest.fixture
    def servers(self, monkeypatch) -> Iterator[tuple[str, str, list[tuple[str, str | None]]]]:
        """Two loopback origins; each request is recorded as ``(path, Authorization)``."""
        monkeypatch.setenv("no_proxy", "127.0.0.1")
        monkeypatch.setenv("NO_PROXY", "127.0.0.1")
        seen: list[tuple[str, str | None]] = []
        locations: dict[str, str] = {}

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - http.server's name
                seen.append((self.path, self.headers.get("Authorization")))
                if self.path in locations:
                    self.send_response(307)
                    self.send_header("Location", locations[self.path])
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                body = b'{"created": "2026-11-17T00:00:00Z"}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_: object) -> None:
                return None

        started = [http.server.HTTPServer(("127.0.0.1", 0), Handler) for _ in range(2)]
        for server in started:
            threading.Thread(target=server.serve_forever, daemon=True).start()
        registry, storage = (f"http://127.0.0.1:{server.server_address[1]}" for server in started)
        locations["/blob-elsewhere"] = f"{storage}/signed-blob"
        locations["/blob-here"] = f"{registry}/same-origin-blob"
        try:
            yield registry, storage, seen
        finally:
            for server in started:
                server.shutdown()
                server.server_close()

    def test_the_token_is_not_forwarded_to_another_host(self, servers: tuple[str, str, list[Any]]) -> None:
        registry, _, seen = servers

        body, _ = checker.http_fetch(f"{registry}/blob-elsewhere", {"Authorization": "Bearer registry-token"})

        assert body == {"created": "2026-11-17T00:00:00Z"}
        assert seen == [("/blob-elsewhere", "Bearer registry-token"), ("/signed-blob", None)]

    def test_the_token_stays_on_a_redirect_within_the_registry(self, servers: tuple[str, str, list[Any]]) -> None:
        registry, _, seen = servers

        checker.http_fetch(f"{registry}/blob-here", {"Authorization": "Bearer registry-token"})

        assert seen == [("/blob-here", "Bearer registry-token"), ("/same-origin-blob", "Bearer registry-token")]


class TestTheEntryPoint:
    """The script as CI runs it: exit code, report file and the ``::error`` line."""

    def _run(self, checkout: Path) -> tuple[subprocess.CompletedProcess[str], Path]:
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None
        report = checkout / "stale-image-report.json"
        completed = subprocess.run(  # noqa: S603 - our own script, fixed arguments
            [sys.executable, str(root / "scripts" / "ci" / "check_stale_image_upstreams.py"), str(report)],
            cwd=checkout,
            env={"GITHUB_WORKSPACE": str(checkout), "PATH": ""},
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        return completed, report

    def test_undetermined_exits_non_zero_says_so_and_writes_no_report(self, tmp_path: Path) -> None:
        """An empty checkout: nothing to ask a registry, so no request is made."""
        completed, report = self._run(tmp_path)

        assert completed.returncode == 1
        assert "::error::stale image upstream check could not be determined" in completed.stderr
        assert "inventory is empty" in completed.stderr
        assert not report.exists()

    def test_determined_writes_the_report_and_exits_zero_even_with_findings(self, tmp_path: Path) -> None:
        """One image on a registry without a reader: a finding, and again no request."""
        (tmp_path / "Dockerfile").write_text(f"FROM quay.io/some/image:1@sha256:{_DIGEST}\n", encoding="utf-8")

        completed, report = self._run(tmp_path)

        assert completed.returncode == 0, completed.stderr
        written = json.loads(report.read_text(encoding="utf-8"))
        assert written["alert"] is True
        assert [entry["image"] for entry in written["images"]] == ["quay.io/some/image"]
        assert "[not checkable] quay.io/some/image" in completed.stdout

    def test_an_unreachable_registry_through_the_real_transport_writes_no_report(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """``main`` with the REAL ``http_fetch``: the transport raises, nothing is written."""
        (tmp_path / "Dockerfile").write_text(f"FROM python:3.15-slim@sha256:{_DIGEST}\n", encoding="utf-8")
        attempts: list[Any] = []

        def unreachable(request: Any, timeout: float | None = None) -> Any:
            attempts.append(request.full_url)
            raise urllib.error.URLError("no route to host")

        monkeypatch.setattr(checker._OPENER, "open", unreachable)
        monkeypatch.setattr(checker.time, "sleep", lambda _: None)
        report = tmp_path / "report.json"

        with pytest.raises(checker.UndeterminedError, match="no route to host"):
            checker.main([str(report)], now=_at("2026-11-20T09:20:00"), repo_root=tmp_path)

        assert attempts == [_HUB.format("library/python")] * checker.HTTP_ATTEMPTS
        assert not report.exists()


class TestTheWorkflowJob:
    """The two properties of the job that live in the workflow, read from the parsed YAML."""

    @pytest.fixture
    def steps(self) -> list[dict[str, Any]]:
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None
        workflow = yaml.safe_load((root / ".github" / "workflows" / "renovate-health.yml").read_text(encoding="utf-8"))
        return workflow["jobs"]["stale-image-upstreams"]["steps"]

    def test_the_checkout_does_not_leave_the_token_beside_the_registry_requests(
        self, steps: list[dict[str, Any]]
    ) -> None:
        checkouts = [step for step in steps if str(step.get("uses", "")).startswith("actions/checkout@")]

        assert len(checkouts) == 1
        assert checkouts[0]["with"]["persist-credentials"] is False

    def test_the_script_step_is_handed_no_token(self, steps: list[dict[str, Any]]) -> None:
        script_steps = [step for step in steps if "check_stale_image_upstreams.py" in str(step.get("run", ""))]

        assert len(script_steps) == 1
        assert "env" not in script_steps[0]

    def test_the_existing_issue_is_matched_by_label_and_exact_title(self, steps: list[dict[str, Any]]) -> None:
        """A hand-labelled issue with another title is not updated or closed (S4)."""
        scripts = [
            step["with"]["script"] for step in steps if str(step.get("uses", "")).startswith("actions/github-script@")
        ]
        assert len(scripts) == 1
        code = [line.strip() for line in scripts[0].splitlines() if not line.strip().startswith("//")]

        assert "})).data.filter(i => !i.pull_request && i.title === TITLE);" in code
        assert "const existing = open[0];" in code
        assert "labels: LABEL," in code


class TestTheRealCheckout:
    """The inventory over THIS repository: not empty, and not narrower than Renovate's own list."""

    @pytest.fixture
    def names(self) -> set[str]:
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None
        return {image.name for image in checker.inventory(root)}

    def test_the_image_of_the_incident_is_in_it(self, names: set[str]) -> None:
        assert "nginx/nginx-unprivileged" in names
        assert "nginxinc/nginx-unprivileged" not in names

    def test_every_image_renovate_groups_as_third_party_is_in_it(self, names: set[str]) -> None:
        root = find_repo_root(Path(__file__).resolve())
        assert root is not None
        config = renovate_config.load((root / "renovate.json5").read_text(encoding="utf-8"))
        grouped = [
            rule["matchPackageNames"]
            for rule in config["packageRules"]
            if "third-party images" in str(rule.get("groupName", ""))
        ]
        assert len(grouped) == 1, "the `third-party images` rule was renamed or split; re-anchor this test"
        assert set(grouped[0]) <= names, sorted(set(grouped[0]) - names)

    def test_every_image_has_a_reader_or_an_acknowledgement(self, names: set[str]) -> None:
        unread = {
            name
            for name in names
            if checker.split_registry(name)[0] not in checker.READERS and name not in checker.ACKNOWLEDGED_NOT_CHECKABLE
        }
        assert unread == set()

    def test_no_exception_outlives_its_image(self, names: set[str]) -> None:
        assert set(checker.THRESHOLD_OVERRIDES_DAYS) <= names
        assert set(checker.ACKNOWLEDGED_NOT_CHECKABLE) <= names
