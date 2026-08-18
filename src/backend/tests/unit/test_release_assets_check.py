"""Tests for the release-completeness alarm (``scripts/ci/check_release_assets.py``).

**What is under test.** The verdict logic, the floor, the settle window and the
fail-loud contract, driven against *constructed* API payloads. Both the HTTP
layer and the clock are injected, so nothing here touches the network, the
GitHub API or a live ``gh`` — a test that asked the real API "is the newest
release complete?" would answer something different after every release and
assert nothing.

**The falsification that matters** lives in :class:`TestTheIncident`. It replays
the state measured on 2026-08-18 with ``gh release view <tag> --json assets``:

    v0.2.0   assets == ["openapi.json"], body without the packages markers
    v0.0.24  assets == ["default.env.example-0.0.24", "docker-compose-0.0.24.yml",
                        "kamerplanter-0.0.24.tgz", "openapi.json"]

Both directions are pinned, because a check that only ever says "incomplete" is
as worthless as one that only ever says "fine".

**One measured fact the plan's acceptance criteria did not anticipate**, and it
is asserted here rather than papered over: v0.0.24's release body carries **no**
``<!-- kp:packages:begin -->`` marker either (``gh release view v0.0.24 --json
body | grep -c`` returns 0). The marker pair was introduced by commit
``3054b7d96`` (#886) on 2026-08-01 — the very commit that broke the chart job —
and v0.0.24 was published 2026-07-30, two days earlier. It carries a plain
``## Packages`` heading with no delimiters. So the honest negative twin is *two*
tests: v0.0.24 replayed exactly as measured (its **assets** are complete, and it
sits below the floor so it is never judged), and the forward shape a repaired
release actually produces (four assets **plus** the marker pair) yielding
silence. Handing the v0.0.24 fixture a marker it never had would be a fixture
inventing impossible data, and the positive result would then certify nothing.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package (it runs on a bare runner with none of
this project's dependencies installed), so it is loaded by path through
``tests.support.repo_scripts``. It is not a backend test in subject; it is one in
placement, because this is the tier that runs.

Traces to issue #1218 (no TC-ID: a CI alarm is not a user-facing case).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.support.repo_scripts import find_repo_root, load_repo_script

checker = load_repo_script("ci/check_release_assets")

REPOSITORY = "nolte/kamerplanter"
RELEASES_URL = f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100"

#: The shipped default, restated here so a change to it breaks a test rather
#: than silently widening or narrowing what the check judges.
SHIPPED_FLOOR = "2026-08-18T00:00:00Z"

PACKAGES_BLOCK = (
    "<!-- kp:packages:begin -->\n\n## Packages\n\n### Helm Chart\n"
    "- `oci://ghcr.io/nolte/charts/kamerplanter:0.3.0`\n<!-- kp:packages:end -->"
)


def at(moment: str) -> datetime:
    """Parse a ``Z``-suffixed instant into an aware UTC datetime."""
    return datetime.fromisoformat(moment.replace("Z", "+00:00"))


# --------------------------------------------------------------------------- #
# Payload builders — shaped exactly like the GitHub REST responses.
# --------------------------------------------------------------------------- #


def release(
    tag: str,
    *,
    published_at: str | None = None,
    assets: list[str] | None = None,
    body: str = "",
    draft: bool = False,
    prerelease: bool = False,
) -> dict[str, Any]:
    """One entry of the ``GET /repos/{repo}/releases`` array."""
    return {
        "tag_name": tag,
        "name": tag,
        "draft": draft,
        "prerelease": prerelease,
        "published_at": published_at,
        "created_at": published_at,
        "html_url": f"https://github.com/{REPOSITORY}/releases/tag/{tag}",
        "body": body,
        "assets": [{"name": name} for name in (assets or [])],
    }


def complete_release(tag: str, *, published_at: str) -> dict[str, Any]:
    """A release carrying everything a repaired delivery run produces.

    Built from :func:`checker.expected_assets` rather than a hand-written list,
    so the "silence" direction cannot quietly diverge from the expectation the
    check enforces — if a new expected asset is added and this builder is not
    updated, the negative test goes red, which is the correct outcome.
    """
    return release(
        tag,
        published_at=published_at,
        assets=list(checker.expected_assets(tag)),
        body=f"Release notes.\n\n{PACKAGES_BLOCK}",
    )


class RecordingFetch:
    """A routing fake for the injected HTTP layer, recording every URL."""

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.urls: list[str] = []

    def __call__(self, url: str) -> Any:
        self.urls.append(url)
        if url not in self.routes:
            raise checker.ReleaseAssetsError(f"GET {url} failed: HTTP 404")
        value = self.routes[url]
        if isinstance(value, Exception):
            raise value
        return value


def fetching(*releases: dict[str, Any]) -> RecordingFetch:
    """A fake serving *releases* on the one URL the check requests."""
    return RecordingFetch({RELEASES_URL: list(releases)})


def build(
    fetch: Callable[[str], Any],
    *,
    now: str,
    floor: str = SHIPPED_FLOOR,
    settle_hours: float = 6.0,
) -> dict[str, Any]:
    """Call the script's report builder with the standard arguments."""
    return checker.build_report(
        fetch,
        repository=REPOSITORY,
        floor=at(floor),
        settle_hours=settle_hours,
        now=at(now),
    )


def entry_for(report: dict[str, Any], tag: str) -> dict[str, Any]:
    """The evaluated entry for *tag*, or fail loudly if it was not judged."""
    matches = [item for item in report["evaluated"] if item["tag"] == tag]
    assert matches, f"{tag} was not evaluated; evaluated={[i['tag'] for i in report['evaluated']]}"
    return matches[0]


# --------------------------------------------------------------------------- #
# The measured releases, exactly as `gh release view` returned them.
# --------------------------------------------------------------------------- #

#: v0.2.0 as measured on 2026-08-18: one asset, no packages markers in the body.
#: The body text is abbreviated; what is load-bearing is the ABSENCE of the
#: markers, which was verified with `gh release view v0.2.0 --json body`.
MEASURED_V0_2_0 = release(
    "v0.2.0",
    published_at="2026-08-13T18:09:49Z",
    assets=["openapi.json"],
    body="## What's Changed\n\n* a pile of merged pull requests\n",
)

#: v0.1.0 as measured: the same loss, one week earlier. The regression starts
#: here, not at v0.2.0 — the issue body says otherwise and is wrong.
MEASURED_V0_1_0 = release(
    "v0.1.0",
    published_at="2026-08-06T13:37:49Z",
    assets=["openapi.json"],
    body="## What's Changed\n\n* a pile of merged pull requests\n",
)

#: v0.0.24 as measured: the last complete asset set, published 2026-07-30 —
#: two days BEFORE #886 introduced the packages markers, so its body has none.
MEASURED_V0_0_24 = release(
    "v0.0.24",
    published_at="2026-07-30T19:03:00Z",
    assets=[
        "default.env.example-0.0.24",
        "docker-compose-0.0.24.yml",
        "kamerplanter-0.0.24.tgz",
        "openapi.json",
    ],
    body="## What's Changed\n\n## Packages\n\n### Container Images\n- `ghcr.io/nolte/kamerplanter-backend:0.0.24`\n",
)

#: A floor low enough to judge the measured history — used only where the point
#: of the test is the verdict on that history, never as the shipped default.
FLOOR_BEFORE_THE_INCIDENT = "2026-07-01T00:00:00Z"


class TestTheIncident:
    """Replay of the measured 2026-08-18 state, and its negative twin."""

    def test_the_measured_v0_2_0_state_is_a_finding_naming_all_four_losses(self) -> None:
        """Positive direction: exactly three missing assets plus the missing block.

        The floor is lowered here on purpose — the point of this test is the
        verdict on the measured payload, not the floor. :class:`TestTheFloor`
        pins the floor separately, so neither can hide the other.
        """
        report = build(
            fetching(MEASURED_V0_2_0),
            now="2026-08-18T10:00:00Z",
            floor=FLOOR_BEFORE_THE_INCIDENT,
        )

        assert report["alert"] is True
        entry = entry_for(report, "v0.2.0")
        assert entry["missing_assets"] == [
            "kamerplanter-0.2.0.tgz",
            "docker-compose-0.2.0.yml",
            "default.env.example-0.2.0",
        ]
        # openapi.json comes from release-publish.yml, a different workflow, and
        # survived. If it ever shows up as missing here, the fixture drifted.
        assert "openapi.json" not in entry["missing_assets"]
        assert entry["present_assets"] == ["openapi.json"]
        assert entry["packages_block_present"] is False
        assert entry["complete"] is False

    def test_both_broken_releases_are_named_not_only_the_newest(self) -> None:
        """The asset loss spans v0.1.0 AND v0.2.0; a newest-only check forgets one.

        This is the shape that makes "watch only the newest release" wrong: once
        a good release follows, a newest-only alert closes and the older hole
        stays unrepaired and unmentioned.

        v0.0.24 is in this payload as the era control. Its ASSETS are complete
        — that is the measured negative direction — and it appears among the
        incomplete entries here only because its body predates the #886 markers.
        Under the SHIPPED floor it is never evaluated at all; only the
        artificially lowered floor of this test reaches back that far.
        """
        report = build(
            fetching(MEASURED_V0_2_0, MEASURED_V0_1_0, MEASURED_V0_0_24),
            now="2026-08-18T10:00:00Z",
            floor=FLOOR_BEFORE_THE_INCIDENT,
        )

        assert report["alert"] is True
        assert [entry["tag"] for entry in report["evaluated"]] == ["v0.2.0", "v0.1.0", "v0.0.24"]
        # The asset loss — the half #1218 is about — is exactly the two releases.
        assert [entry["tag"] for entry in report["evaluated"] if entry["missing_assets"]] == [
            "v0.2.0",
            "v0.1.0",
        ]
        assert entry_for(report, "v0.0.24")["missing_assets"] == []

    def test_v0_0_24_carries_its_full_asset_set_as_measured(self) -> None:
        """Negative direction on the measured data: nothing is missing.

        Asserted on ``missing_assets`` rather than on ``alert``, because
        v0.0.24's body genuinely predates the packages markers (#886,
        2026-08-01, two days after it was published). Giving the fixture a
        marker it never had would make this a test of invented data.
        """
        report = build(
            fetching(MEASURED_V0_0_24),
            now="2026-08-18T10:00:00Z",
            floor=FLOOR_BEFORE_THE_INCIDENT,
        )
        entry = entry_for(report, "v0.0.24")

        assert entry["missing_assets"] == []
        assert entry["packages_block_present"] is False

    def test_a_repaired_release_is_silent(self) -> None:
        """Negative direction, forward shape: the fix's output raises no alert.

        This is the twin that matters operationally — the state
        `update-release-assets` produces once it stops being skipped. Without
        it, a check hard-wired to "alert" would pass every test above.
        """
        report = build(
            fetching(complete_release("v0.3.0", published_at="2026-09-01T12:00:00Z")),
            now="2026-09-02T10:00:00Z",
        )

        assert report["alert"] is False
        assert report["incomplete"] == []
        entry = entry_for(report, "v0.3.0")
        assert entry["complete"] is True
        assert entry["missing_assets"] == []
        assert entry["packages_block_present"] is True


# --------------------------------------------------------------------------- #
# The floor.
# --------------------------------------------------------------------------- #


class TestTheFloor:
    """Both directions of the documented floor (issue #1218, Q4)."""

    def test_a_release_published_before_the_floor_is_not_evaluated(self) -> None:
        """v0.2.0 under the SHIPPED floor: named as skipped, never judged.

        This is the whole reason the floor exists. Retro-fitting assets onto a
        published release is out of scope, so an unfloored check would open an
        alert on day one and keep it open forever.
        """
        report = build(fetching(MEASURED_V0_2_0), now="2026-08-18T10:00:00Z")

        assert report["alert"] is False
        assert report["evaluated"] == []
        assert report["skipped_below_floor"] == ["v0.2.0"]
        # The floor must never be silent: it is reported on every run.
        assert report["floor"] == "2026-08-18T00:00:00+00:00"

    def test_the_same_release_one_second_after_the_floor_is_evaluated(self) -> None:
        """The negative twin of the test above: the floor is not a blanket mute.

        Same broken payload, published a second past the floor. Without this,
        a floor set to the year 3000 would pass every other floor test.
        """
        just_after = release(
            "v0.2.0",
            published_at="2026-08-18T00:00:01Z",
            assets=["openapi.json"],
            body="## What's Changed",
        )
        report = build(fetching(just_after), now="2026-08-19T10:00:00Z")

        assert report["alert"] is True
        assert report["skipped_below_floor"] == []
        assert entry_for(report, "v0.2.0")["missing_assets"]

    def test_the_boundary_is_inclusive(self) -> None:
        """ "At or after" means at: a release published exactly on the floor counts."""
        on_floor = release(
            "v0.3.0",
            published_at=SHIPPED_FLOOR,
            assets=["openapi.json"],
            body="",
        )
        report = build(fetching(on_floor), now="2026-08-19T10:00:00Z")

        assert report["skipped_below_floor"] == []
        assert report["alert"] is True

    def test_the_shipped_default_floor_is_the_dated_decision(self) -> None:
        """Pin the constant itself, so moving it is a visible, reviewed change.

        The floor is a decision about which published releases this project is
        willing to be held to. A silently edited constant would undo that.
        """
        assert checker.DEFAULT_FLOOR == SHIPPED_FLOOR

    def test_a_floor_predating_a_truncated_history_fails_loud(self) -> None:
        """A full page plus a floor below it means invisible releases — say so.

        Under-reporting silently is the failure mode this whole file exists to
        prevent, so the check refuses rather than judging a truncated window.
        """
        page = [
            release(
                f"v9.0.{index}",
                published_at=f"2026-08-{(index % 28) + 1:02d}T00:00:00Z",
                assets=["openapi.json"],
            )
            for index in range(100)
        ]
        with pytest.raises(checker.ReleaseAssetsError, match="truncated"):
            build(fetching(*page), now="2026-09-30T00:00:00Z", floor="2020-01-01T00:00:00Z")


# --------------------------------------------------------------------------- #
# The settle window.
# --------------------------------------------------------------------------- #


class TestTheSettleWindow:
    """A release is legitimately incomplete while its delivery run is still going."""

    def test_a_freshly_published_release_is_pending_not_incomplete(self) -> None:
        """Publication starts the tag build; the assets arrive tens of minutes later.

        Alerting inside that window would be alerting on a release that is
        about to be fine — a guaranteed false positive on any release published
        shortly before the daily schedule.
        """
        fresh = release("v0.3.0", published_at="2026-09-01T09:50:00Z", assets=[], body="")
        report = build(fetching(fresh), now="2026-09-01T10:00:00Z")

        assert report["alert"] is False
        assert report["evaluated"] == []
        assert report["skipped_within_settle"] == [{"tag": "v0.3.0", "age_hours": 0.17}]

    def test_the_same_release_is_judged_once_the_window_elapses(self) -> None:
        """The negative twin: the settle window delays the verdict, it never cancels it."""
        fresh = release("v0.3.0", published_at="2026-09-01T09:50:00Z", assets=[], body="")
        report = build(fetching(fresh), now="2026-09-01T16:00:00Z")

        assert report["alert"] is True
        assert report["skipped_within_settle"] == []
        assert entry_for(report, "v0.3.0")["missing_assets"] == checker.expected_assets("v0.3.0")


# --------------------------------------------------------------------------- #
# What is held to the contract.
# --------------------------------------------------------------------------- #


class TestWhatIsJudged:
    """Only a published, non-prerelease release carries the asset promise."""

    def test_a_draft_is_not_judged(self) -> None:
        """A draft has no tag and no public asset URLs; nothing was promised yet."""
        report = build(
            fetching(
                release("v0.4.0", draft=True, published_at=None, assets=[]),
                complete_release("v0.3.0", published_at="2026-09-01T12:00:00Z"),
            ),
            now="2026-09-02T10:00:00Z",
        )

        assert [entry["tag"] for entry in report["evaluated"]] == ["v0.3.0"]
        assert report["alert"] is False

    def test_a_prerelease_is_not_judged(self) -> None:
        """A prerelease is not what the documented install instructions point at."""
        report = build(
            fetching(
                release("v0.4.0-rc.1", prerelease=True, published_at="2026-09-05T12:00:00Z", assets=[]),
                complete_release("v0.3.0", published_at="2026-09-01T12:00:00Z"),
            ),
            now="2026-09-06T10:00:00Z",
        )

        assert [entry["tag"] for entry in report["evaluated"]] == ["v0.3.0"]
        assert report["alert"] is False

    def test_the_expected_asset_names_are_derived_from_the_tag(self) -> None:
        """Every versioned name follows `VERSION_NUM="${VERSION#v}"`, as the workflows do."""
        assert checker.expected_assets("v1.2.3") == [
            "kamerplanter-1.2.3.tgz",
            "docker-compose-1.2.3.yml",
            "default.env.example-1.2.3",
            "openapi.json",
        ]

    def test_the_environment_file_is_expected_under_the_github_imposed_name(self) -> None:
        """GitHub stores `.env.example-<v>` as `default.env.example-<v>`.

        Measured against the live v0.0.23 and v0.0.24 assets. Expecting the
        UPLOADED name instead would make every complete release look broken —
        a check that alerts always is a check nobody reads.
        """
        assert "default.env.example-0.0.24" in checker.expected_assets("v0.0.24")
        assert ".env.example-0.0.24" not in checker.expected_assets("v0.0.24")

    def test_a_half_written_packages_block_does_not_count(self) -> None:
        """BEGIN without END renders as a broken section and delivers half the facts."""
        assert checker.has_packages_block(PACKAGES_BLOCK) is True
        assert checker.has_packages_block("<!-- kp:packages:begin -->\n## Packages") is False
        assert checker.has_packages_block("## Packages\n<!-- kp:packages:end -->") is False

    def test_a_missing_packages_block_alone_is_a_finding(self) -> None:
        """All four assets present, no block: still incomplete.

        The block is the only place a consumer is told where the images and the
        chart live, so its absence is a delivery loss in its own right — and it
        is the half of the loss an asset-only check would miss.
        """
        no_block = release(
            "v0.3.0",
            published_at="2026-09-01T12:00:00Z",
            assets=checker.expected_assets("v0.3.0"),
            body="## What's Changed\n\n## Packages\n",
        )
        report = build(fetching(no_block), now="2026-09-02T10:00:00Z")

        assert report["alert"] is True
        entry = entry_for(report, "v0.3.0")
        assert entry["missing_assets"] == []
        assert entry["packages_block_present"] is False


# --------------------------------------------------------------------------- #
# Fail-loud.
# --------------------------------------------------------------------------- #


class TestFailLoud:
    """NFR-018 §2: an undetermined check goes red and reports nothing.

    Every case here must raise. The companion assertion — that no report file is
    written, so the workflow's issue step cannot run — lives in
    :class:`TestMain`, because that is where the file is written.
    """

    def test_an_unreachable_api_raises(self) -> None:
        """A transport failure is not "assets complete"."""
        fetch = RecordingFetch({RELEASES_URL: checker.ReleaseAssetsError("GET … failed: <urlopen error>")})
        with pytest.raises(checker.ReleaseAssetsError, match="urlopen error"):
            build(fetch, now="2026-09-02T10:00:00Z")

    def test_an_unparseable_release_list_raises(self) -> None:
        """An object where an array belongs — a proxy or error page, typically."""
        fetch = RecordingFetch({RELEASES_URL: {"message": "Bad credentials"}})
        with pytest.raises(checker.ReleaseAssetsError, match="not a JSON array"):
            build(fetch, now="2026-09-02T10:00:00Z")

    def test_a_missing_assets_field_raises_rather_than_reading_as_no_assets(self) -> None:
        """The most dangerous shape: it would otherwise alert on every release.

        An API change that renamed or dropped `assets` would turn this check
        into a permanent false alarm. Undetermined is the honest verdict.
        """
        payload = release("v0.3.0", published_at="2026-09-01T12:00:00Z")
        del payload["assets"]
        with pytest.raises(checker.ReleaseAssetsError, match="no assets field"):
            build(fetching(payload), now="2026-09-02T10:00:00Z")

    def test_a_missing_body_field_raises(self) -> None:
        """Same reasoning for the packages block: absent field != absent block."""
        payload = release("v0.3.0", published_at="2026-09-01T12:00:00Z", assets=["openapi.json"])
        del payload["body"]
        with pytest.raises(checker.ReleaseAssetsError, match="no body field"):
            build(fetching(payload), now="2026-09-02T10:00:00Z")

    def test_a_null_body_is_an_absent_block_not_an_error(self) -> None:
        """GitHub sends `null` for an empty body — a real state, and a finding."""
        payload = release("v0.3.0", published_at="2026-09-01T12:00:00Z", assets=["openapi.json"])
        payload["body"] = None
        report = build(fetching(payload), now="2026-09-02T10:00:00Z")

        assert entry_for(report, "v0.3.0")["packages_block_present"] is False

    def test_an_asset_without_a_name_raises(self) -> None:
        """A nameless asset cannot be matched against the expected set."""
        payload = release("v0.3.0", published_at="2026-09-01T12:00:00Z")
        payload["assets"] = [{"size": 42}]
        with pytest.raises(checker.ReleaseAssetsError, match="has no name"):
            build(fetching(payload), now="2026-09-02T10:00:00Z")

    def test_a_release_without_a_tag_raises(self) -> None:
        """Without a tag there is no version and no expected asset set."""
        fetch = RecordingFetch({RELEASES_URL: [{"draft": False, "assets": [], "body": ""}]})
        with pytest.raises(checker.ReleaseAssetsError, match="no tag_name"):
            build(fetch, now="2026-09-02T10:00:00Z")

    def test_an_unparseable_publication_timestamp_raises(self) -> None:
        """Never guess a date: it moves both the floor and the settle window."""
        fetch = fetching(release("v0.3.0", published_at="last tuesday", assets=[]))
        with pytest.raises(checker.ReleaseAssetsError, match="unparseable timestamp"):
            build(fetch, now="2026-09-02T10:00:00Z")

    def test_a_tag_outside_the_v_convention_raises(self) -> None:
        """`docker-publish.yml` gates on `refs/tags/v*`; anything else is unknowable."""
        fetch = fetching(release("2026.09.01", published_at="2026-09-01T12:00:00Z", assets=[]))
        with pytest.raises(checker.ReleaseAssetsError, match="v<version> convention"):
            build(fetch, now="2026-09-02T10:00:00Z")

    def test_no_published_release_at_all_raises(self) -> None:
        """Only drafts: there is nothing to judge, so nothing is proven."""
        fetch = fetching(release("v0.3.0", draft=True, assets=[]))
        with pytest.raises(checker.ReleaseAssetsError, match="no published release"):
            build(fetch, now="2026-09-02T10:00:00Z")

    def test_an_empty_release_list_raises(self) -> None:
        """A repository with no releases cannot report a clean asset check."""
        fetch = fetching()
        with pytest.raises(checker.ReleaseAssetsError, match="no published release"):
            build(fetch, now="2026-09-02T10:00:00Z")


# --------------------------------------------------------------------------- #
# The entry point.
# --------------------------------------------------------------------------- #


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin every environment input main() reads, so the run is deterministic."""
    monkeypatch.setenv("GITHUB_REPOSITORY", REPOSITORY)
    monkeypatch.delenv("RELEASE_ASSETS_FLOOR", raising=False)
    monkeypatch.delenv("RELEASE_ASSETS_SETTLE_HOURS", raising=False)


@pytest.mark.usefixtures("clean_env")
class TestMain:
    """The report file is the workflow's contract: present iff determined."""

    def test_a_determined_run_writes_the_report_and_exits_zero(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The workflow's issue step keys off this file existing."""
        monkeypatch.setenv("RELEASE_ASSETS_FLOOR", FLOOR_BEFORE_THE_INCIDENT)
        target = tmp_path / "release-assets-report.json"

        exit_code = checker.main(
            [str(target)],
            fetch=fetching(MEASURED_V0_2_0, MEASURED_V0_1_0),
            now=at("2026-08-18T10:00:00Z"),
        )

        assert exit_code == 0
        report = json.loads(target.read_text(encoding="utf-8"))
        assert report["alert"] is True
        assert [entry["tag"] for entry in report["incomplete"]] == ["v0.2.0", "v0.1.0"]
        assert report["newest_published"]["tag"] == "v0.2.0"

    def test_an_undetermined_run_writes_no_report(self, tmp_path: Path) -> None:
        """Red run, no report, therefore no issue — and no tracker spam."""
        target = tmp_path / "release-assets-report.json"
        fetch = RecordingFetch({RELEASES_URL: checker.ReleaseAssetsError("GET … failed: HTTP 503")})

        with pytest.raises(checker.ReleaseAssetsError):
            checker.main([str(target)], fetch=fetch, now=at("2026-09-02T10:00:00Z"))

        assert not target.exists()

    def test_the_shipped_defaults_apply_when_the_environment_is_silent(self, tmp_path: Path) -> None:
        """No overrides set: the dated floor and the 6h settle window are in force."""
        target = tmp_path / "report.json"

        checker.main([str(target)], fetch=fetching(MEASURED_V0_2_0), now=at("2026-08-18T10:00:00Z"))

        report = json.loads(target.read_text(encoding="utf-8"))
        assert report["floor"] == "2026-08-18T00:00:00+00:00"
        assert report["settle_hours"] == 6.0
        assert report["skipped_below_floor"] == ["v0.2.0"]
        assert report["alert"] is False

    def test_the_floor_is_overridable_from_the_environment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`RELEASE_ASSETS_FLOOR` is what makes a dispatch able to judge history."""
        monkeypatch.setenv("RELEASE_ASSETS_FLOOR", FLOOR_BEFORE_THE_INCIDENT)
        target = tmp_path / "report.json"

        checker.main([str(target)], fetch=fetching(MEASURED_V0_2_0), now=at("2026-08-18T10:00:00Z"))

        report = json.loads(target.read_text(encoding="utf-8"))
        assert report["alert"] is True

    def test_an_unparseable_floor_override_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A typo in the workflow input must not fall back to the shipped floor."""
        monkeypatch.setenv("RELEASE_ASSETS_FLOOR", "yesterday")
        target = tmp_path / "report.json"

        with pytest.raises(checker.ReleaseAssetsError, match="RELEASE_ASSETS_FLOOR"):
            checker.main([str(target)], fetch=fetching(MEASURED_V0_2_0), now=at("2026-08-18T10:00:00Z"))

        assert not target.exists()

    def test_a_non_numeric_settle_window_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Same rule for the settle window: no silent fallback."""
        monkeypatch.setenv("RELEASE_ASSETS_SETTLE_HOURS", "six")
        target = tmp_path / "report.json"

        with pytest.raises(checker.ReleaseAssetsError, match="must be a number"):
            checker.main([str(target)], fetch=fetching(MEASURED_V0_2_0), now=at("2026-08-18T10:00:00Z"))

        assert not target.exists()

    def test_too_many_arguments_is_a_usage_error(self, tmp_path: Path) -> None:
        """Usage errors exit 2, distinct from both a clean run and a red one."""
        assert checker.main([str(tmp_path / "a.json"), str(tmp_path / "b.json")]) == 2

    def test_the_summary_names_the_floor_and_the_inertness(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """The job log must make the floor's cost visible without opening the JSON.

        A floor nobody can see is a threshold; a floor printed on every run is a
        decision. This is the assertion that keeps it printed.
        """
        checker.main([str(tmp_path / "report.json")], fetch=fetching(MEASURED_V0_2_0), now=at("2026-08-18T10:00:00Z"))
        out = capsys.readouterr().out

        assert "Floor: 2026-08-18T00:00:00+00:00" in out
        assert "Below the floor, not evaluated: v0.2.0" in out
        assert "INERT until the next release is published" in out

    def test_the_summary_names_every_missing_artefact(
        self, tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An alerting run must be readable straight off the job log."""
        monkeypatch.setenv("RELEASE_ASSETS_FLOOR", FLOOR_BEFORE_THE_INCIDENT)

        checker.main([str(tmp_path / "report.json")], fetch=fetching(MEASURED_V0_2_0), now=at("2026-08-18T10:00:00Z"))
        out = capsys.readouterr().out

        assert "INCOMPLETE v0.2.0" in out
        assert "kamerplanter-0.2.0.tgz" in out
        assert "docker-compose-0.2.0.yml" in out
        assert "default.env.example-0.2.0" in out
        assert "no packages block" in out
        assert "RELEASE ASSETS INCOMPLETE" in out


# --------------------------------------------------------------------------- #
# The alerting workflow's own decision — review finding F-5 on PR #1224.
# --------------------------------------------------------------------------- #

#: The workflow whose `actions/github-script` step acts on the report.
ALERT_WORKFLOW = ".github/workflows/release-assets-complete.yml"


def alert_script() -> str:
    """The ``actions/github-script`` body of the alerting workflow, as shipped.

    Read out of the workflow file rather than transcribed here: a copy would
    keep passing while the shipped script drifted away from it, which is the
    "test reaches the rule by a different path than production" failure this
    repository pays for repeatedly.
    """
    root = find_repo_root(Path(__file__).resolve())
    assert root is not None, "checkout root not found"
    document = yaml.safe_load((root / ALERT_WORKFLOW).read_text(encoding="utf-8"))
    scripts = [
        step["with"]["script"]
        for step in document["jobs"]["check-release-assets"]["steps"]
        if str(step.get("uses", "")).startswith("actions/github-script@")
    ]
    assert len(scripts) == 1, f"expected exactly one github-script step, found {len(scripts)}"
    return scripts[0]


#: Harness around the shipped script: the three objects `actions/github-script`
#: injects, faked, recording every call. The script body runs verbatim inside
#: the async wrapper — nothing about it is re-implemented here.
NODE_HARNESS = """
const fs = require('fs');
const calls = [];
const openIssues = JSON.parse(process.env.OPEN_ISSUES);
const github = {
  rest: {
    issues: {
      listForRepo: async () => ({ data: openIssues }),
      createComment: async (args) => { calls.push(['createComment', args]); },
      update: async (args) => { calls.push(['update', args]); },
      create: async (args) => { calls.push(['create', args]); return { data: { number: 4242 } }; },
    },
  },
};
const context = { repo: { owner: 'nolte', repo: 'kamerplanter' } };
const core = { notice: (message) => { calls.push(['notice', message]); } };

(async () => {
__BODY__
})().then(
  () => fs.writeFileSync('calls.json', JSON.stringify(calls)),
  (error) => { fs.writeFileSync('calls.json', JSON.stringify([['threw', String(error)]])); process.exit(3); },
);
"""


def run_alert_script(
    tmp_path: Path,
    report: dict[str, Any],
    *,
    open_issues: list[dict[str, Any]] | None = None,
) -> list[list[Any]]:
    """Execute the shipped script against *report* and return the calls it made.

    Node is what runs this script in production (`actions/github-script` is a
    Node action) and is present on every `ubuntu-latest` runner, which is where
    the backend suite runs. Asserting on the text of the script instead would
    pin its spelling, not its behaviour.
    """
    node = shutil.which("node")
    if node is None:  # pragma: no cover — only on a runner without Node
        pytest.skip("node is not on PATH; the shipped github-script body cannot be executed")

    body = "\n".join(f"  {line}" if line.strip() else line for line in alert_script().splitlines())
    (tmp_path / "harness.js").write_text(NODE_HARNESS.replace("__BODY__", body), encoding="utf-8")
    (tmp_path / "release-assets-report.json").write_text(json.dumps(report), encoding="utf-8")

    completed = subprocess.run(  # noqa: S603 — fixed argv, no shell, test-only
        [node, "harness.js"],
        cwd=tmp_path,
        # Inherited rather than replaced: a version-managed `node` shim needs
        # both HOME and its own PATH entries to resolve an interpreter at all.
        env={
            **os.environ,
            "RUN_URL": "https://github.com/nolte/kamerplanter/actions/runs/1",
            "OPEN_ISSUES": json.dumps(open_issues or []),
        },
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, f"node exited {completed.returncode}: {completed.stderr}"
    return json.loads((tmp_path / "calls.json").read_text(encoding="utf-8"))


#: An open alert issue as `listForRepo` returns it.
OPEN_ALERT = {"number": 77, "pull_request": None}


@pytest.mark.usefixtures("clean_env")
class TestNothingJudgedIsNotResolved:
    """The report tells "nothing was measured" apart from "measured clean".

    Review finding F-5 on PR #1224. The workflow closed its alert issue on
    ``!report.alert``, which is also true on every run that judged NOTHING — and
    a `workflow_dispatch` with a raised floor or a long `settle_hours` produces
    exactly that state at will. The comment it wrote said so in as many words
    ("nothing was judged") and closed the issue anyway, on a release that may
    still be genuinely incomplete. An undetermined state presenting itself as
    measured-clean is the class this whole PR exists to remove.
    """

    def test_a_run_that_judged_nothing_is_not_resolved(self) -> None:
        """Everything below the floor: no alert, and no resolution either."""
        report = build(fetching(MEASURED_V0_2_0, MEASURED_V0_1_0), now="2026-08-18T10:00:00Z")

        assert report["evaluated"] == []
        assert report["alert"] is False
        assert report["resolved"] is False

    def test_a_release_still_inside_the_settle_window_is_not_a_resolution_either(self) -> None:
        """The other way to judge nothing — and it is reachable from the dispatch input."""
        report = build(
            fetching(complete_release("v0.3.0", published_at="2026-09-02T09:00:00Z")),
            now="2026-09-02T10:00:00Z",
            settle_hours=6.0,
        )

        assert [entry["tag"] for entry in report["skipped_within_settle"]] == ["v0.3.0"]
        assert report["alert"] is False
        assert report["resolved"] is False

    def test_a_judged_complete_release_is_resolved(self) -> None:
        """The negative twin: a real measurement, and it does resolve."""
        report = build(
            fetching(complete_release("v0.3.0", published_at="2026-09-01T09:00:00Z")),
            now="2026-09-02T10:00:00Z",
        )

        assert [entry["tag"] for entry in report["evaluated"]] == ["v0.3.0"]
        assert report["alert"] is False
        assert report["resolved"] is True

    def test_an_incomplete_release_is_neither_resolved_nor_silent(self) -> None:
        report = build(
            fetching(MEASURED_V0_2_0),
            now="2026-08-18T10:00:00Z",
            floor=FLOOR_BEFORE_THE_INCIDENT,
        )

        assert report["alert"] is True
        assert report["resolved"] is False

    def test_the_written_report_carries_the_flag(self, tmp_path: Path) -> None:
        """The workflow reads the file, not the return value — so the file must carry it."""
        target = tmp_path / "report.json"

        checker.main([str(target)], fetch=fetching(MEASURED_V0_2_0), now=at("2026-08-18T10:00:00Z"))

        assert json.loads(target.read_text(encoding="utf-8"))["resolved"] is False


class TestTheAlertWorkflowActsOnTheMeasurement:
    """The shipped `actions/github-script` body, executed against real reports.

    The reports come from :func:`checker.build_report`, not from hand-written
    JSON: a fixture inventing a report shape the script will never see would
    certify nothing.
    """

    def _nothing_judged(self) -> dict[str, Any]:
        return build(fetching(MEASURED_V0_2_0, MEASURED_V0_1_0), now="2026-08-18T10:00:00Z")

    def _measured_clean(self) -> dict[str, Any]:
        return build(
            fetching(complete_release("v0.3.0", published_at="2026-09-01T09:00:00Z")),
            now="2026-09-02T10:00:00Z",
        )

    def _incomplete(self) -> dict[str, Any]:
        return build(fetching(MEASURED_V0_2_0), now="2026-08-18T10:00:00Z", floor=FLOOR_BEFORE_THE_INCIDENT)

    def test_an_open_alert_survives_a_run_that_judged_nothing(self, tmp_path: Path) -> None:
        """It commented "Resolved: … nothing was judged" and closed the issue before F-5."""
        calls = run_alert_script(tmp_path, self._nothing_judged(), open_issues=[OPEN_ALERT])

        assert [call[0] for call in calls] == ["notice"]
        assert "left OPEN" in calls[0][1]

    def test_a_run_that_judged_nothing_opens_nothing_either(self, tmp_path: Path) -> None:
        """Inertness is not a finding; it must not spawn an issue."""
        calls = run_alert_script(tmp_path, self._nothing_judged())

        assert [call[0] for call in calls] == ["notice"]

    def test_an_open_alert_is_closed_once_a_release_is_judged_clean(self, tmp_path: Path) -> None:
        """The other direction: a measured-clean run must still resolve the alert.

        Without this, "never close" would pass the test above and leave a
        permanently-open issue — the outcome the floor exists to avoid.
        """
        calls = run_alert_script(tmp_path, self._measured_clean(), open_issues=[OPEN_ALERT])

        kinds = [call[0] for call in calls]
        assert "createComment" in kinds
        closing = [call[1] for call in calls if call[0] == "update"]
        assert closing and closing[0]["state"] == "closed"
        assert closing[0]["issue_number"] == 77

    def test_an_incomplete_release_opens_the_alert(self, tmp_path: Path) -> None:
        """The alerting path itself, so the guard cannot have swallowed it."""
        calls = run_alert_script(tmp_path, self._incomplete())

        created = [call[1] for call in calls if call[0] == "create"]
        assert created, f"expected an issue to be created, got {[call[0] for call in calls]}"
        assert "v0.2.0" in created[0]["body"]
        assert created[0]["labels"] == ["release-assets-incomplete", "deployment"]

    def test_the_script_closes_on_the_resolution_flag_and_not_on_the_absent_alert(self) -> None:
        """A structural guard that runs even where Node does not.

        The Node tests above are the behavioural ones; this one holds the line on
        a machine without Node, where they skip. It pins the one relationship
        that matters: no ``state: 'closed'`` before the ``report.resolved`` gate.
        """
        script = alert_script()

        assert "report.resolved" in script
        gate = script.index("if (report.resolved)")
        closes = [index for index in range(len(script)) if script.startswith("state: 'closed'", index)]
        assert closes, "the script no longer closes the alert issue at all"
        assert all(index > gate for index in closes)
