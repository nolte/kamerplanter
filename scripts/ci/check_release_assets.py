#!/usr/bin/env python3
"""Alert when a PUBLISHED release does not carry the artefacts it promises.

Issue #1218. This checks the **outcome**, not the run. Its sibling observers
watch processes — `release-lag.yml` watches "has a release been published",
`delivery-run-alert.yml` watches "did the delivery run go red". Neither of them
could have caught what actually happened here, and the difference is the whole
reason this file exists.

THE INCIDENT THIS EXISTS FOR
----------------------------
`publish-helm-charts` in `.github/workflows/docker-publish.yml` has failed on
every release since 2026-08-01, when commit `3054b7d96` (#886) added an
`Attest chart provenance` step whose action reads `~/.docker/config.json` while
that job only ever writes Helm's own credential store. The chart asset was lost
inside that job — and then `update-release-assets`, which declares
`needs: [... publish-helm-charts]` under `!contains(needs.*.result, 'failure')`,
was **SKIPPED**. Not failed. Skipped.

A skipped job reports success. That is this repository's most expensive
recurring failure class, and it is precisely the shape a failure-watcher cannot
see: nothing was red about `update-release-assets`, it simply never ran, and the
only place the loss is visible is the release page itself.

MEASURED, 2026-08-18 (`gh release view <tag> --json assets`)
------------------------------------------------------------
    v0.0.23  default.env.example-0.0.23, docker-compose-0.0.23.yml,
             kamerplanter-0.0.23.tgz
    v0.0.24  the same three, plus openapi.json
    v0.1.0   openapi.json ONLY          <- the regression starts here
    v0.2.0   openapi.json ONLY

Three assets plus the release-notes Packages block, gone, for two consecutive
published releases, for seventeen days. `gh release view v0.2.0 --json body`
contains no `<!-- kp:packages:begin -->` marker either.

WHAT IS EXPECTED, AND WHERE EACH EXPECTATION COMES FROM
-------------------------------------------------------
Every name below is read off the producing workflow, not guessed:

    kamerplanter-<version>.tgz     docker-publish.yml, job `publish-helm-charts`,
                                   step `Upload chart as release asset`
                                   (`helm package` names the archive
                                   `<chart>-<version>.tgz`).
    docker-compose-<version>.yml   docker-publish.yml, job `update-release-assets`,
                                   step `Generate and upload docker-compose`.
    default.env.example-<version>  the same step, which uploads a file named
                                   `.env.example-<version>`. GitHub refuses a
                                   leading dot in an asset name and stores it as
                                   `default.env.example-<version>` — verified
                                   against the live v0.0.23 and v0.0.24 assets.
                                   The STORED name is what this check compares,
                                   because the stored name is what a consumer
                                   downloads.
    openapi.json                   release-publish.yml, step `Upload OpenAPI
                                   document to the draft release`. A DIFFERENT
                                   workflow, which is why it survived the
                                   incident and why it stays in the expected
                                   set: its own absence is a real loss with a
                                   different cause. Its name is deliberately
                                   unversioned so that
                                   `releases/latest/download/openapi.json`
                                   stays a permalink.
    <!-- kp:packages:begin -->     docker-publish.yml, job `update-release-assets`,
                                   step `Update release body with package links`.
                                   The marker pair delimits the block naming every
                                   image, the chart pull command and the
                                   `gh attestation verify` instructions.

That marker pair was introduced by the SAME commit that broke the chart job
(`3054b7d96`, #886, 2026-08-01). Releases older than that carry a `## Packages`
heading with no markers around it — v0.0.24 is such a release. They are not a
counter-example to this check, they are simply from before the mechanism it
measures; the floor below keeps every evaluated release inside the marker era.

THE FLOOR — A DELIBERATE, DATED DECISION (issue #1218, Q4)
-----------------------------------------------------------
`v0.1.0` and `v0.2.0` are broken **now**, and the recorded operator decision is
to fix forward and NOT to retro-fit assets onto published releases. An unfloored
check would therefore open an alert on its very first run and keep it open until
the next release — a permanently-open issue, which trains every reader to ignore
the label. That is worse than no check at all, so:

    only releases published AT OR AFTER RELEASE_ASSETS_FLOOR are evaluated.

The floor is 2026-08-18, the day #1218's fix strand was written. It is a
timestamp rather than a tag on purpose: a tag floor needs version comparison and
an edit at every release, while a date is a single constant that never needs
touching again and reads as "this check started here".

THE COST OF THE FLOOR, STATED OUT LOUD: this check is INERT until the next
release is published. It cannot alert on anything that exists today. That is not
a bug and it is not a silent skip — every run prints which releases it declined
to evaluate and why, the report carries them under `skipped_below_floor`, and
the alert body repeats the floor and its date. A floor nobody can see is a
threshold; a floor printed on every run is a decision.

THE SETTLE WINDOW
-----------------
A release is published by `release-publish.yml`, which pushes the tag; the tag
push then starts `docker-publish.yml`, whose eight image builds must finish
before `update-release-assets` runs at all. So a release is legitimately
incomplete for tens of minutes after it is published, and a daily check that
happened to run inside that window would alert on a release that was about to be
fine. Releases younger than RELEASE_ASSETS_SETTLE_HOURS (default 6) are
therefore reported as pending rather than judged — generously past the observed
pipeline duration, and still far inside "alerted the same day".

WHY EVERY RELEASE SINCE THE FLOOR, NOT JUST THE NEWEST
-------------------------------------------------------
Checking only the newest published release would let a broken one be forgotten
the moment a good one follows it: the alert would close and the hole would stay.
The incident is exactly that shape — TWO consecutive broken releases — so the
check evaluates every settled release at or after the floor and names all of
them. It costs nothing: the whole check is one API call, because the release
list endpoint already carries each release's assets and body.

FAIL LOUD (NFR-018 section 2)
-----------------------------
An unreachable API, an unparseable release list, a release object without an
assets array, or a tag this repository's naming cannot turn into a version is
NOT "assets complete". It raises, main() prints ``::error::`` and exits non-zero
WITHOUT writing the report — the run goes red and opens NO issue. An undetermined
check must never read as a clean one, and a transient API blip must not spam the
tracker.

Traces to issue #1218 (no TC-ID: a CI alarm is not a user-facing case).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

API_ROOT = "https://api.github.com"

#: Written only on a DETERMINED result; the workflow's issue step keys off its
#: existence, so an undetermined run leaves it absent and opens nothing.
REPORT_PATH = "release-assets-report.json"

DEFAULT_REPOSITORY = "nolte/kamerplanter"

#: The single chart in `publish-helm-charts`'s matrix. `helm package` names the
#: archive `<chart>-<version>.tgz`, which is uploaded under that name verbatim.
CHART_NAME = "kamerplanter"

#: See "THE FLOOR" in the module docstring. Changing this is a decision about
#: which published releases this project is willing to be held to; make it
#: deliberately, and move the date forward only with a reason recorded here.
DEFAULT_FLOOR = "2026-08-18T00:00:00Z"

#: See "THE SETTLE WINDOW" in the module docstring.
DEFAULT_SETTLE_HOURS = "6"

#: Delimiters written by `update-release-assets`'s `Update release body with
#: package links` step. Both are required: a body carrying BEGIN without END is
#: a half-written block, which renders broken and delivers only half the
#: information it exists to carry.
PACKAGES_BLOCK_BEGIN = "<!-- kp:packages:begin -->"
PACKAGES_BLOCK_END = "<!-- kp:packages:end -->"

#: One page covers this repository's whole release history (~27 releases) and
#: keeps the check to a single API call. If the floor is ever moved so far back
#: that it predates the oldest release on the page, releases between the two
#: become invisible here — we fail loud rather than page on, because silently
#: evaluating a truncated history is how a check starts certifying nothing.
RELEASE_PAGE_SIZE = 100

HTTP_TIMEOUT_SECONDS = 30

SECONDS_PER_HOUR = 3600.0


class ReleaseAssetsError(RuntimeError):
    """A condition under which the check could not be determined — fail loud."""


@dataclass(frozen=True)
class Release:
    """One GitHub release object, reduced to what completeness turns on."""

    tag: str
    name: str
    draft: bool
    prerelease: bool
    published_at: datetime | None
    url: str
    assets: tuple[str, ...]
    body: str

    @property
    def is_publication(self) -> bool:
        """Whether this release is one a consumer can actually download from.

        A draft has no tag and no public asset URLs; a prerelease is not what
        this project's documented install instructions point at. Neither is held
        to the asset contract.
        """
        return not self.draft and not self.prerelease and self.published_at is not None


def parse_timestamp(value: Any, *, context: str) -> datetime:
    """Parse an ISO-8601 GitHub timestamp into an aware UTC datetime.

    Args:
        value: The raw field value.
        context: What is being parsed, for the error message.

    Returns:
        A timezone-aware datetime.

    Raises:
        ReleaseAssetsError: The value is absent or unparseable. Never a fallback
            to "now" or "epoch" — a guessed timestamp moves both the floor
            comparison and the settle window this check turns on.
    """
    if not isinstance(value, str) or not value:
        raise ReleaseAssetsError(f"{context}: missing timestamp (got {value!r})")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReleaseAssetsError(f"{context}: unparseable timestamp {value!r}: {exc}") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_assets(payload: Any, *, tag: str) -> tuple[str, ...]:
    """Extract the asset names out of one release payload.

    Args:
        payload: The release object's ``assets`` value.
        tag: The owning release's tag, for error messages.

    Returns:
        The asset names in payload order. An empty tuple is a legitimate answer
        — it is very nearly the state v0.1.0 and v0.2.0 are in.

    Raises:
        ReleaseAssetsError: ``assets`` is not a list of named objects. "The
            payload did not tell us the assets" is not "there are none".
    """
    if not isinstance(payload, list):
        raise ReleaseAssetsError(f"release {tag}: assets is not a JSON array (got {type(payload).__name__})")
    names: list[str] = []
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            raise ReleaseAssetsError(f"release {tag}: asset[{index}] is not an object")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise ReleaseAssetsError(f"release {tag}: asset[{index}] has no name")
        names.append(name)
    return tuple(names)


def parse_release(entry: Any, *, index: int) -> Release:
    """Turn one entry of the ``/releases`` array into a :class:`Release`.

    Raises:
        ReleaseAssetsError: The entry is not a release object, or lacks a field
            the verdict depends on. ``assets`` and ``body`` are required KEYS —
            a payload that omits them is not a release object, and reading a
            missing ``assets`` as "no assets" would turn an API shape change
            into a permanent false alert.
    """
    if not isinstance(entry, dict):
        raise ReleaseAssetsError(f"release[{index}] is not an object (got {type(entry).__name__})")
    tag = entry.get("tag_name")
    if not isinstance(tag, str) or not tag:
        raise ReleaseAssetsError(f"release[{index}] has no tag_name")
    if "assets" not in entry:
        raise ReleaseAssetsError(f"release {tag}: payload carries no assets field")
    if "body" not in entry:
        raise ReleaseAssetsError(f"release {tag}: payload carries no body field")

    published_raw = entry.get("published_at")
    body = entry.get("body")
    return Release(
        tag=tag,
        name=str(entry.get("name") or tag),
        draft=bool(entry.get("draft")),
        prerelease=bool(entry.get("prerelease")),
        published_at=(
            parse_timestamp(published_raw, context=f"release {tag} published_at")
            if published_raw is not None
            else None
        ),
        url=str(entry.get("html_url") or ""),
        assets=parse_assets(entry["assets"], tag=tag),
        # GitHub sends `null` for an empty body. That is a real state, and it
        # means the packages block is absent — a finding, not an error.
        body=body if isinstance(body, str) else "",
    )


def parse_releases(payload: Any) -> list[Release]:
    """Turn the ``/releases`` payload into :class:`Release` objects.

    Args:
        payload: The decoded JSON body.

    Returns:
        Every release on the page, drafts and prereleases included; the caller
        filters.

    Raises:
        ReleaseAssetsError: The payload is not a list of release objects.
    """
    if not isinstance(payload, list):
        raise ReleaseAssetsError(f"release list is not a JSON array (got {type(payload).__name__})")
    return [parse_release(entry, index=index) for index, entry in enumerate(payload)]


def release_version(tag: str) -> str:
    """Strip this project's ``v`` prefix off a release tag.

    Every expected asset name but ``openapi.json`` embeds the version, and every
    producing workflow derives it the same way (``VERSION_NUM="${VERSION#v}"``).

    Raises:
        ReleaseAssetsError: The tag is not ``v<something>``. `docker-publish.yml`
            gates its release steps on ``refs/tags/v*``, so a tag outside that
            shape produces no assets by design and the expected set is
            unknowable — undetermined, not clean.
    """
    if not tag.startswith("v") or len(tag) <= 1:
        raise ReleaseAssetsError(
            f"release tag {tag!r} does not match this project's v<version> convention — "
            "the expected asset names cannot be derived from it"
        )
    return tag[1:]


def expected_assets(tag: str) -> list[str]:
    """The asset names a complete release of *tag* carries.

    See "WHAT IS EXPECTED" in the module docstring for the producing workflow of
    each entry — in particular why the environment file is expected under the
    ``default.`` prefix GitHub imposes on a leading-dot filename.
    """
    version = release_version(tag)
    return [
        f"{CHART_NAME}-{version}.tgz",
        f"docker-compose-{version}.yml",
        f"default.env.example-{version}",
        "openapi.json",
    ]


def has_packages_block(body: str) -> bool:
    """Whether the release body carries a complete package-links block."""
    return PACKAGES_BLOCK_BEGIN in body and PACKAGES_BLOCK_END in body


def _hours_between(later: datetime, earlier: datetime) -> float:
    return (later - earlier).total_seconds() / SECONDS_PER_HOUR


def evaluate_release(release: Release, *, now: datetime) -> dict[str, Any]:
    """Judge one published release against the expected artefact set.

    Args:
        release: A publication (``is_publication`` is True).
        now: Evaluation instant, timezone-aware.

    Returns:
        A JSON-serialisable entry; ``complete`` is the per-release verdict.

    Raises:
        ReleaseAssetsError: The tag cannot be turned into a version.
    """
    expected = expected_assets(release.tag)
    present = set(release.assets)
    missing = [name for name in expected if name not in present]
    packages_block = has_packages_block(release.body)
    published_at = release.published_at
    return {
        "tag": release.tag,
        "name": release.name,
        "url": release.url,
        "published_at": published_at.isoformat() if published_at else None,
        "age_hours": round(_hours_between(now, published_at), 2) if published_at else None,
        "expected_assets": expected,
        "present_assets": list(release.assets),
        "missing_assets": missing,
        "packages_block_present": packages_block,
        "complete": not missing and packages_block,
    }


def build_report(
    fetch: Callable[[str], Any],
    *,
    repository: str,
    floor: datetime,
    settle_hours: float,
    now: datetime,
) -> dict[str, Any]:
    """Measure release completeness and return the report the workflow acts on.

    Args:
        fetch: Returns the decoded JSON body for a URL, or raises
            :class:`ReleaseAssetsError`. Injected so the tests need no network.
        repository: ``owner/name``.
        floor: Releases published before this instant are not evaluated.
        settle_hours: Releases younger than this are pending, not judged.
        now: Evaluation instant, timezone-aware.

    Returns:
        A JSON-serialisable report; ``alert`` is the single verdict the workflow
        keys off.

    Raises:
        ReleaseAssetsError: Anything that leaves the answer undetermined.
    """
    releases = parse_releases(fetch(f"{API_ROOT}/repos/{repository}/releases?per_page={RELEASE_PAGE_SIZE}"))
    publications = [release for release in releases if release.is_publication]
    if not publications:
        raise ReleaseAssetsError(
            f"no published release among the {len(releases)} most recent release object(s) "
            "— refusing to report a clean release-asset check against nothing"
        )

    # published_at is non-None for every publication by construction.
    epoch = datetime.min.replace(tzinfo=timezone.utc)
    ordered = sorted(publications, key=lambda release: release.published_at or epoch, reverse=True)
    newest = ordered[0]

    # The page is a fixed window into the release history. A floor predating the
    # oldest release we can see means releases between the two are invisible to
    # this check, which would then silently under-report. Say so instead.
    oldest_seen = ordered[-1].published_at or epoch
    if len(releases) >= RELEASE_PAGE_SIZE and floor < oldest_seen:
        raise ReleaseAssetsError(
            f"the floor {floor.isoformat()} predates the oldest release on the first page "
            f"({ordered[-1].tag}, {oldest_seen.isoformat()}) — the release history is truncated "
            "and the check would silently under-report"
        )

    evaluated: list[dict[str, Any]] = []
    below_floor: list[str] = []
    pending: list[dict[str, Any]] = []
    for release in ordered:
        published_at = release.published_at or epoch
        if published_at < floor:
            below_floor.append(release.tag)
            continue
        age_hours = _hours_between(now, published_at)
        if age_hours < settle_hours:
            pending.append({"tag": release.tag, "age_hours": round(age_hours, 2)})
            continue
        evaluated.append(evaluate_release(release, now=now))

    incomplete = [entry for entry in evaluated if not entry["complete"]]
    newest_published_at = newest.published_at
    return {
        "repository": repository,
        "evaluated_at": now.isoformat(),
        "floor": floor.isoformat(),
        "settle_hours": settle_hours,
        "newest_published": {
            "tag": newest.tag,
            "published_at": newest_published_at.isoformat() if newest_published_at else None,
            "url": newest.url,
        },
        "evaluated": evaluated,
        "incomplete": incomplete,
        # Named, never silently dropped: the floor is a decision, so every run
        # must show which releases it declined to judge because of it.
        "skipped_below_floor": below_floor,
        "skipped_within_settle": pending,
        "alert": bool(incomplete),
    }


def api_json(url: str) -> Any:
    """GET *url* from the GitHub API and decode it.

    Raises:
        ReleaseAssetsError: Any transport, status or decode failure. Every branch
            raises; none returns a placeholder.
    """
    request = urllib.request.Request(url)
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ReleaseAssetsError(f"GET {url} failed: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ReleaseAssetsError(f"GET {url} failed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseAssetsError(f"GET {url} returned undecodable JSON: {exc}") from exc


def _floor() -> datetime:
    return parse_timestamp(
        os.environ.get("RELEASE_ASSETS_FLOOR") or DEFAULT_FLOOR,
        context="RELEASE_ASSETS_FLOOR",
    )


def _settle_hours() -> float:
    raw = os.environ.get("RELEASE_ASSETS_SETTLE_HOURS") or DEFAULT_SETTLE_HOURS
    try:
        value = float(raw)
    except ValueError as exc:
        raise ReleaseAssetsError(f"RELEASE_ASSETS_SETTLE_HOURS must be a number, got {raw!r}") from exc
    if value < 0:
        raise ReleaseAssetsError(f"RELEASE_ASSETS_SETTLE_HOURS must not be negative, got {value}")
    return value


def _render(report: dict[str, Any]) -> str:
    """The human summary printed to the job log.

    Deliberately verbose about what was NOT judged. An inert check that says
    nothing looks exactly like a passing one, and this check is inert by
    construction until the first release after the floor.
    """
    newest = report["newest_published"]
    lines = [
        f"Newest published release: {newest['tag']} (published {newest['published_at']}).",
        f"Floor: {report['floor']} — releases published before it are not evaluated (issue #1218, Q4).",
        f"Settle window: {report['settle_hours']}h.",
    ]
    if report["skipped_below_floor"]:
        lines.append(f"Below the floor, not evaluated: {', '.join(report['skipped_below_floor'])}.")
    for pending in report["skipped_within_settle"]:
        lines.append(
            f"Pending: {pending['tag']} is {pending['age_hours']}h old, inside the "
            f"{report['settle_hours']}h settle window — its delivery run may still be publishing."
        )

    if not report["evaluated"]:
        lines.append(
            "No settled release at or after the floor — nothing was judged. "
            "This check is INERT until the next release is published."
        )
        return "\n".join(lines)

    for entry in report["evaluated"]:
        if entry["complete"]:
            lines.append(f"OK {entry['tag']}: all {len(entry['expected_assets'])} expected asset(s) plus the packages block.")
            continue
        detail = []
        if entry["missing_assets"]:
            detail.append(f"missing asset(s): {', '.join(entry['missing_assets'])}")
        if not entry["packages_block_present"]:
            detail.append("release notes carry no packages block")
        lines.append(f"INCOMPLETE {entry['tag']}: {'; '.join(detail)}.")

    if report["alert"]:
        lines.append(f"RELEASE ASSETS INCOMPLETE: {len(report['incomplete'])} published release(s) affected.")
    else:
        lines.append(f"All {len(report['evaluated'])} evaluated release(s) are complete.")
    return "\n".join(lines)


def main(
    argv: list[str] | None = None,
    *,
    fetch: Callable[[str], Any] | None = None,
    now: datetime | None = None,
) -> int:
    """Run the check and write the report.

    Args:
        argv: Optional ``[report_path]``; defaults to :data:`REPORT_PATH`.
        fetch: Injection point for the HTTP layer (tests pass a fake).
        now: Injection point for the clock (tests pass a fixed instant).

    Returns:
        0 on a determined result. Undetermined raises
        :class:`ReleaseAssetsError`, which the module entry point turns into a
        red run with no report.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) > 1:
        print("usage: check_release_assets.py [report.json]", file=sys.stderr)
        return 2
    report_path = arguments[0] if arguments else REPORT_PATH

    report = build_report(
        fetch or api_json,
        repository=os.environ.get("GITHUB_REPOSITORY") or DEFAULT_REPOSITORY,
        floor=_floor(),
        settle_hours=_settle_hours(),
        now=now or datetime.now(timezone.utc),
    )

    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(_render(report))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ReleaseAssetsError as exc:
        # Loud, and no report written: an undetermined check is not a clean check.
        print(f"::error::release asset check could not be determined: {exc}", file=sys.stderr)
        sys.exit(1)
