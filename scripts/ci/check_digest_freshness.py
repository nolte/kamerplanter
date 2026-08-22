#!/usr/bin/env python3
"""Alert when a digest-pinned Kamerplanter chart image has fallen behind its channel.

Issue #1026 — the missing half of #987/#1024. The chart pins immutable digests
(``<channel>@sha256:<digest>``) kept current by Renovate. scripts/check_chart_image_
digests.py proves a pin is present, well-formed and consistent, and states in its
own header that it CANNOT prove the pin is CURRENT — that fact lives in the
registry. This script asks the registry.

WHAT COUNTS AS STALE
--------------------
A pin is stale when BOTH hold:

  1. the digest the registry currently serves for the pin's channel differs from
     the pinned digest, AND
  2. the PINNED build was produced more than DRIFT_THRESHOLD_DAYS ago (default 3).

The grace window (2) is the point of the threshold. A publish -> Renovate digest
PR -> automerge -> ArgoCD cycle normally completes within hours to about a day; a
weekend plus one flaky required check can stretch it to ~2. Three days clears a
normal slow cycle without alerting, yet catches a genuine multi-day stall within
days rather than weeks.

WHICH TIMESTAMP THE WINDOW IS MEASURED FROM, AND WHY (#1210)
------------------------------------------------------------
Until #1210 condition (2) read the ``created`` timestamp of the CURRENT registry
build — "how old is the newest build" rather than "how long has the pin been
behind". In a repository that publishes on nearly every merge the newest build is
always hours old, so the comparison could never reach a 3-day window: the check
was structurally unable to alert, however far behind the chart was. It proved
that in production. From 2026-08-12 to 2026-08-16 the chart pinned
``sha256:db4e7f1b…`` while ghcr.io served ``sha256:e2b0aec4…`` (measured: pinned
build 3.95 d old, channel head 0.04 d old), and the 2026-08-16 06:29Z run
reported "All chart image digests are current — nothing to report".

The quantity we actually want is the DIVERGENCE DURATION: now minus the moment
the pin stopped being what the channel serves, i.e. the ``created`` timestamp of
the oldest registry build newer than the pinned one. That moment is not
obtainable from the registry at acceptable cost, measured rather than assumed on
2026-08-16:

  * The registry v2 API exposes no tag-update time. A manifest response carries
    ``docker-content-digest``, ``etag`` and ``date``; nothing says when the tag
    was last moved onto that manifest.
  * The GitHub Packages REST API (``/users/nolte/packages/container/…/versions``)
    does carry per-version ``created_at`` — but it is 401 anonymously and needs
    the ``read:packages`` scope, which the workflow's ``GITHUB_TOKEN`` is not
    guaranteed to satisfy for a user-owned package. A guard whose only data
    source may 403 in CI is a guard that reports red daily.
  * Reconstructing the history from ``/v2/<name>/tags/list`` is possible in
    principle — every build also carries a commit-sha tag — but each tag costs
    an index fetch, a platform-manifest fetch and a config-blob fetch. Measured
    on kamerplanter-backend: 483 tags, ~0.65 s per tag, ~5 min per repository,
    ~21 min for the four owned images — past this job's 10-minute timeout. It
    would also have to lean on GHCR returning tags in push order, which the OCI
    spec does not promise (it asks for lexical order) and which could change
    without notice, quietly making the guard inert again.

So this script uses the anchor it CAN measure exactly: the ``created`` timestamp
of the PINNED build, reported as ``age_days``. Because a build cannot have been
superseded before it existed, ``now - created(pinned)`` is an UPPER BOUND on the
divergence duration, and ``now - created(current)`` — the pre-#1210 measure, kept
in the report as ``current_age_days`` — is a LOWER BOUND. The report carries
both, and the alert quotes both, so nobody reads an upper bound as a measurement.

What the approximation does NOT cover: it overstates the divergence by the gap
between the pinned build and its successor. On this repository, which publishes
near-daily, that gap is hours; on a repository that publishes rarely, a pin
superseded minutes ago could be reported as drift because the build behind it is
older than the window. The overstatement is bounded by the publish interval and
is one-sided — it alerts early, never late, which is the right direction for a
guard whose failure mode was never alerting at all. Both timestamps are build
times, which are ~= publish times here, because these images are built and pushed
in the same docker-publish job.

FAIL LOUD (NFR-018 section 2)
-----------------------------
A registry error, a missing digest header, an unparseable manifest or a missing
``created`` timestamp is NOT "no drift". It raises, main() prints ``::error::`` and
exits non-zero WITHOUT writing freshness-report.json — the workflow run goes red
and opens no issue. An empty/failed check must never read as a clean result.

That now includes a PINNED digest the registry will not serve: since #1210 the
pinned manifest is fetched too, so a pin GHCR has dropped raises instead of being
skipped. Deliberate — a chart pinning a build that cannot be pulled is broken,
not merely stalled, and the red run is the louder signal.

Third-party images (arangodb, timescale/timescaledb) are out of scope, exactly as
in the digest guard and renovate.json5: they are Renovate-aged on version tags,
not on our channel pins. The workflow's ``yq`` extraction only feeds this script
the ``ghcr.io/nolte/kamerplanter-*`` pins.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

REGISTRY_HOST = "ghcr.io"
OWNED_PREFIX = "ghcr.io/nolte/kamerplanter-"
REPORT_PATH = "freshness-report.json"

# ``<channel>@sha256:<64 hex>`` — the shape check_chart_image_digests.py enforces.
PINNED_TAG_RE = re.compile(r"^(?P<channel>[\w][\w.\-]*)@(?P<digest>sha256:[0-9a-f]{64})$")

MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)


class FreshnessError(RuntimeError):
    """A condition under which the check could not be determined — fail loud."""


_token_cache: dict[str, str] = {}


def _get_token(path: str) -> str:
    if path in _token_cache:
        return _token_cache[path]
    url = f"https://{REGISTRY_HOST}/token?scope=repository:{path}:pull&service={REGISTRY_HOST}"
    req = urllib.request.Request(url)
    gh_token = os.environ.get("GHCR_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if gh_token:
        # Same exchange the pin script uses: basic-auth the CI token so this keeps
        # working for a private package; anonymous works for the public ones.
        basic = base64.b64encode(f"x-access-token:{gh_token}".encode()).decode()
        req.add_header("Authorization", f"Basic {basic}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            token = json.load(resp).get("token", "")
    except urllib.error.URLError as exc:
        raise FreshnessError(f"pull-token exchange failed for {path}: {exc}") from exc
    if not token:
        raise FreshnessError(f"registry returned no pull token for {path}")
    _token_cache[path] = token
    return token


def _manifest(path: str, reference: str, token: str) -> tuple[dict, str]:
    """Return (manifest-json, docker-content-digest) for a reference."""
    url = f"https://{REGISTRY_HOST}/v2/{path}/manifests/{reference}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", MANIFEST_ACCEPT)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            digest = resp.headers.get("docker-content-digest", "")
            body = json.load(resp)
    except urllib.error.HTTPError as exc:
        raise FreshnessError(f"{path}:{reference} manifest request failed: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise FreshnessError(f"{path}:{reference} manifest request failed: {exc}") from exc
    if not re.match(r"^sha256:[0-9a-f]{64}$", digest):
        raise FreshnessError(f"{path}:{reference} returned no docker-content-digest")
    return body, digest


def _blob_json(path: str, digest: str, token: str) -> dict:
    url = f"https://{REGISTRY_HOST}/v2/{path}/blobs/{digest}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise FreshnessError(f"{path} config blob {digest} unreadable: {exc}") from exc


def _created_at(path: str, manifest: dict, token: str) -> datetime:
    """Descend index -> platform manifest -> config blob and read ``.created``."""
    if manifest.get("manifests"):
        candidates = [
            m
            for m in manifest["manifests"]
            if m.get("platform", {}).get("os") not in (None, "unknown")
            and m.get("platform", {}).get("architecture") not in (None, "unknown")
        ]
        chosen = next(
            (
                m
                for m in candidates
                if m["platform"].get("os") == "linux" and m["platform"].get("architecture") == "amd64"
            ),
            candidates[0] if candidates else None,
        )
        if chosen is None:
            raise FreshnessError(f"{path}: index carries no usable platform manifest")
        sub, _ = _manifest(path, chosen["digest"], token)
        return _created_at(path, sub, token)

    config_digest = manifest.get("config", {}).get("digest")
    if not config_digest:
        raise FreshnessError(f"{path}: image manifest has no config digest")
    created = _blob_json(path, config_digest, token).get("created")
    if not created:
        raise FreshnessError(f"{path}: image config has no `created` timestamp")
    return _parse_ts(created)


def _parse_ts(value: str) -> datetime:
    normalised = value.replace("Z", "+00:00")
    # Defend against >6 fractional digits, which fromisoformat rejects.
    normalised = re.sub(r"(\.\d{6})\d+", r"\1", normalised)
    try:
        dt = datetime.fromisoformat(normalised)
    except ValueError as exc:
        raise FreshnessError(f"unparseable created timestamp {value!r}: {exc}") from exc
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_digest_freshness.py <pins.json>", file=sys.stderr)
        return 2

    threshold_days = int(os.environ.get("DRIFT_THRESHOLD_DAYS", "3"))
    with open(sys.argv[1], encoding="utf-8") as handle:
        pins = json.load(handle)

    # De-duplicate to (repository, channel, pinned-digest). Backend appears 3x and
    # frontend 2x with one digest each; check_chart_image_digests.py already fails
    # a split, so we trust one digest per (repository, channel) here.
    seen: dict[tuple[str, str], str] = {}
    for pin in pins:
        repository = str(pin.get("repository", ""))
        if not repository.startswith(OWNED_PREFIX):
            continue
        match = PINNED_TAG_RE.match(str(pin.get("tag", "")))
        if not match:
            raise FreshnessError(
                f"{repository} tag {pin.get('tag')!r} is not `<channel>@sha256:<digest>` "
                "— check_chart_image_digests.py should have caught this pre-merge."
            )
        seen[(repository, match.group("channel"))] = match.group("digest")

    if not seen:
        raise FreshnessError("no owned image pins to check — refusing to report clean")

    now = datetime.now(timezone.utc)
    drift: list[dict] = []
    within_grace: list[dict] = []
    checked = 0

    for (repository, channel), pinned in sorted(seen.items()):
        path = repository[len(f"{REGISTRY_HOST}/") :]
        token = _get_token(path)
        manifest, current = _manifest(path, channel, token)
        checked += 1
        if current == pinned:
            continue

        # The window is measured from the PINNED build, not from the channel
        # head: the head is always fresh here, which is what made this check
        # unable to fire (#1210 — see the module docstring). Fetched by digest,
        # so this resolves the exact build the chart deploys.
        pinned_manifest, _ = _manifest(path, pinned, token)
        pinned_created = _created_at(path, pinned_manifest, token)
        current_created = _created_at(path, manifest, token)

        # Upper bound on the divergence: the pin cannot have been superseded
        # before it was built. Lower bound: it has been diverged at least since
        # the build now serving the channel was pushed.
        age_days = (now - pinned_created).total_seconds() / 86400.0
        current_age_days = (now - current_created).total_seconds() / 86400.0
        entry = {
            "repository": repository,
            "channel": channel,
            "pinned": pinned,
            "current": current,
            # Name kept for the workflow's github-script step, which reads it.
            "age_days": round(age_days, 1),
            "pinned_created": pinned_created.isoformat(),
            "current_created": current_created.isoformat(),
            "current_age_days": round(current_age_days, 1),
        }
        (drift if age_days >= threshold_days else within_grace).append(entry)

    report = {
        "checked": checked,
        "threshold_days": threshold_days,
        "drift": drift,
        "within_grace": within_grace,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(f"Checked {checked} pin(s) against {REGISTRY_HOST}.")
    for e in within_grace:
        print(
            f"  within grace: {e['repository']}:{e['channel']} — pinned build is "
            f"{e['age_days']}d old (< {threshold_days}d) and no longer current; not yet alertable."
        )
    for e in drift:
        print(
            f"  DRIFT: {e['repository']}:{e['channel']} — pinned {e['pinned'][:19]}… built "
            f"{e['age_days']}d ago, registry serves {e['current'][:19]}… built "
            f"{e['current_age_days']}d ago; the pin has been behind for at most "
            f"{e['age_days']}d and at least {e['current_age_days']}d."
        )
    if not drift:
        print("No stale pins beyond the grace window.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FreshnessError as exc:
        # Loud, and no report written: an undetermined check is not a clean check.
        print(f"::error::digest freshness check could not be determined: {exc}", file=sys.stderr)
        sys.exit(1)
