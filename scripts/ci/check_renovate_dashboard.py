#!/usr/bin/env python3
"""Alert when Renovate's Dependency Dashboard reports a problem or the manager inventory drifts.

Issue #1383, point 1. This is the check that would have caught six silent weeks.

THE INCIDENT THIS EXISTS FOR
----------------------------
From 2026-08-02 to 2026-09-10 Renovate's ``pip-compile`` manager extracted
**nothing** from this repository. It rejects lock-header options outside its own
allowlist, and the two locks here needed ``--no-strip-extras`` and
``--no-build-isolation`` (#906, #1303). The backend locks therefore aged
untouched for six weeks while every lane stayed green, because nothing in this
repository reads Renovate's output. The one signal that existed was a line

    ⚠️ WARN: pip-compile error

inside the ``## Repository problems`` section of the Dependency Dashboard issue
(#12) — a place nobody looks at on a schedule. Meanwhile the ``poetry`` manager
silently picked up the two side-service ``pyproject.toml`` files and opened
source-only pull requests that left their locks stale (#1371).

Nothing would notice the identical thing happening to ``pep621`` tomorrow. That
is what this script is.

WHAT IT CHECKS
--------------
1. **Repository problems.** Any ``WARN``/``ERROR`` under the dashboard's
   ``## Repository problems`` heading is a finding, quoted verbatim. Renovate
   writes that section only when it has something to say, so its ABSENCE is the
   healthy state — and is treated as such rather than as a parse failure.

2. **The manager inventory, as a STRONG expectation.** The dashboard's
   ``## Detected Dependencies`` section enumerates, per manager, every package
   file Renovate extracted from. The expectation is not "pep621 appears
   somewhere" but the exact set:

   * ``pep621`` extracts from all five LOCKED PEP 621 trees — the backend and
     the four service images (#1374) — and from nothing except the two
     lock-less shared libraries named in
     :data:`KNOWN_LOCKLESS_PEP621_FILES`, which are enumerated rather than
     waved through;
   * no second manager (``poetry``, ``pip_requirements``, ``pip-compile``)
     reads anything inside one of those five LOCKED trees — a path-scoped
     disable is what let the side services keep a second manager without a lock
     for months;
   * ``pip-compile`` does not appear at all.

   Note what is deliberately NOT asserted: that ``poetry`` is absent. Measured
   with ``task renovate:dry-run`` (Renovate 44.94.1, 2026-09-16), ``poetry``
   still extracts the two lock-less shared libraries, because
   ``enabled: false`` disables a manager's dependencies without stopping its
   extraction. "``poetry`` must not appear" would have alerted daily on a
   correct repository.

   A weak expectation ("pep621 is present") would have stayed green through the
   whole #1371 episode, because ``pep621`` *was* present — it simply was not the
   only manager reading those files.

3. **The lock beside each package file.** ``rangeStrategy: update-lockfile`` is
   what makes the in-range updates flow at all, and it needs a lock next to the
   ``pyproject.toml``. The dashboard does **not** list lock files (measured on
   the 2026-09-16 body: the ``pep621`` block names package files only), so this
   one fact is read from the checkout on disk instead — and the report says so,
   rather than implying the dashboard proved it.

FAIL LOUD (NFR-018 section 2)
-----------------------------
An empty body, a missing ``## Detected Dependencies`` section, or an unparseable
inventory is NOT "no drift". It raises :class:`DashboardError`; the entry point
prints ``::error::`` and exits non-zero WITHOUT writing the report, so the
workflow run goes red and opens no issue. A determined result — drift or none —
writes the report and exits 0; the alert then lives in a single deduplicated
issue, exactly as ``release-lag.yml`` does it.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPORT_PATH = "renovate-health-report.json"

#: The five PEP 621 trees ``pep621`` must extract from, and nothing else.
#: Order is the reading order of the repository, not an accident: backend first,
#: then the four service images in the order renovate.json5 groups them.
EXPECTED_PEP621_FILES: tuple[str, ...] = (
    "src/backend/pyproject.toml",
    "src/inference-service/pyproject.toml",
    "src/knowledge-service/pyproject.toml",
    "docker/embedding-service/pyproject.toml",
    "docker/reranker-service/pyproject.toml",
)

#: PEP 621 projects that legitimately have NO uv.lock, and why.
#:
#: MEASURED, and the measurement corrected this file twice. The #1383 analysis
#: said ``poetry`` read "exactly the two side-service pyproject.toml"; the real
#: #12 body of 2026-09-16 showed FOUR, with ``src/libs/kp_errortracking`` and
#: ``src/libs/kp_vectordb`` in there too. The first version of this check then
#: assumed those two would move under ``pep621`` once ``poetry`` was disabled
#: repository-wide (#1374). ``task renovate:dry-run`` against this checkout
#: (Renovate 44.94.1, 2026-09-16) says otherwise::
#:
#:     pep621            fileCount 5   ← exactly EXPECTED_PEP621_FILES, each with its uv.lock
#:     poetry            fileCount 2   ← src/libs/kp_errortracking, src/libs/kp_vectordb
#:     pip_requirements  fileCount 2   ← docs/, tools/rag-eval/ only
#:
#: So ``pep621`` claims a ``pyproject.toml`` that has a ``uv.lock`` beside it and
#: ``poetry`` keeps the ones that do not, and ``enabled: false`` disables a
#: manager's DEPENDENCIES without stopping its EXTRACTION — the manager stays in
#: the inventory. A rule of the form "``poetry`` must not appear at all" would
#: therefore have alerted on a correct repository every single day.
#:
#: The two entries are shared LIBRARIES with no image of their own, so there is
#: nothing that "installs from a lock"; giving them one is a decision about the
#: libraries' release shape, not a CI change (the same reason side-services.yml
#: still pip-installs kp_vectordb). Enumerating them keeps the expectation EXACT
#: — these two are allowed under either manager, an unknown file is not —
#: instead of relaxing the rule to "pep621 lists at least the five", which would
#: have stayed green through the whole #1371 episode.
LOCKLESS_PYTHON_PROJECTS: tuple[str, ...] = (
    "src/libs/kp_errortracking/pyproject.toml",
    "src/libs/kp_vectordb/pyproject.toml",
)

#: Backwards-compatible alias: these files are also the ones allowed to appear
#: under ``pep621`` without a lock, should Renovate's manager assignment change.
KNOWN_LOCKLESS_PEP621_FILES: tuple[str, ...] = LOCKLESS_PYTHON_PROJECTS

#: Managers that must not appear in the inventory AT ALL. ``pip-compile`` is the
#: manager whose six silent weeks this whole check exists for; it is no longer
#: configured, and its reappearance would mean a lock reverted to pip-tools.
#:
#: ``poetry`` is deliberately NOT here — see LOCKLESS_PYTHON_PROJECTS for the
#: measurement. It is handled by :data:`MANAGERS_BANNED_FROM_LOCKED_TREES`
#: instead, which is the rule that actually matters: no second manager on a tree
#: that has a lock, because that manager opens source-only pull requests and
#: leaves the lock stale (#1371).
FORBIDDEN_MANAGERS: tuple[str, ...] = ("pip-compile",)

#: Managers that must not read any file inside a LOCKED tree.
MANAGERS_BANNED_FROM_LOCKED_TREES: tuple[str, ...] = ("poetry", "pip_requirements", "pip-compile")

#: Trees that must not be read by ``pip_requirements``. The four service images
#: had their ``requirements.txt`` deleted in #1374; a file reappearing under one
#: of these prefixes means an image is installing without a hash-bearing lock
#: again.
LOCKED_PYTHON_TREES: tuple[str, ...] = tuple(
    str(Path(package_file).parent) + "/" for package_file in EXPECTED_PEP621_FILES
)

_PROBLEMS_HEADING = re.compile(r"^#{1,3}\s*Repository problems\s*$", re.IGNORECASE | re.MULTILINE)
_DETECTED_HEADING = re.compile(r"^#{1,3}\s*Detected Dependencies\s*$", re.IGNORECASE | re.MULTILINE)
_ANY_HEADING = re.compile(r"^#{1,3}\s+\S", re.MULTILINE)
_SEVERITY = re.compile(r"\b(WARN|ERROR)\b")

# `<details><summary>pep621 (1)</summary>` / `<details><summary>src/backend/pyproject.toml (42)</summary>`
_SUMMARY = re.compile(r"<summary>(?P<label>[^<]+?)\s*(?:\((?P<count>\d+)\))?\s*</summary>")


class DashboardError(RuntimeError):
    """The dashboard could not be read. Never "everything is fine"."""


def _section(body: str, heading: re.Pattern[str]) -> str | None:
    """The text between *heading* and the next heading of any level, or None."""
    match = heading.search(body)
    if match is None:
        return None
    rest = body[match.end() :]
    following = _ANY_HEADING.search(rest)
    return rest[: following.start()] if following else rest


def repository_problems(body: str) -> list[str]:
    """Every ``WARN``/``ERROR`` line under ``## Repository problems``.

    Args:
        body: The raw Markdown body of the Dependency Dashboard issue.

    Returns:
        The offending lines, stripped, in document order. Empty when the section
        is absent — Renovate writes it only when it has something to report, so
        "no section" is the healthy state and not a parse failure.
    """
    section = _section(body, _PROBLEMS_HEADING)
    if section is None:
        return []
    return [line.strip() for line in section.splitlines() if _SEVERITY.search(line)]


def manager_inventory(body: str) -> dict[str, list[str]]:
    """Map each manager under ``## Detected Dependencies`` to its package files.

    The section nests ``<details>`` blocks: one per manager, each containing one
    per package file. Nesting depth is what separates the two, and it is tracked
    by counting ``<details>``/``</details>`` rather than by pattern-matching the
    labels — a manager name and a path are both just text, and guessing which is
    which is how a file named like a manager would be silently misfiled.

    Args:
        body: The raw Markdown body of the Dependency Dashboard issue.

    Returns:
        ``{manager: [package file, ...]}``, files in document order.

    Raises:
        DashboardError: The section is missing or contains no manager at all.
    """
    section = _section(body, _DETECTED_HEADING)
    if section is None:
        raise DashboardError(
            "the dashboard body carries no '## Detected Dependencies' section. Either Renovate has not "
            "run against this repository yet, the issue body was edited by hand, or the dashboard format "
            "changed — none of which is evidence that the manager inventory is correct."
        )

    inventory: dict[str, list[str]] = {}
    depth = 0
    current: str | None = None
    for line in section.splitlines():
        summary = _SUMMARY.search(line)
        if summary is not None:
            label = summary.group("label").strip()
            if depth == 0:
                current = label
                inventory.setdefault(current, [])
            elif depth == 1 and current is not None:
                inventory[current].append(label)
        depth += line.count("<details>") - line.count("</details>")
        if depth < 0:  # pragma: no cover — malformed HTML from upstream
            raise DashboardError(f"unbalanced <details> nesting in the dashboard near: {line.strip()!r}")

    if not inventory:
        raise DashboardError(
            "'## Detected Dependencies' contains no manager blocks. An empty inventory is not an empty "
            "problem: it is the same shape as the six silent weeks of the pip-compile manager (#1303)."
        )
    return inventory


def _lock_beside(package_file: str, repo_root: Path) -> bool:
    return (repo_root / package_file).with_name("uv.lock").is_file()


def build_report(body: str, *, repo_root: Path) -> dict[str, Any]:
    """Decide whether the dashboard shows a problem or the inventory drifted.

    Args:
        body: The raw Markdown body of the Dependency Dashboard issue.
        repo_root: Checkout root, used only to look for a ``uv.lock`` beside each
            package file — the dashboard does not list lock files.

    Returns:
        A JSON-serialisable report. ``alert`` is True when anything is wrong;
        ``findings`` carries one human-readable line per problem.

    Raises:
        DashboardError: The body is empty or the inventory cannot be read. An
            undetermined check must not read as a clean one.
    """
    if not body.strip():
        raise DashboardError("the Dependency Dashboard issue body is empty — nothing was measured")

    problems = repository_problems(body)
    inventory = manager_inventory(body)

    findings: list[str] = []

    for problem in problems:
        findings.append(f"Repository problem reported by Renovate: {problem}")

    pep621 = inventory.get("pep621")
    if pep621 is None:
        findings.append(
            "`pep621` is absent from the inventory entirely. It is the ONLY manager that may read the "
            "five pyproject.toml files here; its absence means the backend and every service image are "
            "unmanaged, which is exactly the shape the pip-compile manager failed in for six weeks."
        )
        pep621 = []

    missing = [expected for expected in EXPECTED_PEP621_FILES if expected not in pep621]
    if missing:
        findings.append("`pep621` does not list: " + ", ".join(missing))

    known = set(EXPECTED_PEP621_FILES) | set(LOCKLESS_PYTHON_PROJECTS)
    unexpected = [seen for seen in pep621 if seen not in known]
    if unexpected:
        findings.append(
            "`pep621` lists a file this check does not know about: "
            + ", ".join(unexpected)
            + ". A new Python tree is fine — add it to EXPECTED_PEP621_FILES together with its uv.lock, or "
            "to KNOWN_LOCKLESS_PEP621_FILES with the reason it has none, so the expectation stays exact "
            "instead of quietly widening."
        )

    for manager in FORBIDDEN_MANAGERS:
        if manager in inventory:
            findings.append(
                f"`{manager}` appears in the inventory, reading "
                + ", ".join(inventory[manager] or ["(no files listed)"])
                + ". It is not configured here at all; its presence means a lock reverted to a toolchain "
                "this repository left behind (#1303)."
            )

    for manager in MANAGERS_BANNED_FROM_LOCKED_TREES:
        for package_file in inventory.get(manager, []):
            if package_file in LOCKLESS_PYTHON_PROJECTS:
                continue
            if any(package_file.startswith(tree) for tree in LOCKED_PYTHON_TREES):
                findings.append(
                    f"`{manager}` reads {package_file}, which lives in a tree that installs from a "
                    "hash-bearing uv.lock (#1374). A second manager on a locked tree opens source-only "
                    "pull requests and leaves the lock stale — that is #1371 verbatim."
                )

    # Measured on disk, NOT read from the dashboard — the dashboard lists package
    # files only. Said out loud in the report so nobody credits the dashboard
    # with a fact it never carried.
    locks_missing = [
        package_file for package_file in EXPECTED_PEP621_FILES if not _lock_beside(package_file, repo_root)
    ]
    if locks_missing:
        findings.append(
            "No uv.lock beside: "
            + ", ".join(locks_missing)
            + ". Without one, `rangeStrategy: update-lockfile` has nothing to update and in-range "
            "releases never reach the image (NFR-009 §2.3)."
        )

    return {
        "alert": bool(findings),
        "findings": findings,
        "repository_problems": problems,
        "managers": sorted(inventory),
        "pep621_files": pep621,
        "pip_requirements_files": inventory.get("pip_requirements", []),
        "expected_pep621_files": list(EXPECTED_PEP621_FILES),
        "known_lockless_pep621_files": list(LOCKLESS_PYTHON_PROJECTS),
        "locks_verified_on_disk": [f for f in EXPECTED_PEP621_FILES if f not in locks_missing],
    }


def render(report: dict[str, Any]) -> str:
    """A run-log summary of *report*, for the workflow's step output."""
    if not report["alert"]:
        return (
            "Renovate dashboard healthy: no repository problems, "
            f"pep621 extracts from all {len(report['expected_pep621_files'])} expected trees, "
            f"managers seen: {', '.join(report['managers'])}."
        )
    return "Renovate dashboard drift:\n" + "\n".join(f"  - {finding}" for finding in report["findings"])


def main(argv: list[str] | None = None, *, body: str | None = None, repo_root: Path | None = None) -> int:
    """Read the dashboard body, write the report, and exit 0 on a determined result.

    Args:
        argv: Optional ``[report_path]``; defaults to :data:`REPORT_PATH`.
        body: Injection point for the dashboard body (tests pass a fixture).
            Falls back to ``$RENOVATE_DASHBOARD_BODY``.
        repo_root: Injection point for the checkout root.

    Returns:
        0 on a determined result — including a drifted one, which is reported
        through the issue rather than through the run status.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) > 1:
        print("usage: check_renovate_dashboard.py [report.json]", file=sys.stderr)
        return 2
    report_path = arguments[0] if arguments else REPORT_PATH

    resolved_body = body if body is not None else os.environ.get("RENOVATE_DASHBOARD_BODY", "")
    resolved_root = repo_root or Path(os.environ.get("GITHUB_WORKSPACE") or Path(__file__).resolve().parents[2])

    report = build_report(resolved_body, repo_root=resolved_root)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    print(render(report))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DashboardError as exc:
        # Loud, and no report written: an undetermined check is not a clean check,
        # and a transient API blip must not spam the tracker with an issue.
        print(f"::error::renovate dashboard health could not be determined: {exc}", file=sys.stderr)
        sys.exit(1)
