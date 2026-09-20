"""#1572 — every ``additional_dependencies:`` install in the required lane is bounded.

**The boundary this file enforces one half of.** Written normatively in
``scripts/ci/check_renovate_dashboard.py`` (§4, "THE BOUNDARY, SET
NORMATIVELY") and repeated here in one sentence, because a rule that lives only
in the other module is a rule nobody reading this file can check against:

* a Python install whose result REACHES A DELIVERED ARTEFACT must be
  hash-bearing — a lock or a ``--generate-hashes`` list, verified at install
  time. Those are covered by ``test_lock_hash_verification.py`` and
  ``test_library_lock_hash_verification.py`` beside this file, and by the two
  sweeps in ``check_renovate_dashboard.py``;
* a Python install that is RUNNER-ONLY and whose output is a verdict — a lint
  result, a gate decision, a report — needs reproducibility of BEHAVIOUR, not of
  bytes. It needs bounds, not hashes. Hashing it would mean a lock file per
  pre-commit hook and would close no threat: the wheel is never shipped.

``.pre-commit-config.yaml``'s ``additional_dependencies:`` is the second class,
and this file is what holds it to "bounded". It deliberately does NOT ask for
hashes.

**Why bounds and not nothing.** The ``static`` lane that runs pre-commit is one
of the two REQUIRED status checks on ``develop``. Renovate's ``pre-commit``
manager maintains ``rev:`` for hook REPOSITORIES and never reads
``additional_dependencies`` — measured in #1572 and consistent with the manager's
documented scope — so an open upper bound here is an unreviewed major upgrade
applied to every contributor and to the required gate at once, with no manager
watching and no lock to fall back on. Measured at HEAD before this file: of the
twenty requirement strings across seventeen hooks, NINETEEN had a floor and no
ceiling — every one but ``selenium>=4.25.0,<5``. Those numbers are a dated
MEASUREMENT, not the rule: the rule is "every entry the file carries", and the
guard enumerates rather than counts, so an eighteenth hook is covered without
anybody editing a sentence.

**Why it enumerates instead of listing.** #1572's own text names ONE entry, the
``e2e-selftest`` hook. Measured against the file, there are **seventeen**
(``ruff`` 4×, ``PyYAML`` 8×, ``mypy`` 4×, plus ``selenium``/``pytest`` and
``jsonschema``/``referencing``), which is the "the issue's site list is too
short until you measure it as a class" shape. A guard bound to the one hook the
issue named would be exactly the opt-in list this repository keeps rediscovering
as a defect class (#1402, #1406, ``backend-guards.yml``'s directory-not-list
argument). So the entries are read out of the YAML: a hook added tomorrow with a
new unbounded dependency is RED, not invisible.

**Each bound is held against a tree that already declares the package**
(:data:`_BINDINGS`), so this file is a clamp and not a second opinion. The hook's
version set must be a SUBSET of what that tree allows — tightening is permitted
(a pre-commit environment may need a newer ruff than the floor the backend
tolerates), widening is not.

WHAT THIS GUARD DOES NOT SEE — named rather than implied, because a sweep is
only as complete as the spelling it matches:

* a hook that installs with its own ``entry:`` — ``language: system`` shelling
  out to ``pip install``, or a script that installs at runtime. There is no such
  hook today (the ``language: system`` hooks all run checked-in shell scripts),
  and the ``language: python`` assertion below is what makes a future one
  visible: a hook carrying ``additional_dependencies`` under a non-Python
  language turns this file red rather than being silently mis-measured;
* ``%pip install`` in a Jupyter notebook — ``tools/rag-eval/rag_eval.ipynb`` has
  one. A notebook magic is neither a requirement list nor a ``run:`` step, so no
  sweep in this repository reads it. It is inventory, not a finding: that tree
  ships nothing and is already ``check_renovate_dashboard``'s argued exception;
* ``pip install`` inside a workflow ``run:`` block — six sites, all ``==``-pinned
  runner tools. Class (b) and already satisfied, so inventory, not a finding
  TODAY. A NEW unpinned one would get past every sweep in this repository,
  including this one, which leaves one half of class (b) enforced and the other
  half only described — the asymmetry that let the entries this file now guards
  drift for years. Tracked as **#1602**, deliberately out of #1572's scope.

Traces to #1572 (no TC-ID: a dependency gate is not a user-facing case).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
import yaml
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

from tests.support.repo_scripts import find_repo_root
from tests.support.version_bounds import missing_bound

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_CONFIG = _REPO_ROOT / ".pre-commit-config.yaml"

#: The trees a binding may point at, all of them PEP 621 files this repository
#: already locks. A binding naming anything else fails on the read.
_BACKEND = "src/backend/pyproject.toml"
_E2E = "tests/e2e/pyproject.toml"
_KP_VECTORDB = "src/libs/kp_vectordb/pyproject.toml"
_KP_ERRORTRACKING = "src/libs/kp_errortracking/pyproject.toml"
_KNOWLEDGE = "src/knowledge-service/pyproject.toml"
_INFERENCE = "src/inference-service/pyproject.toml"


@dataclass(frozen=True)
class Binding:
    """One ``additional_dependencies`` requirement and the tree that justifies it."""

    #: The hook id in ``.pre-commit-config.yaml``.
    hook: str
    #: The EXACT string the config must carry. Equality and not "compatible
    #: with" on purpose: a subset rule alone would let `ruff>=0.15.0` drop to
    #: `ruff>=0.14.0` (still inside the backend's `>=0.8.0,<1.0.0`) without a
    #: word said anywhere. Equality makes every loosening a change to THIS file
    #: as well, i.e. a reviewed decision.
    requirement: str
    #: The pyproject.toml whose declaration of the same package bounds it.
    declared_in: str
    #: Why that tree and not another. Read by a human, asserted by nothing —
    #: the machine-checkable half is the subset relation.
    why: str


#: One binding per ``additional_dependencies`` requirement in the file —
#: seventeen hooks / twenty strings when this was written, and the enumeration
#: above is what keeps that true rather than this comment. Each was decided
#: individually (#1572). Per package:
#:
#: * ``ruff`` — floor 0.15.0 kept (the hooks need a ruff that understands the
#:   current ``ruff.toml``; that is TIGHTER than the tree and allowed), ceiling
#:   taken from the backend's own ``<1.0.0``. A pre-1.0 ruff changes lint and
#:   format behaviour across minors, so an open ceiling here means the hook and
#:   ``task lint:backend`` (which runs the ruff from ``uv.lock``) can disagree
#:   about the same file. Bounding does not remove that risk, it caps it;
#: * ``mypy`` — the four hooks are bound to the four trees they type-check, not
#:   to the backend, because that is where each one's mypy configuration and dev
#:   extra live. Ceiling ``<3.0.0`` from the backend's declaration; mypy majors
#:   change defaults;
#: * ``PyYAML`` — eight hooks, all repo-local scripts under ``scripts/`` that have
#:   no pyproject of their own. The backend is the ONLY tree in this repository
#:   that declares pyyaml, so it is the one source there is; ``<7.0.0`` is its
#:   bound, carried over unchanged;
#: * ``jsonschema`` / ``referencing`` — same argument, same tree, and the floors
#:   already matched the backend's exactly;
#: * ``selenium`` — already bounded and already EQUAL to what
#:   ``tests/e2e/pyproject.toml`` declares, upper bound included, with the reason
#:   for ``<5`` written out there (the suite reads Selenium internals). Left
#:   untouched: it is the one entry that was correct before this issue;
#: * ``pytest`` — the E2E tree declares it WITHOUT a ceiling, so this binding is
#:   deliberately tighter than its source. ``<10.0.0`` is the
#:   backend's ceiling for the same package, and the hook is a pytest RUN
#:   (``python -m pytest tests/e2e_selftest``) inside the required lane: a major
#:   pytest arriving unannounced breaks the gate for everyone at once. Tighter
#:   than the source is a subset, so the clamp below still holds.
#:
#: FIVE bindings are tighter than their declaring tree, not one: ``pytest``
#: above, and the four ``mypy`` bindings, whose library and service trees all
#: declare a bare ``mypy>=1.13.0``. Tighter is a subset and therefore passes the
#: clamp by design — it is recorded here because this file is the document that
#: carries the boundary, and a document that miscounts its own exceptions is the
#: thing that gets believed later.
#:
#: No entry was found to be deliberately open. Every ``additional_dependencies``
#: line was read together with the comment block above its hook; none records an
#: intent to track a moving upper bound, and none of the ceilings added here
#: changes what resolves today (verified by re-running the affected hooks).
_BINDINGS: tuple[Binding, ...] = (
    Binding(
        hook="ruff-lint-e2e",
        requirement="ruff>=0.15.0,<1.0.0",
        declared_in=_BACKEND,
        why="tests/e2e has a ruff.toml but declares no ruff; the backend is the repository's only ruff declaration",
    ),
    Binding(
        hook="ruff-format-e2e",
        requirement="ruff>=0.15.0,<1.0.0",
        declared_in=_BACKEND,
        why="same tool, same hook pair; see ruff-lint-e2e",
    ),
    Binding(
        hook="e2e-selftest",
        requirement="selenium>=4.25.0,<5",
        declared_in=_E2E,
        why="the hook runs the E2E harness self-tests; tests/e2e/pyproject.toml is that harness's declaration",
    ),
    Binding(
        hook="e2e-selftest",
        requirement="pytest>=8.3.0,<10.0.0",
        declared_in=_E2E,
        why="same harness; the ceiling is the backend's, since the E2E tree declares none (see the note above)",
    ),
    Binding(
        hook="seed-catalogue-page-size",
        requirement="PyYAML>=6.0,<7.0.0",
        declared_in=_BACKEND,
        why="scripts/check_seed_catalogue_page_size.py reads backend seed YAML; the backend declares pyyaml",
    ),
    Binding(
        hook="seed-harvest-integrity",
        requirement="PyYAML>=6.0,<7.0.0",
        declared_in=_BACKEND,
        why="scripts/check_seed_harvest_integrity.py reads backend seed YAML",
    ),
    Binding(
        hook="workflow-gate-integrity",
        requirement="PyYAML>=6.0,<7.0.0",
        declared_in=_BACKEND,
        why="scripts/check_workflow_gate_integrity.py parses workflow YAML; no tree of its own",
    ),
    Binding(
        hook="attest-registry-credentials",
        requirement="PyYAML>=6.0,<7.0.0",
        declared_in=_BACKEND,
        why="scripts/check_attest_registry_credentials.py parses workflow YAML",
    ),
    Binding(
        hook="chart-develop-version",
        requirement="PyYAML>=6.0,<7.0.0",
        declared_in=_BACKEND,
        why="scripts/check_chart_develop_version.py parses Chart.yaml",
    ),
    Binding(
        hook="seed-schema-conformance",
        requirement="PyYAML>=6.0,<7.0.0",
        declared_in=_BACKEND,
        why="scripts/check_seed_schema.py reads backend seed YAML",
    ),
    Binding(
        hook="seed-schema-conformance",
        requirement="jsonschema>=4.23.0,<5.0.0",
        declared_in=_BACKEND,
        why="the backend's dev extra declares jsonschema for the same seed-schema tests",
    ),
    Binding(
        hook="seed-schema-conformance",
        requirement="referencing>=0.35.0,<1.0.0",
        declared_in=_BACKEND,
        why="jsonschema's registry dependency, declared beside it in the backend's dev extra",
    ),
    Binding(
        hook="ruff-lint",
        requirement="ruff>=0.15.0,<1.0.0",
        declared_in=_BACKEND,
        why="the hook lints src/backend; the backend declares ruff",
    ),
    Binding(
        hook="ruff-format",
        requirement="ruff>=0.15.0,<1.0.0",
        declared_in=_BACKEND,
        why="same tool, same tree; see ruff-lint",
    ),
    Binding(
        hook="mypy-kp-vectordb",
        requirement="mypy>=1.13.0,<3.0.0",
        declared_in=_KP_VECTORDB,
        why="the hook type-checks kp_vectordb, whose dev extra declares the mypy it is configured for",
    ),
    Binding(
        hook="mypy-kp-errortracking",
        requirement="mypy>=1.13.0,<3.0.0",
        declared_in=_KP_ERRORTRACKING,
        why="the hook type-checks kp_errortracking",
    ),
    Binding(
        hook="mypy-knowledge-service",
        requirement="mypy>=1.13.0,<3.0.0",
        declared_in=_KNOWLEDGE,
        why="the hook type-checks the knowledge service",
    ),
    Binding(
        hook="mypy-inference-service",
        requirement="mypy>=1.13.0,<3.0.0",
        declared_in=_INFERENCE,
        why="the hook type-checks the inference service",
    ),
    Binding(
        hook="steckbrief-seed-consistency",
        requirement="PyYAML>=6.0,<7.0.0",
        declared_in=_BACKEND,
        why="the script lives inside the backend package and reads its seed YAML",
    ),
    Binding(
        hook="plugin-shadowing",
        requirement="PyYAML>=6.0,<7.0.0",
        declared_in=_BACKEND,
        why="scripts/check_skill_plugin_shadowing.py parses skill/agent front matter",
    ),
)

#: The floor the enumeration must clear before any other assertion means
#: anything. Seventeen hooks was the measurement on 2026-09-20; the number is a
#: FLOOR and not an equality, so adding a hook is not a spurious failure — but a
#: parser that suddenly finds two entries (a YAML shape it stopped matching, the
#: "the measuring instrument has the gap" class) fails here instead of passing
#: every downstream check vacuously.
_MINIMUM_HOOKS_WITH_DEPENDENCIES = 17


@dataclass(frozen=True)
class Entry:
    """One ``(hook id, requirement string)`` pair as the config actually spells it."""

    hook: str
    requirement: str
    language: str

    def __str__(self) -> str:  # pragma: no cover — pytest ids and messages only
        return f"{self.hook}: {self.requirement}"


def _load_config(text: str) -> Any:
    """Parse ``.pre-commit-config.yaml``. Separate from the reader so the
    falsification tests below can feed it a MUTATED copy of the real file rather
    than a hand-written fixture — a fixture is where "the double accepts what the
    real thing rejects" gets in."""
    return yaml.safe_load(text)


def additional_dependency_entries(document: Any) -> tuple[Entry, ...]:
    """Every ``additional_dependencies`` requirement in the document, in file order."""
    entries: list[Entry] = []
    for repo in document.get("repos", []):
        for hook in repo.get("hooks", []):
            for requirement in hook.get("additional_dependencies", []) or []:
                entries.append(
                    Entry(
                        hook=str(hook.get("id", "<no id>")),
                        requirement=str(requirement),
                        language=str(hook.get("language", "<unset>")),
                    )
                )
    return tuple(entries)


def unrecorded_entries(entries: tuple[Entry, ...], bindings: tuple[Binding, ...] = _BINDINGS) -> list[str]:
    """Entries whose exact ``(hook, requirement)`` pair is not recorded."""
    recorded = {(binding.hook, binding.requirement) for binding in bindings}
    return [str(entry) for entry in entries if (entry.hook, entry.requirement) not in recorded]


def stale_bindings(entries: tuple[Entry, ...], bindings: tuple[Binding, ...] = _BINDINGS) -> list[str]:
    """Recorded bindings the config no longer carries."""
    present = {(entry.hook, entry.requirement) for entry in entries}
    return [f"{b.hook}: {b.requirement}" for b in bindings if (b.hook, b.requirement) not in present]


def unbounded_requirements(entries: tuple[Entry, ...]) -> list[str]:
    """Entries missing a floor or a ceiling.

    The reading of "bounded" lives in ``tests.support.version_bounds`` and is
    shared with the other two guards of the same §2.1 duty (#1602 review): a
    rule written three times is a rule with three futures.
    """
    offenders: list[str] = []
    for entry in entries:
        missing = missing_bound(Requirement(entry.requirement).specifier)
        if missing is not None:
            offenders.append(f"{entry} ({missing})")
    return offenders


def _declared_specifiers(pyproject: Path) -> dict[str, SpecifierSet]:
    """Every package the tree declares, from ``[project].dependencies``, every
    optional-dependency extra and every PEP 735 dependency group.

    A package declared twice with DIFFERENT specifiers raises rather than
    silently picking one: the clamp would then be measuring a set nobody chose.
    """
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    lists: list[list[str]] = [data.get("project", {}).get("dependencies", []) or []]
    for extra in (data.get("project", {}).get("optional-dependencies", {}) or {}).values():
        lists.append(extra or [])
    for group in (data.get("dependency-groups", {}) or {}).values():
        lists.append([item for item in (group or []) if isinstance(item, str)])

    declared: dict[str, SpecifierSet] = {}
    for requirements in lists:
        for raw in requirements:
            requirement = Requirement(raw)
            name = canonicalize_name(requirement.name)
            previous = declared.get(name)
            if previous is not None and str(previous) != str(requirement.specifier):
                raise AssertionError(
                    f"{pyproject} declares {name} twice with different specifiers "
                    f"({previous} vs {requirement.specifier}); the binding has no single source to clamp against."
                )
            declared[name] = requirement.specifier
    return declared


def _probe_versions(*specifiers: SpecifierSet) -> list[Version]:
    """Candidate versions that distinguish the two specifier sets.

    Every version named in either set, plus each one nudged up and down on every
    release component, plus the extremes. Comparing sets by sampling rather than
    by symbolic reasoning keeps this readable; the nudges are what make the
    sample able to see a moved bound — without them, lowering a floor from
    0.15.0 to 0.14.0 would be invisible because no probe sits between them.
    """
    seeds: set[str] = {"0", "0.0.1", "99999.0.0"}
    for specifier in specifiers:
        for clause in specifier:
            base = Version(clause.version.rstrip("*").rstrip("."))
            seeds.add(str(base))
            release = list(base.release) or [0]
            for index in range(len(release)):
                up = list(release)
                up[index] += 1
                seeds.add(".".join(str(part) for part in up))
                if release[index] > 0:
                    down = list(release)
                    down[index] -= 1
                    seeds.add(".".join(str(part) for part in down))
    return sorted({Version(seed) for seed in seeds})


def out_of_range_requirements(
    entries: tuple[Entry, ...], repo_root: Path, bindings: tuple[Binding, ...] = _BINDINGS
) -> list[str]:
    """Entries allowing a version the tree that declares the package does not.

    Tightening is fine and expected (a hook may need a newer tool than the tree's
    floor tolerates); widening is the finding.
    """
    by_pair = {(b.hook, b.requirement): b for b in bindings}
    offenders: list[str] = []
    for entry in entries:
        binding = by_pair.get((entry.hook, entry.requirement))
        if binding is None:
            continue  # reported by unrecorded_entries(); not this check's finding
        pyproject = repo_root / binding.declared_in
        declared = _declared_specifiers(pyproject)
        requirement = Requirement(entry.requirement)
        name = canonicalize_name(requirement.name)
        source = declared.get(name)
        if source is None:
            offenders.append(f"{entry} — {binding.declared_in} no longer declares {name}; the clamp has no source")
            continue
        escaping = [
            str(version)
            for version in _probe_versions(requirement.specifier, source)
            if requirement.specifier.contains(version) and not source.contains(version)
        ]
        if escaping:
            offenders.append(
                f"{entry} allows {', '.join(escaping)}, which {binding.declared_in} does not ({name}{source})"
            )
    return offenders


@pytest.fixture(scope="module")
def entries() -> tuple[Entry, ...]:
    """The entries as the checked-in config spells them."""
    return additional_dependency_entries(_load_config(_CONFIG.read_text(encoding="utf-8")))


class TestTheSweepReadsTheWholeFile:
    """Anti-vacuity: every assertion below is worthless over an empty entry list."""

    def test_at_least_the_measured_number_of_entries_is_found(self, entries: tuple[Entry, ...]) -> None:
        hooks = {entry.hook for entry in entries}
        assert len(hooks) >= _MINIMUM_HOOKS_WITH_DEPENDENCIES, (
            f"only {len(hooks)} hook(s) with additional_dependencies found in {_CONFIG.name}; "
            f"{_MINIMUM_HOOKS_WITH_DEPENDENCIES} were measured on 2026-09-20. Either hooks were removed "
            "(lower the floor deliberately) or this parser stopped matching the file's shape."
        )

    def test_every_carrying_hook_is_a_python_hook(self, entries: tuple[Entry, ...]) -> None:
        """The subset clamp compares PEP 440 specifiers against pyproject files.

        Under ``language: node`` or ``language: golang`` the same key holds npm
        or Go specs, which those rules cannot read — so such a hook must not slip
        through being mis-measured. It fails here instead, loudly, and the
        decision about how to bound it is taken in review.
        """
        foreign = sorted({f"{e.hook} (language: {e.language})" for e in entries if e.language != "python"})
        assert not foreign, (
            "additional_dependencies under a non-Python language: " + ", ".join(foreign) + ". "
            "These are not PEP 440 requirements; extend this guard before adding them."
        )


class TestEveryEntryIsRecorded:
    """The opt-in-list defence: the config is enumerated, not a list of hook ids."""

    def test_no_hook_installs_something_this_file_does_not_record(self, entries: tuple[Entry, ...]) -> None:
        assert not unrecorded_entries(entries), (
            "additional_dependencies not recorded in _BINDINGS: "
            + "; ".join(unrecorded_entries(entries))
            + ". Add a Binding naming the tree that bounds it (#1572)."
        )

    def test_no_recorded_binding_is_stale(self, entries: tuple[Entry, ...]) -> None:
        assert not stale_bindings(entries), (
            "_BINDINGS records entries .pre-commit-config.yaml no longer carries: "
            + "; ".join(stale_bindings(entries))
            + ". A stale binding is a rule guarding nothing."
        )


class TestEveryEntryIsBounded:
    """Class (b) of the boundary: bounded, not hashed — and never unbounded."""

    def test_every_requirement_has_a_floor_and_a_ceiling(self, entries: tuple[Entry, ...]) -> None:
        assert not unbounded_requirements(entries), (
            "unbounded additional_dependencies inside the required `static` lane: "
            + "; ".join(unbounded_requirements(entries))
            + ". Renovate's pre-commit manager maintains `rev:` only, so nothing else would notice (#1572)."
        )

    def test_every_requirement_stays_inside_its_declaring_tree(self, entries: tuple[Entry, ...]) -> None:
        offenders = out_of_range_requirements(entries, _REPO_ROOT)
        assert not offenders, "additional_dependencies wider than the tree that declares the package: " + "; ".join(
            offenders
        )


class TestTheClampReachesARealDeclaration:
    """The positive control. Without it, a binding pointing at a tree that does
    not declare the package would make :func:`out_of_range_requirements` report
    nothing interesting — and the #1377 lesson is that a check which cannot
    reach the line it claims to test passes while proving nothing."""

    def test_every_binding_resolves_to_a_declared_package(self) -> None:
        missing: list[str] = []
        for binding in _BINDINGS:
            pyproject = _REPO_ROOT / binding.declared_in
            assert pyproject.is_file(), f"{binding.hook}: {binding.declared_in} does not exist"
            name = canonicalize_name(Requirement(binding.requirement).name)
            if name not in _declared_specifiers(pyproject):
                missing.append(f"{binding.hook}: {name} is not declared in {binding.declared_in}")
        assert not missing, "; ".join(missing)

    def test_a_probe_grid_can_separate_two_adjacent_floors(self) -> None:
        """The sampling is only a subset test if the grid contains a separating
        version. ``>=0.14.0`` against ``>=0.15.0`` is the exact shape the
        falsification below relies on."""
        loose, tight = SpecifierSet(">=0.14.0"), SpecifierSet(">=0.15.0")
        separating = [v for v in _probe_versions(loose, tight) if loose.contains(v) and not tight.contains(v)]
        assert separating, "the probe grid cannot distinguish >=0.14.0 from >=0.15.0; the subset test is vacuous"


class TestLooseningAnEntryIsRed:
    """The permanent falsifier (#1572's "red-first" acceptance condition).

    The first two cases mutate a COPY of the real, checked-in document — not a
    hand-written fixture — and assert that the SAME function the production
    assertions above call reports the mutation. A falsification test that checks
    a neighbouring expression is green while the rule is inert.

    The last two construct an ``Entry``/``Binding`` pair by hand, because the
    condition they falsify — a binding that escapes or cannot read its declaring
    tree — cannot be produced by editing ``.pre-commit-config.yaml`` alone; it
    needs a binding pointing somewhere else. They are still not fixtures in the
    dangerous sense: they call the real production function against the real
    checkout, so the pyproject files they clamp against are the ones on disk.
    """

    @staticmethod
    def _mutated(replacement: str) -> tuple[Entry, ...]:
        document = _load_config(_CONFIG.read_text(encoding="utf-8"))
        for repo in document.get("repos", []):
            for hook in repo.get("hooks", []):
                if hook.get("id") == "ruff-lint":
                    hook["additional_dependencies"] = [replacement]
        entries = additional_dependency_entries(document)
        assert any(e.hook == "ruff-lint" and e.requirement == replacement for e in entries), (
            "the mutation did not reach the parsed document; the falsifier would be vacuous"
        )
        return entries

    def test_dropping_the_ceiling_is_reported(self) -> None:
        entries = self._mutated("ruff>=0.15.0")
        assert any("ruff-lint: ruff>=0.15.0" in offender for offender in unbounded_requirements(entries))

    def test_lowering_the_floor_is_reported(self) -> None:
        entries = self._mutated("ruff>=0.14.0,<1.0.0")
        assert any("ruff-lint: ruff>=0.14.0,<1.0.0" in offender for offender in unrecorded_entries(entries))

    def test_escaping_the_declaring_tree_is_reported(self) -> None:
        """Widening past the tree must be reported by the CLAMP as well, not only
        by the equality check — otherwise updating ``_BINDINGS`` to match a
        loosened config would restore green while the hook installs a version no
        tree in this repository allows.

        Simulated by re-pointing a real binding at a tree that declares a
        narrower set of the same package: ``tests/e2e/pyproject.toml`` declares
        ``pytest>=8.3.0``, so a hook asking for ``pytest>=7.0.0`` escapes it.
        """
        entry = Entry(hook="e2e-selftest", requirement="pytest>=7.0.0,<10.0.0", language="python")
        binding = Binding(
            hook=entry.hook,
            requirement=entry.requirement,
            declared_in=_E2E,
            why="mutation of the real e2e-selftest binding",
        )
        offenders = out_of_range_requirements((entry,), _REPO_ROOT, (binding,))
        assert offenders and "allows 7.0.0" in offenders[0], offenders

    def test_a_binding_pointing_at_a_tree_without_the_package_is_reported(self) -> None:
        """The clamp says so instead of passing over a source it cannot read."""
        entry = Entry(hook="ruff-lint", requirement="ruff>=0.15.0,<1.0.0", language="python")
        binding = Binding(hook=entry.hook, requirement=entry.requirement, declared_in=_E2E, why="tests/e2e has no ruff")
        offenders = out_of_range_requirements((entry,), _REPO_ROOT, (binding,))
        assert offenders and "no longer declares ruff" in offenders[0], offenders
