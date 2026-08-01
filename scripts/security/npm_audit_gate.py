#!/usr/bin/env python3
"""Fail the build on npm advisories that are not explicitly and temporarily accepted.

Why this exists (NFR-009 §4.1): the backend has audited its pinned dependencies
with ``pip-audit`` on every pull request for a long time. The frontend had no
equivalent. Trivy scans ``package-lock.json`` but only at ``CRITICAL``, so a
*high*-severity advisory in shipped JavaScript was invisible to every gate in the
repository — and one was: GHSA-qwww-vcr4-c8h2 sat in the production tree
undetected.

Why not plain ``npm audit --audit-level=high``: it has no allowlist. The only
ways to get a green build with a known, assessed, non-applicable advisory are to
lower the threshold for everything or to drop the gate — both of which trade a
real signal for a green tick. This wrapper keeps the threshold and makes each
exception an individually reviewed entry instead.

The allowlist deliberately makes an exception expensive:

* ``reason`` must say why the advisory does not apply *to this application*.
  "Not exploitable" without a mechanism is not a reason.
* ``expires`` is mandatory. An accepted advisory turns the build red again on
  that date, which forces a re-assessment rather than letting the entry become
  permanent furniture. A stale suppression is indistinguishable from an
  unnoticed vulnerability.

Usage:
    npm_audit_gate.py [--omit-dev] [--allowlist PATH] [--severity high,critical]

Run from the directory containing ``package.json``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

DEFAULT_ALLOWLIST = Path("../../tests/security/npm-audit-allowlist.yaml")
REQUIRED_FIELDS = ("advisory", "package", "reason", "expires")


def run_npm_audit(omit_dev: bool) -> dict[str, Any]:
    """Return the parsed ``npm audit --json`` report.

    ``npm audit`` exits non-zero whenever it finds anything, so the return code
    carries no information this script needs — the report does. A failure to
    produce parseable JSON, on the other hand, is fatal: an unreadable report
    must never be mistaken for a clean one.
    """
    cmd = ["npm", "audit", "--json"]
    if omit_dev:
        cmd.append("--omit=dev")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if not proc.stdout.strip():
        print(f"::error::`{' '.join(cmd)}` produced no output.", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        print(f"::error::Could not parse the npm audit report: {exc}", file=sys.stderr)
        print(proc.stdout[:2000], file=sys.stderr)
        sys.exit(2)


def load_allowlist(path: Path) -> dict[str, dict[str, Any]]:
    """Return accepted advisories keyed by advisory id, refusing malformed entries."""
    if not path.exists():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = raw.get("accepted") or []
    allowed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        missing = [f for f in REQUIRED_FIELDS if not entry.get(f)]
        if missing:
            print(
                f"::error file={path}::Allowlist entry {entry!r} is missing "
                f"required field(s): {', '.join(missing)}",
                file=sys.stderr,
            )
            sys.exit(2)
        allowed[str(entry["advisory"])] = entry
    return allowed


def advisory_ids(
    name: str,
    vulns: dict[str, Any],
    _seen: frozenset[str] = frozenset(),
) -> set[str]:
    """Collect the advisory identifiers a vulnerability entry refers to.

    ``npm audit`` reports two shapes of ``via``. A directly vulnerable package
    carries dicts that include the advisory URL. A package that is only
    vulnerable *through* a dependency carries plain strings naming that
    dependency — ``react-router-dom`` has ``via: ["react-router"]`` and no
    advisory of its own.

    Resolving only the first shape was a defect this function had on its first
    draft: the transitive entry produced no identifiers, so it could never match
    an allowlist entry and the gate stayed red no matter what was accepted. The
    string form is therefore followed to the package it names, guarding against
    the dependency cycles npm's own graph can contain.
    """
    if name in _seen:
        return set()
    seen = _seen | {name}
    ids: set[str] = set()
    for via in vulns.get(name, {}).get("via", []):
        if isinstance(via, dict):
            url = via.get("url", "")
            if "/advisories/" in url:
                ids.add(url.rsplit("/", 1)[-1])
        elif isinstance(via, str):
            ids |= advisory_ids(via, vulns, seen)
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--omit-dev", action="store_true", help="audit shipped dependencies only"
    )
    parser.add_argument("--allowlist", type=Path, default=DEFAULT_ALLOWLIST)
    parser.add_argument(
        "--severity",
        default="high,critical",
        help="comma-separated severities that fail the build (default: high,critical)",
    )
    args = parser.parse_args()

    blocking = {s.strip() for s in args.severity.split(",") if s.strip()}
    allowed = load_allowlist(args.allowlist)
    report = run_npm_audit(args.omit_dev)
    today = date.today()

    unaccepted: list[str] = []
    accepted: list[str] = []
    expired: list[str] = []
    used: set[str] = set()

    vulns = report.get("vulnerabilities", {})
    for name, vuln in sorted(vulns.items()):
        severity = vuln.get("severity", "")
        if severity not in blocking:
            continue
        ids = advisory_ids(name, vulns)
        match = next((i for i in ids if i in allowed), None)
        if match is None:
            shown = ", ".join(sorted(ids)) or "no advisory id in report"
            unaccepted.append(f"{name} ({severity}) — {shown}")
            continue
        used.add(match)
        entry = allowed[match]
        expires = entry["expires"]
        if not isinstance(expires, date):
            expires = date.fromisoformat(str(expires))
        if expires < today:
            expired.append(
                f"{name} ({severity}) — {match}, accepted until {expires.isoformat()}, "
                f"which has passed. Re-assess: {entry['reason']}"
            )
        else:
            accepted.append(
                f"{name} ({severity}) — {match}, accepted until {expires.isoformat()}"
            )

    for line in accepted:
        print(f"ACCEPTED  {line}")

    # An allowlist entry whose advisory no longer appears is dead weight that
    # quietly widens the gate for whatever reuses that id later.
    for stale in sorted(set(allowed) - used):
        print(
            f"::warning file={args.allowlist}::Allowlist entry {stale} matches no "
            f"current advisory and should be removed."
        )

    if expired:
        print(
            "::error::Accepted advisories have expired and need re-assessment:",
            file=sys.stderr,
        )
        for line in expired:
            print(f"  {line}", file=sys.stderr)
    if unaccepted:
        print(
            "::error::Unaccepted advisories at or above the blocking severity:",
            file=sys.stderr,
        )
        for line in unaccepted:
            print(f"  {line}", file=sys.stderr)
        print(
            "  Fix the dependency, or add a reviewed entry with a reason and an "
            f"expiry to {args.allowlist}.",
            file=sys.stderr,
        )

    if expired or unaccepted:
        return 1

    scanned = len(vulns)
    print(
        f"OK — no unaccepted {'/'.join(sorted(blocking))} advisories ({scanned} entries scanned)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
