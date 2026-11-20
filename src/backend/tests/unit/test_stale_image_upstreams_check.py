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

**The real checkout is read too** (:class:`TestTheRealCheckout`), because an
inventory that silently finds nothing is the failure mode this check must not
have: the unit tests on a constructed tree cannot notice the walker missing the
directory the Dockerfiles actually live in.

Placement follows ``test_release_lag_check.py``: the script lives outside the
backend package and is loaded by path through ``tests.support.repo_scripts``.

Traces to issue #3060 (no TC-ID: a CI alarm is not a user-facing case).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

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
        registry = _Registry({_HUB.format("gone/image"): checker.RepositoryNotFoundError("HTTP 404")})

        report = checker.build_report([_image("gone/image")], registry, now=_at("2026-11-20T09:20:00"))

        assert report["alert"] is True
        assert report["images"][0]["status"] == "not found"
        assert "removed or renamed" in report["findings"][0]

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
        }

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
