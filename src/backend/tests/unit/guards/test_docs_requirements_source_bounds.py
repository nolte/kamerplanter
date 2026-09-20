"""#1601 — the COMPILE SOURCE of a hash-bearing list is bounded on both sides.

**The half of the boundary this file holds.** NFR-009 §2.3.1 splits Python
installs into class (a) — the result reaches a delivered artefact, so it must be
hash-bearing — and class (b) — runner-only, so it must be bounded. #1598 left one
question inside class (a) open BY NAME, and #1601 decides it: a class (a) list
carries **two** bindings, and they bind different moments.

* the ``--hash=`` lines of the COMPILED list bind the bytes that are installed
  today (``test_docs_requirements_hash_verification.py`` beside this file);
* the ranges of the COMPILE SOURCE bind what the **next** recompile may choose.
  Nothing else does: ``task docs:lock`` resolves the newest version each range
  allows, so an entry without a ceiling is a major upgrade waiting for the next
  run of a command that is supposed to be routine.

A hash cannot stand in for the second one. It is a statement about a file that
already exists; the recompile produces a different file, hashes and all, and it
is just as hash-verified afterwards. Measured on ``docs/requirements.in`` before
this guard: **eight of twelve** entries had a floor and no ceiling, which is why
this is drift rather than a decision — the four that were bounded (``mkdocs``,
``mkdocs-material``, ``mkdocs-literate-nav``, ``pyyaml``) already showed the
intended shape.

**Why it globs instead of naming the file.** ``docs/requirements.in`` is the only
compile source in this repository today. A guard bound to that one path is an
opt-in list, and this repository keeps rediscovering opt-in lists as a defect
class (#1402, #1406, #1572): the second ``*.in``, added next year beside a
different lock, would be invisible. So the sources are DISCOVERED and
:data:`_MINIMUM_SOURCES` keeps the discovery honest — a glob that stops matching
fails here instead of passing every downstream assertion over an empty list.

**Two checks, not one.** Bounds alone would pass for a ceiling BELOW what
resolves today, which is not a bound but an unannounced downgrade. So every
entry is additionally clamped against the compiled list beside it: the version
the compiled file actually pins must satisfy the source's range. That is the
durable form of the measurement #1601 asks for — "the bounds describe the set
already installed rather than moving it" — and it keeps holding after the
pull request that measured it once.

WHAT THIS GUARD DOES NOT SEE, named rather than implied, because a sweep is only
as complete as the spelling it matches:

* a requirement pulled in by a ``-r other.in`` / ``-c constraints.txt`` line.
  Option lines are skipped here (they name no distribution); the file they point
  at is itself a source and is matched by the glob if it ends in ``.in``, and by
  ``check_renovate_dashboard.unhashed_requirements_installs`` if it is a
  ``requirements*.txt``. A ``.txt`` constraint file reached ONLY through such a
  line is the gap;
* a direct URL or VCS requirement (``pkg @ https://…``, ``git+https://…``). It
  pins by locator rather than by range, so the floor/ceiling question does not
  apply — there is none in this repository today, and one added tomorrow fails
  the parse below rather than being silently skipped;
* what a range means for a 0.x package. ``mkdocs-minify-plugin>=0.7.0,<1.0.0``
  is bounded by this file's rule and still admits a breaking 0.9; semver says
  nothing below 1.0. Bounding caps the blast radius, it does not remove it.

Traces to #1601 (no TC-ID: a dependency gate is not a user-facing case).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

#: Directories a glob over the checkout must not descend into: build output and
#: dependency trees carry requirement files nobody in this repository edits.
_SKIPPED_DIRECTORIES = frozenset(
    {".git", ".venv", ".venv-docs", "node_modules", "__pycache__", ".mypy_cache", ".pytest_cache", "dist", "build"}
)

#: The floor the discovery must clear before any assertion below means anything.
#: One compile source on 2026-09-20 (``docs/requirements.in``). A FLOOR, not an
#: equality: a second one is covered without anybody editing this number, while
#: a glob that suddenly finds nothing fails here rather than passing vacuously.
_MINIMUM_SOURCES = 1

#: Same reasoning one level down: twelve entries in ``docs/requirements.in``.
_MINIMUM_ENTRIES_PER_SOURCE = 1

#: A line that configures pip rather than naming a distribution.
_OPTION_LINE = re.compile(r"^-")

#: An inline comment: whitespace, then ``#``. Anchored on the whitespace so a
#: fragment inside a URL (``…#egg=name``) is not mistaken for one.
_INLINE_COMMENT = re.compile(r"\s+#.*$")


@dataclass(frozen=True)
class SourceEntry:
    """One requirement line of a compile source, as the file spells it."""

    #: Path relative to the checkout root, e.g. ``docs/requirements.in``.
    source: str
    #: The requirement string with any inline comment stripped.
    requirement: str

    def __str__(self) -> str:  # pragma: no cover — pytest ids and messages only
        return f"{self.source}: {self.requirement}"


def compile_sources(repo_root: Path) -> tuple[Path, ...]:
    """Every ``*.in`` requirement source in the checkout, sorted, discovered."""
    found: list[Path] = []
    for candidate in repo_root.rglob("*.in"):
        if any(part in _SKIPPED_DIRECTORIES for part in candidate.relative_to(repo_root).parts):
            continue
        if candidate.is_file():
            found.append(candidate)
    return tuple(sorted(found))


def source_entries(source: str, text: str) -> tuple[SourceEntry, ...]:
    """Every requirement line of *text*, in file order.

    Continuation lines are joined first; comment lines and option lines are
    skipped because they name no distribution.
    """
    entries: list[SourceEntry] = []
    for raw in text.replace("\\\n", " ").splitlines():
        line = _INLINE_COMMENT.sub("", raw.strip()).strip()
        if not line or line.startswith("#") or _OPTION_LINE.match(line):
            continue
        entries.append(SourceEntry(source=source, requirement=line))
    return tuple(entries)


def _bounds(specifier: SpecifierSet) -> tuple[bool, bool]:
    """``(has_floor, has_ceiling)`` for a specifier set.

    Deliberately identical to ``test_pre_commit_dependency_bounds._bounds``:
    the two halves of the same §2.1 duty must not read "bounded" differently.
    ``==``/``===``/``~=`` count as both, since each closes the range on both
    sides by itself.
    """
    has_floor = any(clause.operator in (">=", ">", "==", "===", "~=") for clause in specifier)
    has_ceiling = any(clause.operator in ("<=", "<", "==", "===", "~=") for clause in specifier)
    return has_floor, has_ceiling


def unbounded_entries(entries: tuple[SourceEntry, ...]) -> list[str]:
    """Entries missing a floor or a ceiling, with the missing side named.

    An unparseable requirement is a FINDING, not a skip — a URL or VCS pin that
    this file cannot reason about must be visible rather than assumed fine.
    """
    offenders: list[str] = []
    for entry in entries:
        try:
            requirement = Requirement(entry.requirement)
        except InvalidRequirement as exc:
            offenders.append(f"{entry} (not a PEP 508 requirement: {exc})")
            continue
        if requirement.url is not None:
            offenders.append(f"{entry} (pinned by URL; ranges do not apply — decide it explicitly)")
            continue
        has_floor, has_ceiling = _bounds(requirement.specifier)
        if not (has_floor and has_ceiling):
            missing = "floor" if not has_floor else "ceiling"
            offenders.append(f"{entry} (no {missing})")
    return offenders


def compiled_versions(text: str) -> dict[str, Version]:
    """``{canonical name: version}`` for a ``--generate-hashes`` compiled list."""
    versions: dict[str, Version] = {}
    for raw in text.splitlines():
        line = raw.strip().rstrip("\\").strip()
        if not line or line.startswith("#") or line.startswith("--hash") or _OPTION_LINE.match(line):
            continue
        match = re.match(r"^([A-Za-z0-9._-]+)\s*==\s*([^\s;]+)", line)
        if match:
            versions[canonicalize_name(match.group(1))] = Version(match.group(2))
    return versions


def entries_excluding_what_is_installed(entries: tuple[SourceEntry, ...], compiled: dict[str, Version]) -> list[str]:
    """Entries whose range does NOT contain the version the compiled list pins.

    The machine-checkable form of "a bound describes the set already installed".
    A ceiling below what resolves today is an unannounced downgrade wearing a
    bound's clothes; it belongs in its own reviewed pull request, together with
    the recompiled list that shows what it moves.
    """
    offenders: list[str] = []
    for entry in entries:
        try:
            requirement = Requirement(entry.requirement)
        except InvalidRequirement:
            continue  # reported by unbounded_entries(); not this check's finding
        name = canonicalize_name(requirement.name)
        installed = compiled.get(name)
        if installed is None:
            offenders.append(f"{entry} — the compiled list beside it pins no {name}; source and output disagree")
            continue
        if not requirement.specifier.contains(installed, prereleases=True):
            offenders.append(f"{entry} excludes the pinned {name}=={installed}; recompiling would MOVE the set")
    return offenders


@pytest.fixture(scope="module")
def sources() -> tuple[Path, ...]:
    """The compile sources as the checkout actually carries them."""
    return compile_sources(_REPO_ROOT)


@pytest.fixture(scope="module")
def entries(sources: tuple[Path, ...]) -> tuple[SourceEntry, ...]:
    """Every entry of every compile source, in discovery order."""
    collected: list[SourceEntry] = []
    for source in sources:
        relative = source.relative_to(_REPO_ROOT).as_posix()
        collected.extend(source_entries(relative, source.read_text(encoding="utf-8")))
    return tuple(collected)


class TestTheSweepReadsSomething:
    """Anti-vacuity: every assertion below is worthless over an empty list."""

    def test_at_least_the_measured_number_of_sources_is_found(self, sources: tuple[Path, ...]) -> None:
        assert len(sources) >= _MINIMUM_SOURCES, (
            f"only {len(sources)} compile source(s) found; {_MINIMUM_SOURCES} was measured on 2026-09-20 "
            "(docs/requirements.in). Either the file moved or this glob stopped matching it."
        )

    def test_every_source_yields_entries(self, sources: tuple[Path, ...]) -> None:
        empty = [
            source.relative_to(_REPO_ROOT).as_posix()
            for source in sources
            if len(source_entries("", source.read_text(encoding="utf-8"))) < _MINIMUM_ENTRIES_PER_SOURCE
        ]
        assert not empty, (
            "compile source(s) this parser reads as empty: "
            + ", ".join(empty)
            + ". A source that parses to nothing passes every check below without checking anything."
        )


class TestEveryEntryIsBounded:
    """#1601's decision: §2.1 binds the compile source, not only the output."""

    def test_every_entry_has_a_floor_and_a_ceiling(self, entries: tuple[SourceEntry, ...]) -> None:
        offenders = unbounded_entries(entries)
        assert not offenders, (
            "compile-source entries without both bounds: "
            + "; ".join(offenders)
            + ". The hashes in the compiled list bind today's bytes; only these ranges bind what the next "
            "`task docs:lock` may choose (NFR-009 §2.3.1, #1601)."
        )

    def test_every_bound_contains_what_the_compiled_list_pins(self, sources: tuple[Path, ...]) -> None:
        offenders: list[str] = []
        for source in sources:
            compiled_path = source.with_suffix(".txt")
            if not compiled_path.is_file():
                offenders.append(f"{source.relative_to(_REPO_ROOT).as_posix()} has no compiled list beside it")
                continue
            relative = source.relative_to(_REPO_ROOT).as_posix()
            offenders.extend(
                entries_excluding_what_is_installed(
                    source_entries(relative, source.read_text(encoding="utf-8")),
                    compiled_versions(compiled_path.read_text(encoding="utf-8")),
                )
            )
        assert not offenders, (
            "compile-source ranges that do not describe the compiled set: "
            + "; ".join(offenders)
            + ". A bound must record the set already installed; moving it is an update and needs its own "
            "pull request with the recompiled list in the diff (#1601)."
        )


class TestTheGuardCanFail:
    """The falsifier. It asserts the SAME expression the rule asserts —
    :func:`unbounded_entries` and :func:`entries_excluding_what_is_installed`
    over a MUTATED copy of the real file, not a hand-written fixture. A fixture
    is where "the double accepts what the real thing rejects" gets in, and a
    falsifier that checks a neighbouring statement is green while the rule is
    inert (measured three times in this repository in one week)."""

    @pytest.fixture
    def real_source(self) -> str:
        return (_REPO_ROOT / "docs" / "requirements.in").read_text(encoding="utf-8")

    def test_dropping_a_ceiling_is_reported(self, real_source: str) -> None:
        mutated = real_source.replace("mike>=2.0.0,<3.0.0", "mike>=2.0.0", 1)
        assert mutated != real_source, "the mutation did not apply; this test would pass vacuously"
        offenders = unbounded_entries(source_entries("docs/requirements.in", mutated))
        assert any("mike" in offender and "no ceiling" in offender for offender in offenders), offenders

    def test_the_unmutated_file_is_clean(self, real_source: str) -> None:
        """The other half of the falsifier: the real file is GREEN, so the test
        above measures the mutation and not a rule that reports everything."""
        assert not unbounded_entries(source_entries("docs/requirements.in", real_source))

    def test_a_ceiling_below_what_is_installed_is_reported(self, real_source: str) -> None:
        mutated = real_source.replace("mike>=2.0.0,<3.0.0", "mike>=2.0.0,<2.1.0", 1)
        assert mutated != real_source, "the mutation did not apply; this test would pass vacuously"
        compiled = compiled_versions((_REPO_ROOT / "docs" / "requirements.txt").read_text(encoding="utf-8"))
        offenders = entries_excluding_what_is_installed(source_entries("docs/requirements.in", mutated), compiled)
        assert any("mike" in offender and "MOVE" in offender for offender in offenders), offenders

    def test_the_compiled_list_is_read_at_all(self) -> None:
        """Positive control for the clamp: the parse above must actually find
        the packages, or :func:`entries_excluding_what_is_installed` would
        report everything (and the test above would pass for the wrong reason)."""
        compiled = compiled_versions((_REPO_ROOT / "docs" / "requirements.txt").read_text(encoding="utf-8"))
        assert compiled.get(canonicalize_name("mike")) is not None
        assert len(compiled) >= 12, f"only {len(compiled)} pinned distributions parsed out of docs/requirements.txt"
