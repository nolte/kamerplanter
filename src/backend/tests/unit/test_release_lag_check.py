"""Tests for the release-lag alarm (``scripts/ci/check_release_lag.py``).

**What is under test.** The verdict logic and the fail-loud contract, driven
against *constructed* API payloads. Both the HTTP layer and the clock are
injected, so nothing here touches the network, the GitHub API or a live git
repository — a test that asked the real API "is develop ahead?" would answer
something different every day and assert nothing.

**The falsification that matters** lives in :class:`TestTheIncident`: it replays
the real numbers of the 2026-08-16 incident (newest published release ``v0.2.0``
at 2026-08-13T18:09:49Z, ``develop`` carrying #1163's merge commit
``796c0047`` from 2026-08-14T20:50:49Z) and its counterfactual twin (the same
inputs with ``v0.2.1`` **published** rather than drafted). A check that would not
have caught the incident it exists for is worthless, so both directions are
pinned — including the uncomfortable one: with the **default** 3-day window the
alarm would not yet have fired at the moment of re-encounter. That is a measured
property of the window, and it is asserted rather than hidden behind a threshold
chosen to flatter the check.

**Why here.** ``pytest tests/unit/`` from ``src/backend`` is a CI check, and the
script lives outside the backend package (it runs on a bare runner with none of
this project's dependencies installed), so it is loaded by path through
``tests.support.repo_scripts``. It is not a backend test in subject; it is one in
placement, because this is the tier that runs.

Traces to issue #1210 (no TC-ID: a CI alarm is not a user-facing case).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("ci/check_release_lag")

REPOSITORY = "nolte/kamerplanter"
RELEASES_URL = f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100"


def compare_url(tag: str, head: str = "develop") -> str:
    """The compare URL the script is expected to request for *tag*."""
    return f"https://api.github.com/repos/{REPOSITORY}/compare/{tag}...{head}"


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
    created_at: str = "2026-08-13T17:54:59Z",
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
        "created_at": created_at,
        "html_url": f"https://github.com/{REPOSITORY}/releases/tag/{tag}",
    }


def commit(sha: str, *, date: str, message: str = "fix: something") -> dict[str, Any]:
    """One entry of the ``commits`` array of a compare response."""
    return {
        "sha": sha,
        "commit": {
            "message": message,
            "author": {"date": date},
            "committer": {"date": date},
        },
        "html_url": f"https://github.com/{REPOSITORY}/commit/{sha}",
    }


def comparison(*commits: dict[str, Any], ahead_by: int | None = None) -> dict[str, Any]:
    """A ``GET /repos/{repo}/compare/{base}...{head}`` response body."""
    return {
        "status": "ahead" if commits else "identical",
        "ahead_by": len(commits) if ahead_by is None else ahead_by,
        "behind_by": 0,
        "total_commits": len(commits),
        "commits": list(commits),
    }


class RecordingFetch:
    """A routing fake for the injected HTTP layer, recording every URL.

    Recording matters for one assertion in particular: that the *published*
    release, not the draft, is the tag the comparison is taken against. If the
    script asked about the draft, the requested URL would differ — and no
    assertion on the verdict alone would notice.
    """

    def __init__(self, routes: dict[str, Any]) -> None:
        self.routes = routes
        self.urls: list[str] = []

    def __call__(self, url: str) -> Any:
        self.urls.append(url)
        if url not in self.routes:
            # Mirrors api_json()'s HTTP-404 branch: an unresolvable tag.
            raise checker.ReleaseLagError(f"GET {url} failed: HTTP 404")
        value = self.routes[url]
        if isinstance(value, Exception):
            raise value
        return value


def build(fetch: Callable[[str], Any], *, now: str, threshold_days: int = 3) -> dict[str, Any]:
    """Call the script's report builder with the standard arguments."""
    return checker.build_report(
        fetch,
        repository=REPOSITORY,
        base_branch="develop",
        threshold_days=threshold_days,
        now=at(now),
    )


# --------------------------------------------------------------------------- #
# The incident (criterion 8) — both directions.
# --------------------------------------------------------------------------- #

#: The release list as `gh api repos/nolte/kamerplanter/releases` actually
#: returned it around the incident: v0.2.1 created as a DRAFT (published_at
#: null) *before* the fix merged, v0.2.0 the newest published release.
INCIDENT_RELEASES = [
    release("v0.2.1", draft=True, created_at="2026-08-13T21:26:23Z"),
    release("v0.2.0", published_at="2026-08-13T18:09:49Z", created_at="2026-08-13T17:54:59Z"),
    release("v0.1.0", published_at="2026-08-06T13:37:49Z", created_at="2026-08-06T10:14:38Z"),
]

#: PR #1163's merge commit on develop, with its real SHA and committer date.
INCIDENT_COMMIT = commit(
    "796c00474a137868e0f39fba978f09b6e9b83d78",
    date="2026-08-14T20:50:49Z",
    message=("fix(mcp): repair assign_nutrient_plan and get_mcp_activity, and the blind spots that hid them (#1163)"),
)

#: The moment the operator re-encountered the already-fixed bug.
RE_ENCOUNTER = "2026-08-16T12:00:00Z"


def incident_fetch(*, publish_v021: bool) -> RecordingFetch:
    """The incident's payloads, with ``v0.2.1`` drafted or published.

    The counterfactual is deliberately minimal: only ``v0.2.1``'s draft flag and
    publication timestamp change. Published, it is the newest delivery, its tag
    contains #1163's merge commit, and the comparison is empty.
    """
    releases = [
        (
            release("v0.2.1", published_at="2026-08-15T09:00:00Z", created_at="2026-08-13T21:26:23Z")
            if publish_v021
            else INCIDENT_RELEASES[0]
        ),
        *INCIDENT_RELEASES[1:],
    ]
    routes: dict[str, Any] = {RELEASES_URL: releases}
    if publish_v021:
        routes[compare_url("v0.2.1")] = comparison()
    else:
        routes[compare_url("v0.2.0")] = comparison(INCIDENT_COMMIT)
    return RecordingFetch(routes)


class TestTheIncident:
    """Replay of the 2026-08-16 incident, and its negative twin."""

    def test_the_draft_does_not_count_and_the_lag_is_measured_from_v0_2_0(self) -> None:
        """The comparison is taken against the newest PUBLISHED tag, not the draft.

        If a draft counted as a delivery, the script would compare against
        `v0.2.1` and find nothing — the exact misreading ("a release exists, so
        we are fine") the incident consisted of.
        """
        fetch = incident_fetch(publish_v021=False)
        report = build(fetch, now=RE_ENCOUNTER)

        assert compare_url("v0.2.0") in fetch.urls
        assert compare_url("v0.2.1") not in fetch.urls
        assert report["released"]["tag"] == "v0.2.0"
        assert report["released"]["published_at"] == "2026-08-13T18:09:49+00:00"
        assert report["unreleased_count"] == 1
        assert report["oldest_unreleased"]["sha"] == "796c00474a137868e0f39fba978f09b6e9b83d78"
        assert report["unpublished_draft"]["tag"] == "v0.2.1"

    def test_it_alerts_at_the_moment_of_re_encounter_under_a_one_day_window(self) -> None:
        """Criterion 8, positive direction: the incident yields the alert verdict.

        Evaluated as of the re-encounter, 2026-08-16T12:00Z, with a one-day
        window — which is the window under which "merged yesterday, still not
        delivered" is alertable at all.
        """
        report = build(incident_fetch(publish_v021=False), now=RE_ENCOUNTER, threshold_days=1)

        assert report["alert"] is True
        assert report["within_grace"] is False
        assert report["unreleased_count"] == 1
        assert report["oldest_unreleased"]["age_days"] == pytest.approx(1.63, abs=0.01)

    def test_the_default_window_had_not_elapsed_yet_at_the_moment_of_re_encounter(self) -> None:
        """The honest limit of the default 3-day window, pinned rather than hidden.

        #1163's merge commit was ~1.6 days old when the operator hit the bug
        again, so the default window had not elapsed. Asserting this is the point:
        it stops a later reader from believing the shipped default would have
        caught the incident in real time, and it makes any change to the default
        a deliberate, visible one.
        """
        report = build(incident_fetch(publish_v021=False), now=RE_ENCOUNTER, threshold_days=3)

        assert report["alert"] is False
        assert report["within_grace"] is True
        assert report["unreleased_count"] == 1

    def test_it_alerts_under_the_default_window_once_three_days_have_passed(self) -> None:
        """Same incident, same inputs, default window — red as soon as it elapses.

        2026-08-17T21:00Z is just past three days after the merge commit. Still a
        day and a half before anybody would plausibly have re-encountered the bug
        a second time.
        """
        report = build(incident_fetch(publish_v021=False), now="2026-08-17T21:00:00Z", threshold_days=3)

        assert report["alert"] is True
        assert report["oldest_unreleased"]["age_days"] == pytest.approx(3.01, abs=0.01)

    @pytest.mark.parametrize("threshold_days", [1, 3])
    def test_the_negative_twin_publishing_v0_2_1_clears_the_alert(self, threshold_days: int) -> None:
        """Criterion 8, negative direction: same inputs, `v0.2.1` published.

        The lag disappears because a published `v0.2.1` contains #1163's merge
        commit — proving the alert tracks *delivery*, not merely "develop moved".
        """
        fetch = incident_fetch(publish_v021=True)
        report = build(fetch, now=RE_ENCOUNTER, threshold_days=threshold_days)

        assert compare_url("v0.2.1") in fetch.urls
        assert report["released"]["tag"] == "v0.2.1"
        assert report["unpublished_draft"] is None
        assert report["unreleased_count"] == 0
        assert report["alert"] is False
        assert report["oldest_unreleased"] is None


# --------------------------------------------------------------------------- #
# Delivery selection.
# --------------------------------------------------------------------------- #


class TestWhatCountsAsADelivery:
    """Criterion 1: only a published, non-prerelease release is a delivery."""

    def test_a_prerelease_is_not_a_delivery(self) -> None:
        """A prerelease is published, but it is not what production tracks."""
        fetch = RecordingFetch(
            {
                RELEASES_URL: [
                    release("v0.3.0-rc.1", published_at="2026-08-15T10:00:00Z", prerelease=True),
                    release("v0.2.0", published_at="2026-08-13T18:09:49Z"),
                ],
                compare_url("v0.2.0"): comparison(commit("a" * 40, date="2026-08-14T00:00:00Z")),
            }
        )
        report = build(fetch, now="2026-08-20T00:00:00Z")

        assert report["released"]["tag"] == "v0.2.0"
        assert report["alert"] is True

    def test_the_newest_publication_wins_not_the_newest_creation(self) -> None:
        """Ordering is by `published_at`; a release created earlier can publish later."""
        fetch = RecordingFetch(
            {
                RELEASES_URL: [
                    release("v0.2.0", published_at="2026-08-13T18:09:49Z", created_at="2026-08-13T17:00:00Z"),
                    release("v0.1.9", published_at="2026-08-14T09:00:00Z", created_at="2026-08-01T09:00:00Z"),
                ],
                compare_url("v0.1.9"): comparison(),
            }
        )
        report = build(fetch, now="2026-08-20T00:00:00Z")

        assert report["released"]["tag"] == "v0.1.9"

    def test_the_draft_is_named_even_when_there_is_no_lag(self) -> None:
        """Criterion 4: the draft is reported unconditionally, not only on alert."""
        fetch = RecordingFetch(
            {
                RELEASES_URL: [
                    release("v0.3.0", draft=True, created_at="2026-08-19T08:00:00Z"),
                    release("v0.2.0", published_at="2026-08-13T18:09:49Z"),
                ],
                compare_url("v0.2.0"): comparison(),
            }
        )
        report = build(fetch, now="2026-08-20T00:00:00Z")

        assert report["alert"] is False
        assert report["unpublished_draft"]["tag"] == "v0.3.0"


# --------------------------------------------------------------------------- #
# The grace window.
# --------------------------------------------------------------------------- #


class TestGraceWindow:
    """Criteria 2 and 3: when the lag is alertable and when it is not."""

    def test_no_un_released_commits_is_no_alert(self) -> None:
        """Criterion 2: an empty set exits clean, with nothing to report."""
        fetch = RecordingFetch(
            {
                RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")],
                compare_url("v0.2.0"): comparison(),
            }
        )
        report = build(fetch, now="2026-08-20T00:00:00Z")

        assert report["unreleased_count"] == 0
        assert report["alert"] is False
        assert report["within_grace"] is False
        assert report["oldest_unreleased"] is None
        assert report["newest_unreleased"] is None

    def test_a_fresh_un_released_commit_is_within_grace(self) -> None:
        """Develop is ahead almost always; that alone must never alert."""
        fetch = RecordingFetch(
            {
                RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")],
                compare_url("v0.2.0"): comparison(commit("b" * 40, date="2026-08-19T12:00:00Z")),
            }
        )
        report = build(fetch, now="2026-08-20T00:00:00Z")

        assert report["unreleased_count"] == 1
        assert report["alert"] is False
        assert report["within_grace"] is True

    def test_the_oldest_commit_drives_the_verdict_not_the_newest(self) -> None:
        """A stale commit stays alertable however much fresh work lands on top of it."""
        fetch = RecordingFetch(
            {
                RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")],
                compare_url("v0.2.0"): comparison(
                    commit("c" * 40, date="2026-08-14T00:00:00Z", message="the stale one"),
                    commit("d" * 40, date="2026-08-19T23:00:00Z", message="landed minutes ago"),
                ),
            }
        )
        report = build(fetch, now="2026-08-20T00:00:00Z")

        assert report["alert"] is True
        assert report["oldest_unreleased"]["sha"] == "c" * 40
        assert report["oldest_unreleased"]["headline"] == "the stale one"
        assert report["newest_unreleased"]["sha"] == "d" * 40
        assert report["unreleased_count"] == 2

    def test_the_boundary_is_inclusive(self) -> None:
        """Exactly `threshold_days` old alerts; a minute younger does not."""
        releases = [release("v0.2.0", published_at="2026-08-13T18:09:49Z")]
        on_boundary = RecordingFetch(
            {
                RELEASES_URL: releases,
                compare_url("v0.2.0"): comparison(commit("e" * 40, date="2026-08-17T00:00:00Z")),
            }
        )
        just_inside = RecordingFetch(
            {
                RELEASES_URL: releases,
                compare_url("v0.2.0"): comparison(commit("e" * 40, date="2026-08-17T00:01:00Z")),
            }
        )

        assert build(on_boundary, now="2026-08-20T00:00:00Z")["alert"] is True
        assert build(just_inside, now="2026-08-20T00:00:00Z")["alert"] is False

    def test_a_truncated_commit_array_still_yields_the_oldest_commit(self) -> None:
        """Compare caps `commits` at 250 while `ahead_by` stays exact.

        The array is oldest-first, so truncation removes the *newest* entries and
        the age clock is unaffected; the count comes from `ahead_by`.
        """
        fetch = RecordingFetch(
            {
                RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")],
                compare_url("v0.2.0"): comparison(
                    commit("f" * 40, date="2026-08-14T00:00:00Z"),
                    ahead_by=312,
                ),
            }
        )
        report = build(fetch, now="2026-08-20T00:00:00Z")

        assert report["unreleased_count"] == 312
        assert report["oldest_unreleased"]["sha"] == "f" * 40
        assert report["alert"] is True

    def test_a_truncated_commit_array_reports_no_newest_commit(self) -> None:
        """Past the 250-commit cap the newest entry is unknowable — say so.

        The array is oldest-first, so truncation removes exactly the entries a
        naive ``commits[-1]`` would call "newest". Reporting the 250th commit
        under that label produces an alert that reads correct and is not, with
        nothing in the rendering to reveal the substitution. `ahead_by` exceeding
        the array length is the detectable signal, and the honest answer is None.
        """
        fetch = RecordingFetch(
            {
                RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")],
                compare_url("v0.2.0"): comparison(
                    commit("f" * 40, date="2026-08-14T00:00:00Z"),
                    commit("e" * 40, date="2026-08-15T00:00:00Z"),
                    ahead_by=312,
                ),
            }
        )
        report = build(fetch, now="2026-08-20T00:00:00Z")

        assert report["newest_unreleased"] is None
        # The oldest — which drives the age clock and the alert — survives the cap.
        assert report["oldest_unreleased"]["sha"] == "f" * 40
        assert report["alert"] is True

    def test_an_untruncated_comparison_still_reports_its_newest_commit(self) -> None:
        """The guard must not cost the ordinary case its answer.

        Twin of the test above: with `ahead_by` matching the array length nothing
        was dropped, so the newest entry is genuine and must still be reported.
        Without this, silencing `newest_unreleased` unconditionally would pass.
        """
        fetch = RecordingFetch(
            {
                RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")],
                compare_url("v0.2.0"): comparison(
                    commit("f" * 40, date="2026-08-14T00:00:00Z"),
                    commit("e" * 40, date="2026-08-15T00:00:00Z"),
                    ahead_by=2,
                ),
            }
        )
        report = build(fetch, now="2026-08-20T00:00:00Z")

        assert report["newest_unreleased"]["sha"] == "e" * 40
        assert report["oldest_unreleased"]["sha"] == "f" * 40


# --------------------------------------------------------------------------- #
# Fail-loud (criterion 5).
# --------------------------------------------------------------------------- #


class TestFailLoud:
    """NFR-018 §2: an undetermined check goes red and reports nothing.

    Every case here must raise. The companion assertion — that no report file is
    written, so the workflow's issue step cannot run — lives in
    :class:`TestMain`, because that is where the file is written.
    """

    def test_an_unreachable_api_raises(self) -> None:
        """A transport failure is not "no lag"."""
        fetch = RecordingFetch({RELEASES_URL: checker.ReleaseLagError("GET … failed: <urlopen error>")})
        with pytest.raises(checker.ReleaseLagError, match="urlopen error"):
            build(fetch, now="2026-08-20T00:00:00Z")

    def test_an_unparseable_release_list_raises(self) -> None:
        """An object where an array belongs — a proxy or error page, typically."""
        fetch = RecordingFetch({RELEASES_URL: {"message": "Bad credentials"}})
        with pytest.raises(checker.ReleaseLagError, match="not a JSON array"):
            build(fetch, now="2026-08-20T00:00:00Z")

    def test_a_release_without_a_tag_raises(self) -> None:
        """A release object we cannot compare against is undetermined, not clean."""
        fetch = RecordingFetch({RELEASES_URL: [{"draft": False, "published_at": "2026-08-13T18:09:49Z"}]})
        with pytest.raises(checker.ReleaseLagError, match="no tag_name"):
            build(fetch, now="2026-08-20T00:00:00Z")

    def test_an_unparseable_publication_timestamp_raises(self) -> None:
        """Never fall back to a guessed date: the age is the whole verdict."""
        fetch = RecordingFetch({RELEASES_URL: [release("v0.2.0", published_at="last tuesday")]})
        with pytest.raises(checker.ReleaseLagError, match="unparseable timestamp"):
            build(fetch, now="2026-08-20T00:00:00Z")

    def test_no_published_release_at_all_raises(self) -> None:
        """Only drafts: there is nothing to compare against, so nothing is proven."""
        fetch = RecordingFetch({RELEASES_URL: [release("v0.2.1", draft=True)]})
        with pytest.raises(checker.ReleaseLagError, match="no published release"):
            build(fetch, now="2026-08-20T00:00:00Z")

    def test_an_empty_release_list_raises(self) -> None:
        """A repository with no releases cannot report a clean lag check."""
        fetch = RecordingFetch({RELEASES_URL: []})
        with pytest.raises(checker.ReleaseLagError, match="no published release"):
            build(fetch, now="2026-08-20T00:00:00Z")

    def test_a_tag_that_cannot_be_resolved_raises(self) -> None:
        """The compare endpoint 404s when the tag is not a ref — e.g. a deleted tag."""
        fetch = RecordingFetch({RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")]})
        with pytest.raises(checker.ReleaseLagError, match="HTTP 404"):
            build(fetch, now="2026-08-20T00:00:00Z")

    def test_a_comparison_without_ahead_by_raises(self) -> None:
        """Missing the count means we cannot say whether the set is empty."""
        fetch = RecordingFetch(
            {
                RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")],
                compare_url("v0.2.0"): {"commits": []},
            }
        )
        with pytest.raises(checker.ReleaseLagError, match="no integer ahead_by"):
            build(fetch, now="2026-08-20T00:00:00Z")

    def test_a_comparison_claiming_commits_it_does_not_carry_raises(self) -> None:
        """`ahead_by > 0` with an empty array leaves the age clock unreadable."""
        fetch = RecordingFetch(
            {
                RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")],
                compare_url("v0.2.0"): {"ahead_by": 4, "commits": []},
            }
        )
        with pytest.raises(checker.ReleaseLagError, match="could not be resolved"):
            build(fetch, now="2026-08-20T00:00:00Z")

    def test_a_commit_without_a_date_raises(self) -> None:
        """No date, no age, no verdict."""
        fetch = RecordingFetch(
            {
                RELEASES_URL: [release("v0.2.0", published_at="2026-08-13T18:09:49Z")],
                compare_url("v0.2.0"): {
                    "ahead_by": 1,
                    "commits": [{"sha": "a" * 40, "commit": {"message": "x"}}],
                },
            }
        )
        with pytest.raises(checker.ReleaseLagError, match="no dated committer/author"):
            build(fetch, now="2026-08-20T00:00:00Z")


# --------------------------------------------------------------------------- #
# The entry point.
# --------------------------------------------------------------------------- #


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin every environment input main() reads, so the run is deterministic."""
    monkeypatch.setenv("GITHUB_REPOSITORY", REPOSITORY)
    monkeypatch.setenv("RELEASE_LAG_BASE_BRANCH", "develop")
    monkeypatch.delenv("RELEASE_LAG_THRESHOLD_DAYS", raising=False)


@pytest.mark.usefixtures("clean_env")
class TestMain:
    """The report file is the workflow's contract: present iff determined."""

    def test_a_determined_run_writes_the_report_and_exits_zero(self, tmp_path: Path) -> None:
        """The workflow's issue step keys off this file existing."""
        target = tmp_path / "release-lag-report.json"
        exit_code = checker.main(
            [str(target)],
            fetch=incident_fetch(publish_v021=False),
            now=at("2026-08-17T21:00:00Z"),
        )

        assert exit_code == 0
        report = json.loads(target.read_text(encoding="utf-8"))
        assert report["alert"] is True
        assert report["released"]["tag"] == "v0.2.0"
        assert report["unpublished_draft"]["tag"] == "v0.2.1"
        assert report["threshold_days"] == 3

    def test_an_undetermined_run_writes_no_report(self, tmp_path: Path) -> None:
        """Criterion 5: red run, no report, therefore no issue."""
        target = tmp_path / "release-lag-report.json"
        fetch = RecordingFetch({RELEASES_URL: checker.ReleaseLagError("GET … failed: HTTP 503")})

        with pytest.raises(checker.ReleaseLagError):
            checker.main([str(target)], fetch=fetch, now=at("2026-08-20T00:00:00Z"))

        assert not target.exists()

    def test_the_threshold_is_read_from_the_environment(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """`RELEASE_LAG_THRESHOLD_DAYS` tightens the window the workflow passes in."""
        monkeypatch.setenv("RELEASE_LAG_THRESHOLD_DAYS", "1")
        target = tmp_path / "release-lag-report.json"

        checker.main([str(target)], fetch=incident_fetch(publish_v021=False), now=at(RE_ENCOUNTER))

        report = json.loads(target.read_text(encoding="utf-8"))
        assert report["threshold_days"] == 1
        assert report["alert"] is True

    def test_a_non_integer_threshold_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A typo in the workflow input must not silently fall back to the default."""
        monkeypatch.setenv("RELEASE_LAG_THRESHOLD_DAYS", "three")
        target = tmp_path / "release-lag-report.json"

        with pytest.raises(checker.ReleaseLagError, match="must be an integer"):
            checker.main([str(target)], fetch=incident_fetch(publish_v021=False), now=at(RE_ENCOUNTER))

        assert not target.exists()

    def test_too_many_arguments_is_a_usage_error(self, tmp_path: Path) -> None:
        """Usage errors exit 2, distinct from both a clean run and a red one."""
        assert checker.main([str(tmp_path / "a.json"), str(tmp_path / "b.json")]) == 2

    def test_the_summary_names_the_draft_and_the_lag(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        """The job log must be readable without opening the JSON."""
        checker.main(
            [str(tmp_path / "report.json")],
            fetch=incident_fetch(publish_v021=False),
            now=at("2026-08-17T21:00:00Z"),
        )
        out = capsys.readouterr().out

        assert "v0.2.0" in out
        assert "Unpublished draft present: v0.2.1" in out
        assert "RELEASE LAG" in out
