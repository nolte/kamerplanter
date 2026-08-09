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
  2. that current registry build has been the current one for longer than
     DRIFT_THRESHOLD_DAYS (default 3).

The grace window (2) is the point of the threshold. A publish -> Renovate digest
PR -> automerge -> ArgoCD cycle normally completes within hours to about a day; a
weekend plus one flaky required check can stretch it to ~2. Three days clears a
normal slow cycle without alerting, yet catches a genuine multi-day stall within
days rather than weeks. Tune via DRIFT_THRESHOLD_DAYS; the divergence age is read
from the current image's config ``created`` timestamp (build time ~= publish time,
because these images are built and pushed in the same docker-publish job).

FAIL LOUD (NFR-018 section 2)
-----------------------------
A registry error, a missing digest header, an unparseable manifest or a missing
``created`` timestamp is NOT "no drift". It raises, main() prints ``::error::`` and
exits non-zero WITHOUT writing freshness-report.json — the workflow run goes red
and opens no issue. An empty/failed check must never read as a clean result.

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
        age = now - _created_at(path, manifest, token)
        age_days = age.total_seconds() / 86400.0
        entry = {
            "repository": repository,
            "channel": channel,
            "pinned": pinned,
            "current": current,
            "age_days": round(age_days, 1),
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
            f"  within grace: {e['repository']}:{e['channel']} diverged "
            f"{e['age_days']}d (< {threshold_days}d) — not yet alertable."
        )
    for e in drift:
        print(
            f"  DRIFT: {e['repository']}:{e['channel']} — pinned {e['pinned'][:19]}…, "
            f"registry {e['current'][:19]}…, current for {e['age_days']}d."
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
