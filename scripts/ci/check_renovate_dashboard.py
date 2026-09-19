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

   * ``pep621`` extracts from all eight LOCKED PEP 621 trees — the backend,
     the four service images (#1374), the two shared libraries (#1464) and the
     E2E suite (#1509) — and from nothing else.
     :data:`KNOWN_LOCKLESS_PEP621_FILES` is EMPTY since #1464: a Python tree
     without a lock is a finding, not an allowance;
   * no second manager (``poetry``, ``pip_requirements``, ``pip-compile``)
     reads anything inside one of those seven LOCKED trees — a path-scoped
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

4. **Every Python install goes through hashes** (#1509), also read from disk,
   in the two spellings that exist here: a ``requirements*.txt`` whose entries
   carry no ``--hash=`` (:func:`unhashed_requirements_installs`) and a
   ``Dockerfile`` that pip-installs inline, with no requirement list at all for
   the first sweep to find (:func:`dockerfile_python_installs`). Both were
   report-only or absent before; the decision per file — lock, hash-pin in
   place, argued exception — is what turned them into findings, with
   :data:`KNOWN_UNHASHED_REQUIREMENTS` holding the one argued exception.

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

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPORT_PATH = "renovate-health-report.json"

#: The eight PEP 621 trees ``pep621`` must extract from, and nothing else.
#: Order is the reading order of the repository, not an accident: backend first,
#: then the four service images in the order renovate.json5 groups them, then the
#: two shared libraries locked by #1464, then the E2E suite locked by #1509.
EXPECTED_PEP621_FILES: tuple[str, ...] = (
    "src/backend/pyproject.toml",
    "src/inference-service/pyproject.toml",
    "src/knowledge-service/pyproject.toml",
    "docker/embedding-service/pyproject.toml",
    "docker/reranker-service/pyproject.toml",
    "src/libs/kp_vectordb/pyproject.toml",
    "src/libs/kp_errortracking/pyproject.toml",
    "tests/e2e/pyproject.toml",
)

#: PEP 621 projects that legitimately have NO uv.lock. EMPTY, and that is the
#: point (#1464).
#:
#: It used to hold ``src/libs/kp_vectordb`` and ``src/libs/kp_errortracking``. The
#: reason recorded for the allowance was that a shared library has no image of its
#: own, so there is nothing that "installs from a lock" — true about images and
#: false about installs: ``side-services.yml`` ran ``pip install -e '.[dev]'`` for
#: kp_vectordb on a runner, and NFR-009 §2.3 is a property of the install. Both
#: trees now carry a hash-bearing uv.lock and sit in
#: :data:`EXPECTED_PEP621_FILES`.
#:
#: MEASURED after the change, ``task renovate:dry-run`` (Renovate 44.103.2,
#: 2026-09-19, #1509)::
#:
#:     pep621            fileCount 8   ← exactly EXPECTED_PEP621_FILES
#:     poetry            absent        ← it only ever held the two lockless libs
#:     pip_requirements  fileCount 2   ← docs/, tools/rag-eval/
#:
#: ``poetry`` leaving the inventory entirely is a CONSEQUENCE, not a goal: it
#: extracted those two trees precisely because they had no lock. The rule that
#: matters is still :data:`MANAGERS_BANNED_FROM_LOCKED_TREES` — no second manager
#: on a tree that has a lock — and it now covers seven trees instead of five.
#:
#: KEEPING THIS EMPTY IS THE RULE, not an accident of today's tree. An allowance
#: register is how a workaround becomes the design (CI spec §H): a new PEP 621
#: tree gets a lock, or the pull request that adds it argues for an entry here in
#: writing. :func:`lockless_python_trees` measures the same property against the
#: FILESYSTEM rather than against Renovate's inventory, so a tree Renovate does
#: not extract at all — the failure mode an inventory check cannot see — is a
#: finding too.
#:
#: THE SCOPE IS PEP 621, AND THAT IS NOW SAID OUT LOUD (#1491 review). The
#: earlier wording claimed "every Python tree"; the sweep only ever read
#: ``pyproject.toml``, so three ``requirements.txt`` — ``tests/e2e/``,
#: ``docs/`` and ``tools/rag-eval/`` — installed with neither a lock nor hashes
#: and no measurement said so. A claim wider than its measuring tool is the
#: NFR-018 §1 shape, so both were brought together: the claim was narrowed and
#: :func:`unhashed_requirements_installs` was added to report the remainder.
#:
#: #1509 then decided that remainder, one outcome per file: ``tests/e2e/`` was
#: LOCKED (it is a built image, so it joins the list above),  ``docs/`` was
#: HASH-PINNED IN PLACE, and ``tools/rag-eval/`` is the one argued exception in
#: :data:`KNOWN_UNHASHED_REQUIREMENTS`. Everything else is a finding now, not a
#: report.
LOCKLESS_PYTHON_PROJECTS: tuple[str, ...] = ()

#: Backwards-compatible alias: these files are also the ones allowed to appear
#: under ``pep621`` without a lock, should Renovate's manager assignment change.
KNOWN_LOCKLESS_PEP621_FILES: tuple[str, ...] = LOCKLESS_PYTHON_PROJECTS

#: Files that must be OBSERVED by a named manager, keyed by that manager (#1464).
#:
#: `config:recommended` pulls in `:ignoreModulesAndTests`, whose `ignorePaths`
#: includes ``**/tests/**``. That rule is written for a repository whose
#: ``tests/`` holds fixtures; here it also swallowed ``tests/e2e/``, which is a
#: shipped artefact — the image the nightly E2E matrix and the ``E2E smoke`` lane
#: build. Its selenium, axe-core and base-image versions were unmanaged, and
#: nothing said so: an ignored path produces no warning, no dashboard entry and
#: no finding. ``renovate.json5`` now restates ``ignorePaths`` without
#: ``**/tests/**``.
#:
#: This is the tripwire for that override. Absence is invisible by construction,
#: so it has to be asserted from the other side: these three files must APPEAR in
#: the inventory. Measured with ``task renovate:dry-run`` (Renovate 44.94.1,
#: 2026-09-17) before and after the override — ``pip_requirements`` 2 -> 3 files,
#: ``npm`` 1 -> 2, ``dockerfile`` 8 -> 9, and nothing else changed.
#: The Python half moved from ``pip_requirements`` to ``pep621`` in #1509:
#: ``tests/e2e/requirements.txt`` was replaced by a ``pyproject.toml`` with a
#: hash-bearing ``uv.lock``, so the tripwire for it is its entry in
#: :data:`EXPECTED_PEP621_FILES` — and, in the other direction,
#: :data:`MANAGERS_BANNED_FROM_LOCKED_TREES`, which now forbids
#: ``pip_requirements`` inside ``tests/e2e/`` because that prefix became a
#: LOCKED tree. A requirements.txt reappearing there is a finding rather than a
#: second manager nobody notices.
EXPECTED_OBSERVED_FILES: dict[str, tuple[str, ...]] = {
    "npm": ("tests/e2e/package.json",),
    "dockerfile": ("tests/e2e/Dockerfile",),
}

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


#: Directories the pyproject sweep never descends into. Build and environment
#: artefacts, not source: a virtualenv contains other projects' pyproject.toml by
#: the hundred, and reporting those would drown the finding this check exists for.
#: ``site`` is the MkDocs build output (``.gitignore:55``), and it is on this
#: list because of a measurement during #1509, not on principle: after a local
#: ``task docs:build`` the tree carries ``site/requirements.txt`` — MkDocs copies
#: every non-Markdown file under ``docs/`` into the built site — and the dry-run
#: duly reported ``pip_requirements fileCount 3`` where a clean checkout has 2.
#: CI checks out clean and never saw it; a developer running the check after a
#: docs build would have got a finding about a build artefact.
_SWEEP_EXCLUDED = frozenset(
    {
        ".git",
        ".venv",
        ".venv-docs",
        "node_modules",
        "site",
        "site-packages",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
    }
)


#: The shapes a pip requirement list takes here, and the two the #1509 class
#: sweep added after asking for a spelling the first one misses: ``.pip`` is
#: pip's own second extension (and Renovate's ``pip_requirements`` matches it
#: too), and a list under a ``requirements/`` DIRECTORY — ``requirements/dev.txt``
#: — is the common layout that ``requirements*.txt`` never sees because the name
#: does not start with the word. ``constraints*.txt`` is a list pip installs from
#: with ``-c`` in exactly the same way.
#:
#: Measured on 2026-09-19: widening the sweep from one pattern to four changes
#: nothing about this checkout (still the single argued exception) — which is the
#: point. A pattern added the day a matching file appears is a pattern added too
#: late.
_REQUIREMENT_LIST_PATTERNS: tuple[str, ...] = (
    "requirements*.txt",
    "requirements*.pip",
    "requirements/*.txt",
    "constraints*.txt",
)


#: The ONE ``requirements*.txt`` that installs without hashes, with its argument
#: in writing. Every other one is a finding (:func:`unhashed_requirements_installs`).
#:
#: #1509 decided the three this register used to hold, one outcome per file:
#:
#: * ``tests/e2e/requirements.txt`` — LOCKED. It is installed into a BUILT image
#:   (``tests/e2e/Dockerfile``, the ``E2E smoke`` lane and the nightly matrix),
#:   which is exactly the property NFR-009 §2.3 is about, so it became a
#:   ``pyproject.toml`` + ``uv.lock`` like the other seven trees and the
#:   Dockerfile now runs ``uv sync --locked``;
#: * ``docs/requirements.txt`` — HASH-PINNED IN PLACE. It is not built into an
#:   image but it IS installed by a delivery lane
#:   (``release-cd-deliver-docs.yml`` through ``reusable-mkdocs.yaml``, twice:
#:   once on the runner and once inside ``mhausenblas/mkdocs-deploy-gh-pages``),
#:   so the artefacts it fetches decide what the published site is built from.
#:   ``docs/requirements.in`` keeps the human-edited ranges and
#:   ``docs/requirements.txt`` is the compiled, fully hashed set (``task
#:   docs:lock``). ``pip install -r`` switches itself into hash-checking mode as
#:   soon as one hash is present, so the pin is enforced by pip rather than by a
#:   convention;
#: * ``tools/rag-eval/requirements.txt`` — OUT OF SCOPE, ARGUED. It is a local
#:   analysis tool (``tools/rag-eval/README.md``, ``rag_eval.ipynb``): no image
#:   builds it, no workflow installs it, no delivered artefact contains it. The
#:   reason is recorded in the file itself, not only here and not only in the
#:   pull request, so the next reader of that file finds it. An entry here is a
#:   claim that nothing DELIVERED depends on the list — if a lane ever installs
#:   it, the entry is wrong and must go, not grow a second friend.
KNOWN_UNHASHED_REQUIREMENTS: tuple[str, ...] = ("tools/rag-eval/requirements.txt",)


def unhashed_requirements_installs(repo_root: Path) -> list[str]:
    """Every ``requirements*.txt`` with no hash-bearing lock beside it, sorted.

    A FINDING since #1509, for everything outside
    :data:`KNOWN_UNHASHED_REQUIREMENTS`. It was report-only for one release
    cycle, deliberately: the three lists it found predated #1464 and reddening
    the lane for a decision nobody had made would have failed a correct
    repository. The decision has now been made per file — lock, hash-pin in
    place, argued exception — so the default flips. A reported-only category is
    how a workaround becomes the design (CI spec §H); the report existed to give
    the remainder a size, not a home.

    "Hash-bearing" means the entries carry ``--hash=`` — pip's own form, so a
    list that is pinned by hash is not reported as if it were not.

    A ``uv.lock`` IN THE SAME DIRECTORY does NOT excuse it, and that exemption
    used to exist. It was removed by the red-first check of #1509 itself:
    restoring the pre-#1509 ``tests/e2e/requirements.txt`` beside the new
    ``tests/e2e/uv.lock`` produced a GREEN run, i.e. the proof that the new gate
    reddens did not redden. A directory holding both is not a locked tree — it
    is two sources of truth for one install, and ``pip install -r`` reads the
    one without hashes.

    Args:
        repo_root: Checkout root to sweep.

    Returns:
        The requirement lists installed without hash verification, sorted —
        including the argued exception, which :func:`build_report` subtracts.
        Returning it keeps the register auditable: an entry that no longer
        matches a file on disk is visible instead of inert.
    """
    found = []
    for pattern in _REQUIREMENT_LIST_PATTERNS:
        for requirements in repo_root.rglob(pattern):
            relative = requirements.relative_to(repo_root)
            if _SWEEP_EXCLUDED.intersection(relative.parts):
                continue
            if "--hash=" in requirements.read_text(encoding="utf-8", errors="replace"):
                continue
            found.append(relative.as_posix())
    return sorted(set(found))


#: A Python package install inside a Dockerfile, in every spelling this
#: repository could plausibly use: ``pip install``, ``pip3 install``,
#: ``python -m pip install``, ``python3.14 -m pip install`` and ``uv pip
#: install``. NOT ``uv sync``, which is the locked form and the point.
#:
#: The class sweep behind #1509 asked the question this pattern exists for:
#: name a spelling of "installs Python without a hash-bearing lock" that a
#: ``requirements*.txt`` sweep does not see. A Dockerfile that names its
#: packages INLINE is one — it has no requirement list at all, so
#: :func:`unhashed_requirements_installs` is blind to it by construction, and
#: an image is the artefact NFR-009 §2.3 is most about.
_DOCKERFILE_PIP_INSTALL = re.compile(
    r"(?<![\w.-])(?:(?:python[\d.]*\s+-m\s+)?pip[\d.]*|uv\s+pip)\s+install\b",
    re.IGNORECASE,
)


def dockerfile_python_installs(repo_root: Path) -> list[str]:
    """Every ``Dockerfile`` line that installs Python packages outside a lock.

    COMMENTS ARE STRIPPED FIRST, and that is not cosmetic: three Dockerfiles
    here carry prose saying what they used to do ("it used to be an unpinned
    ``pip install`` outside any lock"). A sweep reading raw text would report
    the explanation of a fixed defect as the defect — the exact failure this
    repository has paid for before, prose answering for configuration.

    Args:
        repo_root: Checkout root to sweep.

    Returns:
        ``path:line`` for each offending instruction, sorted. Empty is the
        state #1374 and #1509 established: every image installs with
        ``uv sync --locked``.
    """
    found = []
    for dockerfile in repo_root.rglob("Dockerfile*"):
        relative = dockerfile.relative_to(repo_root)
        if _SWEEP_EXCLUDED.intersection(relative.parts) or not dockerfile.is_file():
            continue
        for number, line in enumerate(dockerfile.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if _DOCKERFILE_PIP_INSTALL.search(line):
                found.append(f"{relative.as_posix()}:{number}")
    return sorted(found)


def lockless_python_trees(repo_root: Path) -> list[str]:
    """Every ``pyproject.toml`` in the checkout with no ``uv.lock`` beside it.

    Measured against the FILESYSTEM, deliberately, because the inventory check
    above can only see what Renovate extracted. A Python tree that no manager
    reads at all is invisible there and is exactly the worse case: unlocked AND
    unobserved. Paths are returned relative to *repo_root*, sorted, so the
    finding reads the same on every machine.

    Args:
        repo_root: Checkout root to sweep.

    Returns:
        The offending package files, sorted. Empty when every Python tree is
        locked, which is the state #1464 established and this keeps.
    """
    found = []
    for pyproject in repo_root.rglob("pyproject.toml"):
        relative = pyproject.relative_to(repo_root)
        if _SWEEP_EXCLUDED.intersection(relative.parts):
            continue
        if not pyproject.with_name("uv.lock").is_file():
            found.append(relative.as_posix())
    return sorted(found)


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
            "seven pyproject.toml files here; its absence means the backend, every service image and both "
            "shared libraries are "
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

    for manager, package_files in EXPECTED_OBSERVED_FILES.items():
        seen = inventory.get(manager, [])
        unobserved = [package_file for package_file in package_files if package_file not in seen]
        if unobserved:
            findings.append(
                f"`{manager}` does not read "
                + ", ".join(unobserved)
                + ". These are shipped artefacts that an inherited `ignorePaths` rule used to swallow "
                "(#1464); an ignored path produces no warning and no dashboard entry, so its absence is "
                "only visible from this side. Check the `ignorePaths` override in renovate.json5."
            )

    # The same property, reached from the filesystem instead of from the
    # dashboard (#1464). The inventory check above can only judge trees Renovate
    # extracted; this one also catches a tree no manager reads, which is the
    # worse case and the invisible one.
    unlocked = [tree for tree in lockless_python_trees(repo_root) if tree not in LOCKLESS_PYTHON_PROJECTS]
    if unlocked:
        findings.append(
            "Python tree without a uv.lock beside its pyproject.toml: "
            + ", ".join(unlocked)
            + ". Every PEP 621 tree in this repository installs from a hash-bearing lock (NFR-009 §2.3); "
            "run `uv lock` in that directory and add the file to EXPECTED_PEP621_FILES. "
            "LOCKLESS_PYTHON_PROJECTS is empty on purpose and an entry there needs the argument in "
            "writing — an allowance register is how a workaround becomes the design (CI spec §H)."
        )

    # A FINDING since #1509, no longer a report. Every requirement list that is
    # installed anywhere now resolves through hashes, except the one argued
    # entry in KNOWN_UNHASHED_REQUIREMENTS — so a new unhashed list is a
    # regression against a decided state rather than an old debt.
    unhashed = unhashed_requirements_installs(repo_root)
    undecided = [requirements for requirements in unhashed if requirements not in KNOWN_UNHASHED_REQUIREMENTS]
    if undecided:
        findings.append(
            "Installed without hash verification: "
            + ", ".join(undecided)
            + ". A requirement list resolves whatever the index serves that minute (NFR-009 §2.3). Give it "
            "a uv.lock like the eight PEP 621 trees, or compile it with `--generate-hashes` in place "
            "(#1509 did both, one per file). KNOWN_UNHASHED_REQUIREMENTS takes an entry only with the "
            "argument that nothing delivered installs it, written into the file itself."
        )

    # The same property, reached through the spelling the sweep above cannot
    # see: a Dockerfile that names its packages inline has no requirement list
    # at all (#1509 class sweep).
    dockerfile_installs = dockerfile_python_installs(repo_root)
    if dockerfile_installs:
        findings.append(
            "Dockerfile installs Python packages outside a lock: "
            + ", ".join(dockerfile_installs)
            + ". Every image here installs with `uv sync --locked`, which verifies each artifact against "
            "its recorded hash; a `pip install` in a build stage ships whatever the index served during "
            "that build (NFR-009 §2.3)."
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
        "lockless_python_trees": lockless_python_trees(repo_root),
        # The full sweep, including the argued exception; `findings` above
        # carries only what is NOT in KNOWN_UNHASHED_REQUIREMENTS, so the report
        # stays auditable while the lane reddens (#1509).
        "unhashed_requirements_installs": unhashed,
        "undecided_unhashed_requirements": undecided,
        "dockerfile_python_installs": dockerfile_installs,
        "observed_files": {manager: inventory.get(manager, []) for manager in EXPECTED_OBSERVED_FILES},
    }


def render(report: dict[str, Any]) -> str:
    """A run-log summary of *report*, for the workflow's step output."""
    if not report["alert"]:
        unhashed = report.get("unhashed_requirements_installs") or []
        # Printed on a GREEN run too, which is the point: the argued exception
        # of #1509 is the only requirement list left without hashes, and an
        # allowance that appears solely in JSON is one nobody re-reads.
        remainder = (
            f" Installed without hash verification (argued exception, see "
            f"KNOWN_UNHASHED_REQUIREMENTS): {', '.join(unhashed)}."
            if unhashed
            else ""
        )
        return (
            "Renovate dashboard healthy: no repository problems, "
            f"pep621 extracts from all {len(report['expected_pep621_files'])} expected trees, "
            f"managers seen: {', '.join(report['managers'])}." + remainder
        )
    return "Renovate dashboard drift:\n" + "\n".join(f"  - {finding}" for finding in report["findings"])


def _read_body_file(path: str) -> str:
    """The dashboard body from *path*, or a loud :class:`DashboardError`.

    A missing or unreadable body file is an UNDETERMINED run, never a clean one:
    returning "" here would parse as an empty dashboard and, worse, a caller that
    swallowed the error would report "no drift" having read nothing.
    """
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise DashboardError(
            f"--body-file {path} could not be read ({exc.strerror or exc}). The dashboard body was never "
            "fetched, so nothing was measured."
        ) from exc


def _parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="check_renovate_dashboard.py",
        description="Compare Renovate's Dependency Dashboard against the expected manager inventory.",
    )
    parser.add_argument(
        "report_path",
        nargs="?",
        default=REPORT_PATH,
        help=f"where to write the JSON report (default: {REPORT_PATH})",
    )
    parser.add_argument(
        "--body-file",
        dest="body_file",
        default=None,
        help=(
            "read the dashboard body from this file instead of $RENOVATE_DASHBOARD_BODY. This is how CI "
            "passes it: the body is ~900 lines and grows, and a single argv/env string is capped by "
            "MAX_ARG_STRLEN (128 KiB per argument on Linux), so the env route would start failing with "
            "E2BIG on a day nothing here changed."
        ),
    )
    return parser.parse_args(sys.argv[1:] if argv is None else argv)


def main(argv: list[str] | None = None, *, body: str | None = None, repo_root: Path | None = None) -> int:
    """Read the dashboard body, write the report, and exit 0 on a determined result.

    Args:
        argv: Optional ``[--body-file PATH] [report.json]``; defaults to
            :data:`REPORT_PATH` for the report.
        body: Injection point for the dashboard body (tests pass a fixture).
            Takes precedence over both ``--body-file`` and the environment.
        repo_root: Injection point for the checkout root.

    Returns:
        0 on a determined result — including a drifted one, which is reported
        through the issue rather than through the run status.

    Raises:
        DashboardError: ``--body-file`` names a file that cannot be read, or the
            body that was resolved cannot be parsed.
    """
    arguments = _parse_arguments(argv)
    report_path = arguments.report_path

    # Precedence: explicit injection (tests) > --body-file (CI) > environment
    # (the ad-hoc local fallback the CI lane no longer uses).
    if body is not None:
        resolved_body = body
    elif arguments.body_file is not None:
        resolved_body = _read_body_file(arguments.body_file)
    else:
        resolved_body = os.environ.get("RENOVATE_DASHBOARD_BODY", "")
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
