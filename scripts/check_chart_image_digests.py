#!/usr/bin/env python3
"""Refuse a Kamerplanter image reference in the Helm chart without a digest.

Issue #987: the chart referenced `ghcr.io/nolte/kamerplanter-*:latest`. A tag
that is rewritten by every publish cannot be rolled back to — "go back to the
previous image" resolves to whatever is current — so the documented recovery
path was inert in exactly the situation it exists for. The values now carry
`tag: <channel>@sha256:<digest>`, and this check is what keeps them that way.

It runs in the required `static` gate rather than in the chart's own
`skaffold-verify` workflow, which is path-filtered and not required: a pin that
is only checked when someone happens to touch `helm/**` in a pull request is a
pin that can be dropped by a merge conflict resolution and noticed by nobody.

Two things are checked, and neither is the interesting failure:

  1. every Kamerplanter image reference carries `@sha256:<64 hex>`
  2. all references to the SAME repository within one file carry the SAME
     digest — the backend image appears three times (api, celery-worker,
     celery-beat), so a half-applied bump would ship two builds of one
     application against one database schema

What this CANNOT check is whether the pinned digest is the CURRENT one. Nothing
inside the repository can: the answer lives in the registry. That is the
residual risk of moving delivery onto an updater — a stalled Renovate stops
deploys silently, where a broken publish step fails loudly. If that risk is to
be closed, it is closed by a scheduled job that compares these digests against
`:latest` in GHCR and reports drift, not by anything here.

Third-party images (arangodb, timescale/timescaledb) are deliberately out of
scope: they sit on upstream version tags that Renovate ages, and folding them in
here would silently widen a delivery change into a supply-chain policy change.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CHART_GLOB = "helm/**/values*.yaml"

# The images this repository builds and publishes. Everything else is upstream.
OWNED_PREFIX = "ghcr.io/nolte/kamerplanter-"

# Renovate's helm-values manager matches any key ending in `image` (case
# insensitive) that carries `repository` plus `tag`/`version`; the same
# heuristic is used here so the guard and the updater see the same references.
IMAGE_KEY_RE = re.compile(r"image$", re.IGNORECASE)

# `<channel>@sha256:<64 hex>` — the shape Renovate writes for a pinned tag
# (autoReplaceStringTemplate `{{newValue}}{{#if newDigest}}@{{newDigest}}{{/if}}`).
PINNED_TAG_RE = re.compile(r"^[\w][\w.\-]*@sha256:[0-9a-f]{64}$")


def _walk(node: Any, path: str = "") -> list[tuple[str, str, str]]:
    """Yield (yaml-path, repository, tag) for every image spec found."""
    found: list[tuple[str, str, str]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            child = f"{path}.{key}" if path else str(key)
            if (
                IMAGE_KEY_RE.search(str(key))
                and isinstance(value, dict)
                and "repository" in value
            ):
                repository = str(value.get("repository", ""))
                tag = str(value.get("tag", value.get("version", "")))
                found.append((child, repository, tag))
                # An image spec has no nested image specs; do not descend.
                continue
            found.extend(_walk(value, child))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            found.extend(_walk(item, f"{path}[{index}]"))
    return found


def main() -> int:
    problems: list[str] = []
    checked = 0

    files = sorted(REPO_ROOT.glob(CHART_GLOB))
    if not files:
        print(
            "::error::No chart values files matched "
            f"{CHART_GLOB} — the guard would pass by examining nothing.",
            file=sys.stderr,
        )
        return 1

    for values_file in files:
        try:
            documents = list(yaml.safe_load_all(values_file.read_text()))
        except yaml.YAMLError as exc:
            problems.append(f"{values_file.relative_to(REPO_ROOT)}: unparseable YAML: {exc}")
            continue

        digests_seen: dict[str, dict[str, list[str]]] = {}
        for document in documents:
            for yaml_path, repository, tag in _walk(document):
                if not repository.startswith(OWNED_PREFIX):
                    continue
                checked += 1
                where = f"{values_file.relative_to(REPO_ROOT)}:{yaml_path}"
                if not PINNED_TAG_RE.match(tag):
                    problems.append(
                        f"{where}\n"
                        f"    {repository}:{tag}\n"
                        "    is not pinned. Use `tag: <channel>@sha256:<digest>`; resolve the\n"
                        "    digest with `docker buildx imagetools inspect "
                        f"{repository}:<channel>`."
                    )
                    continue
                digest = tag.split("@", 1)[1]
                digests_seen.setdefault(repository, {}).setdefault(digest, []).append(where)

        for repository, by_digest in digests_seen.items():
            if len(by_digest) > 1:
                detail = "\n".join(
                    f"      {digest} <- {', '.join(places)}"
                    for digest, places in sorted(by_digest.items())
                )
                problems.append(
                    f"{values_file.relative_to(REPO_ROOT)}: {repository} is pinned to "
                    f"{len(by_digest)} different digests in one file:\n{detail}\n"
                    "    A half-applied bump ships two builds of one application."
                )

    if problems:
        print(
            "::error::Kamerplanter image references must be digest-pinned (#987):",
            file=sys.stderr,
        )
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    print(f"{checked} Kamerplanter image references, all digest-pinned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
