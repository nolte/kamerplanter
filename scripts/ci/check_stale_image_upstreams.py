#!/usr/bin/env python3
"""Alert when the registry repository behind a pinned third-party image went quiet.

Issue #3060. Renovate answers "is there a newer tag in THIS repository?". It
cannot answer "does this repository still receive tags at all?" — and neither
could anything else here.

THE INCIDENT THIS EXISTS FOR
----------------------------
``src/frontend/Dockerfile`` pinned ``nginxinc/nginx-unprivileged:1.31-alpine``
by digest. Upstream moved publishing to ``nginx/nginx-unprivileged``. The old
Docker Hub repository kept resolving, but its newest tag push is 2026-10-19
(``1.31.7``); ``1.31.8`` (2026-10-21) and ``1.31.9`` (2026-11-18, ten security
fixes) were only ever pushed to the new coordinate. Renovate reported nothing
and ``Renovate Health`` stayed green, because from their side the pin was
simply up to date. The only signal was ZAP rule 20020 a month later (#3040 and
nine identical reports); #3061 repaired the pin.

A renamed or abandoned coordinate looks exactly like a quiet one unless
somebody asks the registry when the repository last received a tag.

WHAT IS MEASURED
----------------
For every third-party image the checkout references (see :func:`inventory`),
the date of the newest activity in its registry repository:

* **Docker Hub** — ``tag_last_pushed`` of the most recently updated tag, from
  the public tags API. This is a real push date.
* **ghcr.io** — the registry API carries no push date. Measured on 2026-11-20:
  ``/v2/<repo>/tags/list`` returns tags in creation order (hadolint ends in
  ``v2.15.1``, astral-sh/uv in ``0.13.9``, zaproxy in ``20261119-weekly``), so
  the check reads the image config's ``created`` timestamp of the newest few
  tags plus ``latest``. That is a BUILD date, not a push date, and the report
  says so per image (``signal``). It is the best anonymous signal there is, and
  for the question asked here — "is anyone still publishing?" — it is the same
  clock.
* **Any other registry** — no reader. The image is reported as NOT CHECKABLE
  and that is a finding, never a silent pass. Either add a reader or record the
  image in :data:`ACKNOWLEDGED_NOT_CHECKABLE` with the reason.

All reads are anonymous. No token is sent anywhere, and the request carries a
generic client name.

THE THRESHOLD, MEASURED AND STATED HONESTLY
-------------------------------------------
:data:`DEFAULT_THRESHOLD_DAYS` is 45, with per-image overrides in
:data:`THRESHOLD_OVERRIDES_DAYS`. The numbers behind it, read from the
registries on 2026-11-20 (age of the newest activity, in days): ollama 0,
selenium 0, renovate 0, postgres 0, valkey 0, rclone 0, timescaledb 1, zaproxy
1, nginx/nginx-unprivileged 2, python 3, node 3, uv 3, arangodb 15, busybox 21,
curl 23, hadolint 112. The largest gap between two consecutive push days in the
recent history of an image that keeps the default was 36 days (arangodb,
2026-06-29 to 2026-08-04), so 30 would alert on a healthy repository and 45
does not.

With 45 days this check would NOT have fired on the day the incident was found
(2026-11-19, day 31 of silence). It first alerts on 2026-12-03. That is a property of
the window, not a defect hidden behind a number chosen to flatter the check:
the old repository received its last push only two days before the first
release it missed, so no threshold separates "moved" from "between releases" in
the first weeks. This is a backstop that bounds the silence at 45 days instead
of leaving it unbounded; ``tests/unit/test_stale_image_upstreams_check.py``
pins both dates.

FAIL LOUD (NFR-018 section 2), AND WHAT IS A FINDING VERSUS UNDETERMINED
------------------------------------------------------------------------
*Determined* results go into the report and into the single deduplicated alert
issue: a stale repository, a repository the registry says does not exist
(HTTP 404 — the strongest form of "moved"), a repository with no tags, an image
on a registry without a reader, an override naming an image nothing pins.

*Undetermined* results make the RUN RED and write NO report, so no issue is
opened, updated or closed: a registry that is unreachable, rate-limits (429) or
answers 5xx after the retries, an undecodable answer, an EMPTY INVENTORY, or a
digest pin whose image name could not be read. A transient registry blip must
not spam the tracker, and an inventory that silently found nothing is precisely
the failure mode this check must not have. One unreachable image makes the
whole run undetermined rather than producing a partial report: a partial report
with no findings would close an open alert on evidence that was never
collected.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPORT_PATH = "stale-image-report.json"
HTTP_TIMEOUT_SECONDS = 20
HTTP_ATTEMPTS = 3
#: Generic on purpose: the request goes to third-party registries and names
#: neither this repository nor its owner.
USER_AGENT = "stale-image-upstream-check/1 (python-urllib)"

#: Days without activity after which a repository is reported. See the module
#: docstring for the measurement behind the number.
DEFAULT_THRESHOLD_DAYS = 45

#: Images whose upstream releases rarely, with the reason. Keyed by the image
#: name exactly as the checkout spells it. An entry naming an image the
#: inventory no longer contains is itself a finding, so this table cannot
#: outlive the pin it was written for.
THRESHOLD_OVERRIDES_DAYS: dict[str, tuple[int, str]] = {
    "curlimages/curl": (
        120,
        "curl ships roughly every eight weeks; push days measured 2026-11-20 were 56, 70 and 104 days "
        "apart (2026-10-28, 2026-09-02, 2026-06-24, 2026-04-29 / 2026-01-08)",
    ),
    "busybox": (
        365,
        "busybox releases about once a year and the official image is rebuilt irregularly; surviving "
        "tag push days measured 2026-11-20 lie up to 509 days apart (2024-09-12 to 2026-02-03)",
    ),
    "ghcr.io/hadolint/hadolint": (
        365,
        "hadolint releases sporadically; the newest image was built 2026-07-31, 112 days before the "
        "measurement on 2026-11-20, with the project alive",
    ),
}

#: Images on a registry this script has no reader for, accepted with a reason.
#: EMPTY today: every inventoried image lives on Docker Hub or ghcr.io. An entry
#: here turns a "not checkable" finding into a listed, visible exception.
ACKNOWLEDGED_NOT_CHECKABLE: dict[str, str] = {}

#: Images this repository builds itself: ``ghcr.io/nolte/kamerplanter-*`` as
#: published, bare ``kamerplanter-*`` as Skaffold names them in the dev values.
#: Their freshness is the delivery chain's subject (release-lag.yml), not this
#: check's.
_OWNED_IMAGE = re.compile(r"^(?:ghcr\.io/nolte/)?kamerplanter-")

_DIGEST = re.compile(r"@sha256:[0-9a-f]{64}")
#: ``name[:tag]@sha256:<digest>``. The tag is optional because a bare digest is
#: a pin too (#1563 found three of them).
_DIGEST_PIN = re.compile(
    r"(?P<name>[a-z0-9][a-z0-9._-]*(?::[0-9]+)?(?:/[a-z0-9][a-z0-9._-]*)*)"
    r"(?::(?P<tag>[A-Za-z0-9_][A-Za-z0-9._-]*))?"
    r"@sha256:[0-9a-f]{64}"
)
#: A Helm values image block: ``repository:`` directly followed by ``tag:``.
#: The chart's own dependencies spell ``repository:`` too, but as a URL and
#: without a ``tag:`` line beneath.
_HELM_IMAGE = re.compile(
    r"^[ \t]*repository:[ \t]*[\"']?(?P<name>[^\s\"'#]+)[\"']?[ \t]*\n[ \t]*tag:[ \t]*[\"']?(?P<tag>[^\s\"'#]+)",
    re.MULTILINE,
)

#: Hidden directories that hold files this repository ships or runs. Every other
#: dot-directory (``.git``, ``.venv``, ``.claude`` and its worktrees, caches) is
#: not walked.
_WALKED_DOT_DIRECTORIES = frozenset({".github", ".pins", ".taskfiles"})
#: Directories that hold copies rather than references: dependency trees, build
#: output, test fixtures (recorded Renovate dashboards full of old pins).
_PRUNED_DIRECTORIES = frozenset({"node_modules", "site", "dist", "build", "fixtures", "__pycache__"})
#: Recorded lane inputs quote workflow text, pins included; the workflow is the
#: reference, the record is not.
_PRUNED_PATHS = frozenset({".github/lane-inputs"})

_ATTESTATION_TAG = re.compile(r"^sha256-[0-9a-f]{64}")
_GHCR_TAGS_PAGE_SIZE = 1000
#: astral-sh/uv needed 9 pages on 2026-11-20. Past this the walk is refused
#: rather than left to run into the job timeout.
_GHCR_MAX_PAGES = 60
_GHCR_SAMPLED_TAGS = 3
_MANIFEST_ACCEPT = ", ".join(
    (
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    )
)
_NEXT_LINK = re.compile(r'<([^>]+)>\s*;\s*rel="next"')

#: ``fetch(url, headers) -> (decoded JSON body, response headers)``.
Fetch = Callable[[str, Mapping[str, str]], tuple[Any, Mapping[str, str]]]


class UndeterminedError(RuntimeError):
    """The check could not be decided. The run goes red and writes no report."""


class RepositoryNotFoundError(RuntimeError):
    """The registry says the repository does not exist. A determined finding."""


class NoUsableDateError(RuntimeError):
    """The repository exists but yields no activity date. A determined finding."""


@dataclass(frozen=True)
class Image:
    """One third-party image and every place the checkout references it."""

    name: str
    references: tuple[str, ...]


# ── Inventory ────────────────────────────────────────────────────────────────


def _is_image_file(name: str) -> bool:
    return name.startswith("Dockerfile") or name.endswith((".Dockerfile", ".yml", ".yaml"))


def _walk(repo_root: Path) -> list[Path]:
    found = []
    for directory, subdirectories, files in os.walk(repo_root):
        relative = Path(directory).relative_to(repo_root)
        subdirectories[:] = sorted(
            name
            for name in subdirectories
            if name not in _PRUNED_DIRECTORIES
            and (not name.startswith(".") or name in _WALKED_DOT_DIRECTORIES)
            and (relative / name).as_posix() not in _PRUNED_PATHS
        )
        found.extend(Path(directory) / name for name in sorted(files) if _is_image_file(name))
    return found


def inventory(repo_root: Path) -> list[Image]:
    """Every third-party image the checkout references, read from the checkout.

    DERIVED, NOT LISTED. The ``third-party images`` rule in ``renovate.json5``
    enumerates nine package names by hand and is a grouping rule, not an
    inventory: on 2026-11-20 the tree pinned seventeen distinct third-party
    images (selenium, curl, renovate, hadolint, zaproxy, uv and rclone are not
    in that rule). A second hand-kept list here would drift the same way, so
    the images are read from the files that use them:

    * every ``name[:tag]@sha256:<digest>`` in a Dockerfile or YAML file —
      Dockerfiles, compose files, workflow ``image:`` and ``*_IMAGE`` values,
      ``.pins/``, Taskfiles;
    * every ``repository:`` + ``tag:`` image block in a Helm values file, which
      is where an image pinned by tag only lives (``rclone/rclone``).

    Whole-line comments are skipped; images this repository builds are not
    third-party and are left out.

    Raises:
        UndeterminedError: A digest that no image name could be read from. Such
            a pin would otherwise drop out of the inventory unseen.
    """
    references: dict[str, list[str]] = {}
    for path in _walk(repo_root):
        relative = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("#"):
                continue
            pins = list(_DIGEST_PIN.finditer(line))
            if len(pins) != len(_DIGEST.findall(line)):
                raise UndeterminedError(
                    f"{relative}:{number} carries a sha256 digest that no image name could be read from. "
                    "The pin would be missing from the inventory, so nothing was measured."
                )
            for pin in pins:
                references.setdefault(pin.group("name"), []).append(f"{relative}:{number}")
        if relative.startswith("helm/") and path.name.startswith("values"):
            for block in _HELM_IMAGE.finditer(text):
                name = block.group("name")
                if "://" in name or "{{" in name:
                    continue
                # Newline arithmetic: turns the match offset into a line number.
                number = text.count("\n", 0, block.start()) + 1
                references.setdefault(name, []).append(f"{relative}:{number}")
    return [
        Image(name=name, references=tuple(dict.fromkeys(places)))
        for name, places in sorted(references.items())
        if not _OWNED_IMAGE.match(name)
    ]


# ── Registries ───────────────────────────────────────────────────────────────


def split_registry(name: str) -> tuple[str, str]:
    """``(registry host, repository path)`` by Docker's own naming rule.

    The first path component is a registry only when it contains a ``.`` or a
    ``:`` or is ``localhost``; otherwise the image lives on Docker Hub, and a
    single-component name is an official image under ``library/``.
    """
    first, _, rest = name.partition("/")
    if rest and ("." in first or ":" in first or first == "localhost"):
        return first, rest
    return "docker.io", name if "/" in name else f"library/{name}"


def parse_timestamp(value: Any, *, context: str) -> datetime:
    """An RFC 3339 timestamp as an aware datetime (nanoseconds tolerated)."""
    if not isinstance(value, str) or not value:
        raise UndeterminedError(f"{context}: expected a timestamp, got {value!r}")
    text = re.sub(r"(\.\d{6})\d+", r"\1", value.strip()).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise UndeterminedError(f"{context}: unparseable timestamp {value!r}") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def docker_hub_newest(repository: str, fetch: Fetch) -> tuple[datetime, str]:
    """Newest tag push in a Docker Hub repository."""
    url = f"https://hub.docker.com/v2/repositories/{repository}/tags?page_size=5&ordering=last_updated"
    body, _ = fetch(url, {})
    results = body.get("results") if isinstance(body, dict) else None
    if not isinstance(results, list):
        raise UndeterminedError(f"GET {url}: no `results` list in the answer")
    pushes = [
        (parse_timestamp(entry.get("tag_last_pushed") or entry.get("last_updated"), context=url), entry.get("name"))
        for entry in results
        if isinstance(entry, dict) and (entry.get("tag_last_pushed") or entry.get("last_updated"))
    ]
    if not pushes:
        raise NoUsableDateError("the repository has no tags")
    newest, tag = max(pushes, key=lambda push: push[0])
    return newest, f"tag `{tag}` pushed"


def ghcr_newest(repository: str, fetch: Fetch) -> tuple[datetime, str]:
    """Newest image build among the most recently created tags of a ghcr.io repository."""
    root = "https://ghcr.io"
    token_body, _ = fetch(f"{root}/token?scope=repository:{repository}:pull", {})
    token = token_body.get("token") if isinstance(token_body, dict) else None
    if not isinstance(token, str) or not token:
        raise UndeterminedError(f"ghcr.io issued no anonymous pull token for {repository}")
    headers = {"Authorization": f"Bearer {token}"}

    tags: list[str] = []
    url: str | None = f"{root}/v2/{repository}/tags/list?n={_GHCR_TAGS_PAGE_SIZE}"
    pages = 0
    while url:
        pages += 1
        if pages > _GHCR_MAX_PAGES:
            raise UndeterminedError(f"ghcr.io/{repository}: more than {_GHCR_MAX_PAGES} pages of tags")
        body, response_headers = fetch(url, headers)
        page = body.get("tags") if isinstance(body, dict) else None
        tags.extend(tag for tag in page or [] if isinstance(tag, str))
        link = next((value for key, value in response_headers.items() if key.lower() == "link"), "")
        following = _NEXT_LINK.search(link or "")
        url = urllib.parse.urljoin(root, following.group(1)) if following else None

    # Signature and attestation tags (`sha256-<digest>.att`) are created after
    # the image they describe and carry no image config.
    images = [tag for tag in tags if not _ATTESTATION_TAG.match(tag)]
    if not images:
        raise NoUsableDateError("the repository has no image tags")
    sampled = list(dict.fromkeys(images[-_GHCR_SAMPLED_TAGS:] + (["latest"] if "latest" in images else [])))

    manifest_headers = {**headers, "Accept": _MANIFEST_ACCEPT}
    builds: list[tuple[datetime, str]] = []
    for tag in sampled:
        manifest, _ = fetch(f"{root}/v2/{repository}/manifests/{tag}", manifest_headers)
        if isinstance(manifest, dict) and isinstance(manifest.get("manifests"), list):
            # A multi-platform index. Attestation manifests are listed with the
            # platform `unknown/unknown` and have no image config.
            platforms = [
                entry
                for entry in manifest["manifests"]
                if isinstance(entry, dict) and (entry.get("platform") or {}).get("os") != "unknown"
            ]
            if not platforms:
                continue
            manifest, _ = fetch(f"{root}/v2/{repository}/manifests/{platforms[0]['digest']}", manifest_headers)
        digest = (manifest.get("config") or {}).get("digest") if isinstance(manifest, dict) else None
        if not digest:
            continue
        config, _ = fetch(f"{root}/v2/{repository}/blobs/{digest}", headers)
        created = config.get("created") if isinstance(config, dict) else None
        if not created:
            continue
        built = parse_timestamp(created, context=f"ghcr.io/{repository}:{tag}")
        # Reproducible builds stamp the epoch (or SOURCE_DATE_EPOCH of some old
        # commit). A date before 2000 says nothing about activity.
        if built.year >= 2000:
            builds.append((built, tag))
    if not builds:
        raise NoUsableDateError(
            "none of the newest tags carries a usable `created` date (reproducible build or no image config)"
        )
    newest, tag = max(builds, key=lambda build: build[0])
    return newest, f"image `{tag}` built"


#: Registry host -> reader. A host missing here is "not checkable".
READERS: dict[str, Callable[[str, Fetch], tuple[datetime, str]]] = {
    "docker.io": docker_hub_newest,
    "ghcr.io": ghcr_newest,
}


# ── Verdict ──────────────────────────────────────────────────────────────────


def build_report(images: list[Image], fetch: Fetch, *, now: datetime) -> dict[str, Any]:
    """Measure every image and decide.

    Raises:
        UndeterminedError: Empty inventory, or any registry answer that is not
            a measurement (see the module docstring).
    """
    if not images:
        raise UndeterminedError(
            "the inventory is empty: no third-party image reference was found in the checkout. "
            "That is a broken inventory, not a clean result."
        )

    entries: list[dict[str, Any]] = []
    findings: list[str] = []
    for image in images:
        registry, repository = split_registry(image.name)
        threshold, reason = THRESHOLD_OVERRIDES_DAYS.get(image.name, (DEFAULT_THRESHOLD_DAYS, None))
        entry: dict[str, Any] = {
            "image": image.name,
            "registry": registry,
            "repository": repository,
            "references": list(image.references),
            "threshold_days": threshold,
            "threshold_reason": reason,
            "newest_activity": None,
            "signal": None,
            "age_days": None,
            "status": "fresh",
        }
        entries.append(entry)
        where = ", ".join(image.references)
        reader = READERS.get(registry)
        if reader is None:
            acknowledged = ACKNOWLEDGED_NOT_CHECKABLE.get(image.name)
            entry["status"] = "not checkable (acknowledged)" if acknowledged else "not checkable"
            entry["signal"] = acknowledged or f"no reader for registry {registry}"
            if not acknowledged:
                findings.append(
                    f"`{image.name}` cannot be checked: there is no reader for the registry `{registry}`. "
                    f"Add one or record the image in `ACKNOWLEDGED_NOT_CHECKABLE` with a reason. Referenced in {where}."
                )
            continue
        try:
            newest, signal = reader(repository, fetch)
        except RepositoryNotFoundError as exc:
            entry["status"] = "not found"
            entry["signal"] = str(exc)
            findings.append(
                f"`{image.name}`: the registry reports no such repository ({exc}). The image was removed or "
                f"renamed. Referenced in {where}."
            )
            continue
        except NoUsableDateError as exc:
            entry["status"] = "not checkable"
            entry["signal"] = str(exc)
            findings.append(f"`{image.name}` cannot be checked: {exc}. Referenced in {where}.")
            continue
        age = round((now - newest).total_seconds() / 86400, 1)
        entry["newest_activity"] = newest.astimezone(timezone.utc).isoformat()
        entry["signal"] = signal
        entry["age_days"] = age
        if age > threshold:
            entry["status"] = "stale"
            findings.append(
                f"`{image.name}`: newest activity in `{registry}/{repository}` is {newest.date().isoformat()} "
                f"({signal}), {age} days ago — past the {threshold}-day window. Check whether upstream "
                f"publishes under another name. Referenced in {where}."
            )

    pinned = {image.name for image in images}
    for table, label in (
        (THRESHOLD_OVERRIDES_DAYS, "THRESHOLD_OVERRIDES_DAYS"),
        (ACKNOWLEDGED_NOT_CHECKABLE, "ACKNOWLEDGED_NOT_CHECKABLE"),
    ):
        for name in sorted(set(table) - pinned):
            findings.append(
                f"`{label}` names `{name}`, which nothing in the checkout references any more. Remove the entry "
                "(or rename it together with the pin) so the exception does not outlive its image."
            )

    return {
        "checked_at": now.astimezone(timezone.utc).isoformat(),
        "default_threshold_days": DEFAULT_THRESHOLD_DAYS,
        "images": entries,
        "findings": findings,
        "alert": bool(findings),
    }


def render(report: dict[str, Any]) -> str:
    """The human summary printed to the job log: every image looked at, then the verdict."""
    lines = [f"Looked at {len(report['images'])} third-party image(s):"]
    for entry in report["images"]:
        if entry["age_days"] is None:
            measured = entry["signal"]
        else:
            measured = f"{entry['newest_activity'][:10]}, {entry['age_days']}d ago ({entry['signal']})"
        lines.append(
            f"  [{entry['status']}] {entry['image']} — {measured}; window {entry['threshold_days']}d; "
            f"{len(entry['references'])} reference(s), first {entry['references'][0]}"
        )
    if report["findings"]:
        lines.append(f"STALE IMAGE UPSTREAM: {len(report['findings'])} finding(s).")
        lines.extend(f"  - {finding}" for finding in report["findings"])
    else:
        lines.append("Every repository received activity inside its window.")
    return "\n".join(lines)


# ── Transport ────────────────────────────────────────────────────────────────


def http_fetch(url: str, headers: Mapping[str, str]) -> tuple[Any, Mapping[str, str]]:
    """Anonymous GET, decoded as JSON.

    Raises:
        RepositoryNotFoundError: HTTP 404, or ghcr.io refusing an anonymous pull
            token or the pull itself (401/403) — its answer for a repository
            that is gone or was made private. Both are answers, not outages.
        UndeterminedError: Anything else, after :data:`HTTP_ATTEMPTS` tries for
            the transient kinds (429, 5xx, transport errors).
    """
    # The host is logged, never the query: a ghcr.io token request carries the
    # repository scope and nothing secret, but headers (the bearer token) are
    # never printed.
    failure = "no attempt made"
    for attempt in range(1, HTTP_ATTEMPTS + 1):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
                return json.load(response), dict(response.headers.items())
        except urllib.error.HTTPError as exc:
            if exc.code == 404 or (exc.code in (401, 403) and "ghcr.io" in url):
                raise RepositoryNotFoundError(f"HTTP {exc.code}") from exc
            failure = f"HTTP {exc.code}"
            if exc.code != 429 and exc.code < 500:
                break
        except (urllib.error.URLError, TimeoutError) as exc:
            failure = str(exc)
        except json.JSONDecodeError as exc:
            failure = f"undecodable JSON: {exc}"
            break
        if attempt < HTTP_ATTEMPTS:
            time.sleep(2 * attempt)
    raise UndeterminedError(f"GET {url} failed: {failure}")


def main(
    argv: list[str] | None = None,
    *,
    fetch: Fetch | None = None,
    now: datetime | None = None,
    repo_root: Path | None = None,
) -> int:
    """Run the check and write the report.

    Args:
        argv: Optional ``[report_path]``; defaults to :data:`REPORT_PATH`.
        fetch: Injection point for the registry access (tests pass a fake).
        now: Injection point for the clock.
        repo_root: Checkout to read; defaults to ``$GITHUB_WORKSPACE`` or the
            current directory.

    Returns:
        0 on a determined result, with or without findings. Undetermined
        raises :class:`UndeterminedError`, which the module entry point turns
        into a red run with no report.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) > 1:
        print("usage: check_stale_image_upstreams.py [report.json]", file=sys.stderr)
        return 2
    report_path = arguments[0] if arguments else REPORT_PATH
    root = repo_root or Path(os.environ.get("GITHUB_WORKSPACE") or Path.cwd())

    report = build_report(inventory(root), fetch or http_fetch, now=now or datetime.now(timezone.utc))

    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(render(report))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except UndeterminedError as exc:
        # Loud, and no report written: an undetermined check is not a clean check.
        print(f"::error::stale image upstream check could not be determined: {exc}", file=sys.stderr)
        sys.exit(1)
