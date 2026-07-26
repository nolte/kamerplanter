#!/usr/bin/env python3
"""Check that every BDD scenario traces back to a declared test case.

Run via ``task test:e2e:traceability``.

`spec/project/behavior-driven-development/` makes the scenario-to-test-case link
a hard gate: every scenario is derived *from* a TC-ID by construction, so a
scenario whose ``@TC-<id>`` tag resolves to nothing — or that carries no tag at
all — is a defect, not a warning. Without this check the tag is a bare string
that nobody verifies.

Two defect classes fail the run (exit 1):

* **orphan tag** — a ``@TC-<id>`` in a ``.feature`` that no test-case document
  under ``spec/e2e-testcases/`` declares as a heading.
* **untagged scenario** — a scenario carrying no TC-ID tag at all.

The reverse direction is deliberately **not** a defect: a declared test case
without a scenario is simply not automated yet (one of ~90 REQ-004 cases is a
BDD scenario today). Those are reported as an informational count only, so the
check does not fail permanently from day one.

Neither of the two shapes this check depends on is restated here; both are
loaded from the single source of truth that the test run itself uses, so the
check and the suite cannot drift apart:

* the strict TC-ID pattern comes from
  ``tests/e2e/protocol_plugin.py::TC_ID_PATTERN``, which ``tests/e2e/conftest.py``
  already shares;
* the classification of a Gherkin source line — tag line, comment, docstring
  payload, content — comes from ``tests/e2e/_gherkin.py``, which
  ``tests/e2e/conftest.py`` also uses to register its markers.

Standard library only: it must run anywhere the repository is checked out,
without installing a Gherkin parser and without the E2E extras. Both SSOT
modules are therefore loaded *by path* (see :func:`load_tc_id_pattern` and
:func:`load_gherkin_module`) and neither pulls in Selenium or pytest.

The parse below covers the subset of Gherkin this repository writes (tags,
``Feature``, ``Rule``, ``Background``, ``Scenario``, ``Scenario Outline``,
``Examples``, docstrings, and the ``# language:`` header). Only the keyword
dialect is this script's own business — the shared module deliberately stops
short of it.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FEATURE_ROOTS = ("tests/e2e/features",)
DEFAULT_SPEC_ROOTS = ("spec/e2e-testcases",)
PROTOCOL_PLUGIN = REPO_ROOT / "tests" / "e2e" / "protocol_plugin.py"
GHERKIN_MODULE = REPO_ROOT / "tests" / "e2e" / "_gherkin.py"

EXIT_OK = 0
EXIT_DEFECTS = 1
EXIT_USAGE = 2

_LANGUAGE_HEADER = re.compile(r"^\s*#\s*language\s*:\s*([A-Za-z-]+)\s*$")

# A test case in the spec is a Markdown heading of level 2..6 opening with its
# ID: ``## TC-004-092: <title>`` or ``### TC-REQ-034-001: <title>``. Level-1
# headings are document titles (``# TC-REQ-009 — …``) and declare no case.
_SPEC_HEADING = re.compile(
    r"^\s{0,3}#{2,6}\s+(TC-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)\s*[:—–-]?\s*(.*)$"
)
# A heading only declares a case if its ID ends in a case number; this keeps
# section headings such as ``## TC-REQ-004`` out of the index.
_CASE_NUMBER_SUFFIX = re.compile(r"-\d{2,}$")
_MARKDOWN_FENCE = re.compile(r"^\s*(```|~~~)")

# Gherkin keyword dialects. Only the structural keywords are needed; step
# keywords are irrelevant to traceability. Longest-first matching is applied at
# lookup time, so ``Scenario Outline`` wins over ``Scenario`` and ``Beispiele``
# over ``Beispiel``.
_DIALECTS: dict[str, dict[str, tuple[str, ...]]] = {
    "en": {
        "feature": ("Feature", "Business Need", "Ability"),
        "rule": ("Rule",),
        "background": ("Background",),
        "scenario": ("Scenario Outline", "Scenario Template", "Scenario", "Example"),
        "examples": ("Examples", "Scenarios"),
    },
    "de": {
        "feature": ("Funktionalität", "Funktionalitaet", "Funktion", "Feature"),
        "rule": ("Regel", "Rule"),
        "background": ("Grundlage", "Hintergrund", "Voraussetzungen", "Vorbedingungen"),
        "scenario": ("Szenariogrundriss", "Szenarien", "Szenario", "Beispiel"),
        "examples": ("Beispiele",),
    },
}
_FALLBACK_DIALECT = "en"


class TraceabilityError(RuntimeError):
    """Raised when the check cannot run at all (missing roots, unreadable SSOT)."""


@dataclass(frozen=True)
class Scenario:
    """A Gherkin scenario with its effective tags (feature + rule + own)."""

    name: str
    path: Path
    line: int
    tags: tuple[str, ...]
    tc_ids: tuple[str, ...]


@dataclass(frozen=True)
class SpecCase:
    """A test case declared as a heading in a ``spec/e2e-testcases/`` document."""

    tc_id: str
    title: str
    path: Path
    line: int


@dataclass
class _ScenarioDraft:
    """Mutable scenario under construction — ``Examples:`` tags arrive later."""

    name: str
    line: int
    tags: list[str] = field(default_factory=list)


# ── Shared single sources of truth, loaded by path ───────────────────────────


def _load_module_by_path(module_name: str, path: Path, purpose: str) -> ModuleType:
    """Execute a module from an explicit file path and return it.

    ``tests/e2e/`` is not an importable package, so a plain ``import`` is not an
    option — and pulling the repository root onto ``sys.path`` would risk
    dragging in the E2E ``conftest.py`` (and with it Selenium) on a checkout
    that has no E2E extras installed. Loading by path keeps the check runnable
    on a bare clone; it is the same mechanism ``tests/e2e/conftest.py`` uses.

    Args:
        module_name: Private name to register the module under. It must not
            collide with the name the module carries under pytest.
        path: The ``.py`` file to execute.
        purpose: What the caller needs the module for, used in the error text.

    Returns:
        The executed module.

    Raises:
        TraceabilityError: If the file is missing or cannot be loaded.
    """
    if not path.is_file():
        raise TraceabilityError(f"cannot resolve {purpose}: {path} does not exist")
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise TraceabilityError(f"cannot load {path} as a Python module")
    module = importlib.util.module_from_spec(spec)
    # Both modules define dataclasses, and ``@dataclass`` resolves its own module
    # via ``sys.modules`` — so the module must be registered *before* it runs
    # (same reason conftest.py registers it).
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_tc_id_pattern(plugin_path: Path = PROTOCOL_PLUGIN) -> re.Pattern[str]:
    """Import the canonical strict TC-ID pattern from the e2e protocol plugin.

    The plugin imports only standard-library modules at import time, so this is
    side-effect free.

    Args:
        plugin_path: Path to ``tests/e2e/protocol_plugin.py``.

    Returns:
        The compiled ``TC_ID_PATTERN`` owned by the plugin.

    Raises:
        TraceabilityError: If the plugin is missing or exposes no pattern.
    """
    module = _load_module_by_path(
        "_bdd_traceability_protocol_plugin", plugin_path, "the canonical TC-ID pattern"
    )
    pattern = getattr(module, "TC_ID_PATTERN", None)
    if not isinstance(pattern, re.Pattern):
        raise TraceabilityError(f"{plugin_path} exposes no TC_ID_PATTERN — cannot validate tags")
    return pattern


@lru_cache(maxsize=1)
def load_gherkin_module(module_path: Path = GHERKIN_MODULE) -> ModuleType:
    """Import the shared Gherkin line classifier used by the E2E suite.

    ``tests/e2e/_gherkin.py`` owns the tag-line shape and the docstring state
    machine that this script used to duplicate. It is standard-library only, so
    loading it costs nothing and drags in no E2E dependency. The result is
    cached because :func:`parse_feature_file` is called once per ``.feature``.

    Args:
        module_path: Path to ``tests/e2e/_gherkin.py``.

    Returns:
        The executed module, exposing ``iter_lines`` and ``GherkinLineKind``.

    Raises:
        TraceabilityError: If the module is missing or exposes neither symbol.
    """
    module = _load_module_by_path(
        "_bdd_traceability_gherkin", module_path, "the canonical Gherkin line classifier"
    )
    missing = [name for name in ("iter_lines", "GherkinLineKind") if not hasattr(module, name)]
    if missing:
        raise TraceabilityError(
            f"{module_path} exposes no {', '.join(missing)} — cannot classify feature lines"
        )
    return module


# ── Gherkin parsing ──────────────────────────────────────────────────────────


def _dialect_for(lines: list[str]) -> dict[str, tuple[str, ...]]:
    """Pick the keyword dialect from a leading ``# language:`` header."""
    for raw in lines:
        stripped = raw.strip()
        if not stripped:
            continue
        match = _LANGUAGE_HEADER.match(stripped)
        if match:
            language = match.group(1).lower().split("-")[0]
            return _DIALECTS.get(language, _DIALECTS[_FALLBACK_DIALECT])
        if not stripped.startswith("#"):
            break
    return _DIALECTS[_FALLBACK_DIALECT]


def _keyword_of(line: str, dialect: dict[str, tuple[str, ...]]) -> tuple[str, str] | None:
    """Classify a Gherkin line as ``(kind, title)`` — or None if it is not a keyword line.

    Args:
        line: The stripped source line.
        dialect: Keyword table for the file's language.

    Returns:
        A ``(kind, title)`` pair with kind in ``feature``/``rule``/``background``/
        ``scenario``/``examples``, or None.
    """
    candidates = [
        (keyword, kind) for kind, keywords in dialect.items() for keyword in keywords
    ]
    # Longest keyword first: "Scenario Outline" must not be read as "Scenario".
    for keyword, kind in sorted(candidates, key=lambda pair: -len(pair[0])):
        prefix = f"{keyword}:"
        if line.startswith(prefix):
            return kind, line[len(prefix) :].strip()
    return None


def parse_feature_file(path: Path, tc_pattern: re.Pattern[str]) -> list[Scenario]:
    """Extract every scenario and its effective tags from one ``.feature`` file.

    Feature-level and rule-level tags are inherited by the scenarios below them,
    matching how pytest-bdd turns tags into markers. Tags on an ``Examples:``
    table are attributed to the enclosing scenario outline.

    Line classification — what is a tag line, a comment, or opaque docstring
    payload — is delegated to the shared ``tests/e2e/_gherkin`` module; only the
    keyword dialect is interpreted here.

    Args:
        path: The ``.feature`` file to read.
        tc_pattern: Canonical strict TC-ID pattern.

    Returns:
        The scenarios in source order.

    Raises:
        TraceabilityError: If the shared Gherkin classifier cannot be loaded.
    """
    gherkin = load_gherkin_module()
    kinds = gherkin.GherkinLineKind
    # Docstring payload may contain anything — a "#", a tag block, a line that
    # looks like a keyword — and blanks and comments carry no structure either.
    ignored_kinds = frozenset({kinds.DOCSTRING, kinds.BLANK, kinds.COMMENT})

    lines = path.read_text(encoding="utf-8").splitlines()
    dialect = _dialect_for(lines)

    scenarios: list[Scenario] = []
    pending_tags: list[str] = []
    feature_tags: tuple[str, ...] = ()
    rule_tags: tuple[str, ...] = ()
    draft: _ScenarioDraft | None = None

    def close_draft() -> None:
        nonlocal draft
        if draft is None:
            return
        tags = tuple(dict.fromkeys(draft.tags))
        scenarios.append(
            Scenario(
                name=draft.name,
                path=path,
                line=draft.line,
                tags=tags,
                tc_ids=tuple(tag for tag in tags if tc_pattern.fullmatch(tag)),
            )
        )
        draft = None

    for line in gherkin.iter_lines(lines):
        if line.kind in ignored_kinds:
            continue

        if line.is_tag:
            pending_tags.extend(line.tags)
            continue

        keyword = _keyword_of(line.stripped, dialect)
        if keyword is None:
            # Steps, tables, free-form description: a tag block never survives
            # non-keyword content.
            pending_tags.clear()
            continue

        kind, title = keyword
        if kind == "feature":
            close_draft()
            feature_tags = tuple(pending_tags)
            rule_tags = ()
        elif kind == "rule":
            close_draft()
            rule_tags = tuple(pending_tags)
        elif kind == "background":
            close_draft()
        elif kind == "scenario":
            close_draft()
            draft = _ScenarioDraft(
                name=title,
                line=line.number,
                tags=[*feature_tags, *rule_tags, *pending_tags],
            )
        elif kind == "examples" and draft is not None:
            draft.tags.extend(pending_tags)
        pending_tags.clear()

    close_draft()
    return scenarios


def collect_scenarios(roots: list[Path], tc_pattern: re.Pattern[str]) -> list[Scenario]:
    """Parse every ``.feature`` file below the given roots.

    Args:
        roots: Directories (or single ``.feature`` files) to scan.
        tc_pattern: Canonical strict TC-ID pattern.

    Returns:
        All scenarios found, ordered by file then source line.

    Raises:
        TraceabilityError: If a root does not exist.
    """
    scenarios: list[Scenario] = []
    for root in roots:
        if root.is_file():
            scenarios.extend(parse_feature_file(root, tc_pattern))
            continue
        if not root.is_dir():
            raise TraceabilityError(f"feature root does not exist: {root}")
        for feature_file in sorted(root.glob("**/*.feature")):
            scenarios.extend(parse_feature_file(feature_file, tc_pattern))
    return scenarios


# ── Test-case specification index ────────────────────────────────────────────


def parse_spec_document(path: Path) -> list[SpecCase]:
    """Extract the declared test cases from one ``spec/e2e-testcases`` document."""
    cases: list[SpecCase] = []
    in_fence = False
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if _MARKDOWN_FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _SPEC_HEADING.match(raw)
        if match is None:
            continue
        tc_id, title = match.group(1), match.group(2).strip()
        if not _CASE_NUMBER_SUFFIX.search(tc_id):
            continue
        cases.append(SpecCase(tc_id=tc_id, title=title, path=path, line=lineno))
    return cases


def collect_spec_cases(roots: list[Path]) -> tuple[dict[str, SpecCase], list[str], int]:
    """Index every declared test case below the given roots.

    Args:
        roots: Directories (or single ``.md`` files) holding test-case documents.

    Returns:
        A ``(cases_by_id, duplicate_ids, document_count)`` triple. The first
        declaration of a duplicated ID wins; duplicates are reported, not fatal.

    Raises:
        TraceabilityError: If a root does not exist or declares no test case.
    """
    cases: dict[str, SpecCase] = {}
    duplicates: list[str] = []
    documents = 0
    for root in roots:
        files = [root] if root.is_file() else None
        if files is None:
            if not root.is_dir():
                raise TraceabilityError(f"spec root does not exist: {root}")
            files = sorted(root.glob("**/*.md"))
        for document in files:
            documents += 1
            for case in parse_spec_document(document):
                if case.tc_id in cases:
                    duplicates.append(case.tc_id)
                    continue
                cases[case.tc_id] = case
    if not cases:
        raise TraceabilityError(
            "no test cases found — expected headings such as '## TC-004-092: <title>' "
            f"under: {', '.join(str(root) for root in roots)}"
        )
    return cases, sorted(set(duplicates)), documents


def suggest_alternative(tc_id: str, known: dict[str, SpecCase]) -> str | None:
    """Suggest the other legal spelling of an unresolved ID, if that one exists.

    ``TC-004-092`` and ``TC-REQ-004-092`` are both legal shapes, so a tag that
    picked the wrong one is the most likely cause of an orphan.
    """
    alternative = (
        tc_id.replace("TC-REQ-", "TC-", 1)
        if tc_id.startswith("TC-REQ-")
        else tc_id.replace("TC-", "TC-REQ-", 1)
    )
    return alternative if alternative in known else None


# ── Reporting ────────────────────────────────────────────────────────────────


def _relative(path: Path) -> str:
    """Render a path relative to the repository root when possible."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def report(
    scenarios: list[Scenario],
    cases: dict[str, SpecCase],
    duplicates: list[str],
    documents: int,
    feature_roots: list[Path],
    spec_roots: list[Path],
    list_unimplemented: bool,
) -> int:
    """Print the traceability report and return the process exit code.

    Args:
        scenarios: Every parsed Gherkin scenario.
        cases: Declared test cases by ID.
        duplicates: IDs declared more than once in the spec (informational).
        documents: Number of scanned spec documents.
        feature_roots: Scanned feature roots (for the header line).
        spec_roots: Scanned spec roots (for the header line).
        list_unimplemented: Whether to list the not-yet-automated case IDs.

    Returns:
        ``EXIT_OK`` when every scenario resolves, ``EXIT_DEFECTS`` otherwise.
    """
    feature_files = sorted({scenario.path for scenario in scenarios})
    print("BDD traceability check")
    print(
        f"  features: {', '.join(_relative(root) for root in feature_roots)} "
        f"— {len(feature_files)} file(s), {len(scenarios)} scenario(s)"
    )
    print(
        f"  spec:     {', '.join(_relative(root) for root in spec_roots)} "
        f"— {len(cases)} declared test case(s) in {documents} document(s)"
    )
    print()

    defects: list[str] = []
    resolved: list[tuple[Scenario, SpecCase]] = []
    for scenario in scenarios:
        location = f"{_relative(scenario.path)}:{scenario.line}"
        if not scenario.tc_ids:
            defects.append(
                f'untagged scenario: {location} — "{scenario.name}" carries no @TC-<id> tag; '
                "every scenario must name the test case it was derived from"
            )
            continue
        for tc_id in scenario.tc_ids:
            case = cases.get(tc_id)
            if case is None:
                hint = suggest_alternative(tc_id, cases)
                suffix = f" (did you mean @{hint}?)" if hint else ""
                defects.append(
                    f'orphan tag: {location} — "{scenario.name}" is tagged @{tc_id}, '
                    f"which no test-case document declares{suffix}"
                )
                continue
            resolved.append((scenario, case))

    for scenario, case in resolved:
        print(
            f"  OK  {case.tc_id}  {_relative(scenario.path)}:{scenario.line}"
            f"  ->  {_relative(case.path)}:{case.line}"
        )
    if resolved:
        print()

    for defect in defects:
        print(f"  ERROR  {defect}")
    if defects:
        print()

    implemented = {case.tc_id for _, case in resolved}
    unimplemented = sorted(set(cases) - implemented)
    print(
        f"  info: {len(implemented)} of {len(cases)} declared test case(s) have a BDD scenario; "
        f"{len(unimplemented)} do not yet (not a defect — automation coverage grows over time)"
    )
    if duplicates:
        print(f"  info: {len(duplicates)} test-case ID(s) declared more than once: {', '.join(duplicates)}")
    if list_unimplemented:
        by_document: dict[str, list[str]] = {}
        for tc_id in unimplemented:
            by_document.setdefault(_relative(cases[tc_id].path), []).append(tc_id)
        for document, ids in sorted(by_document.items()):
            print(f"  not automated — {document} ({len(ids)}): {', '.join(ids)}")

    print()
    if defects:
        print(f"FAILED — {len(defects)} traceability defect(s).")
        return EXIT_DEFECTS
    print(f"OK — all {len(scenarios)} scenario(s) resolve to a declared test case.")
    return EXIT_OK


# ── Entry point ──────────────────────────────────────────────────────────────


def _resolve(paths: list[str]) -> list[Path]:
    """Resolve CLI paths against the repository root when they are relative."""
    return [Path(path) if Path(path).is_absolute() else REPO_ROOT / path for path in paths]


def main(argv: list[str] | None = None) -> int:
    """Run the traceability check.

    Returns:
        0 when every scenario resolves, 1 on traceability defects, 2 on a usage
        or environment error.
    """
    parser = argparse.ArgumentParser(
        prog="check_bdd_traceability.py",
        description=(
            "Verify that every Gherkin scenario carries a @TC-<id> tag that resolves to a "
            "test case declared in the specification. Declared cases without a scenario are "
            "reported as an informational count and never fail the check."
        ),
    )
    parser.add_argument(
        "--features-root",
        action="append",
        metavar="PATH",
        help=f"directory or .feature file to scan (repeatable; default: {DEFAULT_FEATURE_ROOTS[0]})",
    )
    parser.add_argument(
        "--spec-root",
        action="append",
        metavar="PATH",
        help=f"directory or .md file holding test cases (repeatable; default: {DEFAULT_SPEC_ROOTS[0]})",
    )
    parser.add_argument(
        "--list-unimplemented",
        action="store_true",
        help="also list the declared test cases that have no BDD scenario yet",
    )
    args = parser.parse_args(argv)

    feature_roots = _resolve(args.features_root or list(DEFAULT_FEATURE_ROOTS))
    spec_roots = _resolve(args.spec_root or list(DEFAULT_SPEC_ROOTS))

    try:
        tc_pattern = load_tc_id_pattern()
        scenarios = collect_scenarios(feature_roots, tc_pattern)
        cases, duplicates, documents = collect_spec_cases(spec_roots)
    except TraceabilityError as exc:
        print(f"check_bdd_traceability: {exc}", file=sys.stderr)
        return EXIT_USAGE

    return report(
        scenarios=scenarios,
        cases=cases,
        duplicates=duplicates,
        documents=documents,
        feature_roots=feature_roots,
        spec_roots=spec_roots,
        list_unimplemented=args.list_unimplemented,
    )


if __name__ == "__main__":
    raise SystemExit(main())
