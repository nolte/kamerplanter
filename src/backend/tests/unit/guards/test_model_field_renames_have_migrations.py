"""A persisted model field that disappears must be named by a migration (#1468).

The defect #1468 reports is a *process* gap, not a coding mistake: #1174 renamed
``Substrate.cec_meq_per_100g`` → ``cec_meq_per_100cm3`` in the model and in the
seed YAML, both halves of the change were reviewed and green, and the stored
documents were left under a name no reader asks for any more. ``seed_substrates``
skips records that exist, so nothing repaired them either — the whole catalogue's
CEC read as ``None`` for months. ``app/migrations/README.md`` already states the
rule (M-9: "wird ein persistierter Enum-Wert oder ein Feld entfernt/umbenannt,
MUSS dieselbe Änderung eine Migration mitliefern"); it had no gate.

This is the gate. It is **derived, not hand-kept**: the population of vanished
field names comes out of git history, so a rename that nobody thinks to declare
is exactly the case that turns this red.

## How the population is derived

For every revision that touched ``app/domain/models/`` since the migration
framework's baseline commit, both the revision's own version of each touched file
and its parent's are parsed, and every class-level annotated attribute name is
collected. The parent state is what makes a rename visible at all: the commit that
performs one contains only the new name.

Subtracting the names the file declares *today* leaves the names that vanished.
Every one of them must be classified in :data:`_CLASSIFIED` — either as migrated
(and then the named migration must reference the old name **in code**, not in
prose) or with a reason why no data could be affected.

## Why the baseline commit is the floor

``versions/v0001_baseline.py`` landed on 2026-07-05 with the framework itself.
Before it there was no mechanism to migrate anything and the application was
pre-release; the nine names that vanished earlier (measured: ``task.plant_key``,
``species.propagation_methods``, ``nutrient_plan.tank_key`` and six more) are
archaeology, and listing them would be a table of excuses rather than a gate.
Measured on the dev cluster 2026-09-18: no document in any of its 300 collections
carries any of them under the model that lost it.

## What this guard does NOT claim

That a classified rename was migrated *correctly* — that is the migration's own
test. And it sees renames of **fields**, not of collections or of enum *values*;
M-9 covers those too and they would need their own derivation.
"""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pytest

import app

_BACKEND_ROOT = Path(app.__file__).resolve().parents[1]
_REPO_ROOT = _BACKEND_ROOT.parents[1]
_MODELS_DIR = "src/backend/app/domain/models"
_VERSIONS_DIR = _BACKEND_ROOT / "app" / "migrations" / "versions"

#: ``feat(migrations): versioned, lock-guarded DB migration framework`` (#374),
#: the commit that added ``versions/v0001_baseline.py``. Everything before it
#: predates any ability to migrate; see the module docstring.
_BASELINE_COMMIT = "548deed22cf891e497a933630ae3455c843b4c7f"


@dataclass(frozen=True)
class _MigratedBy:
    """The field was renamed/removed and version ``migration`` moves the data."""

    migration: str


@dataclass(frozen=True)
class _NoStoredDocuments:
    """No document could have carried the field — with the evidence for that."""

    reason: str


#: Every field name that vanished from a model since the baseline commit.
#:
#: Add an entry when this test names a field you removed. ``_MigratedBy`` is the
#: normal answer; ``_NoStoredDocuments`` needs evidence that no persisted document
#: can be affected, and "I don't think anyone used it" is not evidence.
_CLASSIFIED: dict[tuple[str, str], _MigratedBy | _NoStoredDocuments] = {
    ("substrate.py", "cec_meq_per_100g"): _MigratedBy("0051"),
    ("actuator.py", "state"): _NoStoredDocuments(
        "Renamed to current_state in 426be8b4e (#561), the same commit whose v0015 "
        "CREATES the actuators collection — no actuator document can predate it."
    ),
    ("actuator.py", "last_changed_at"): _NoStoredDocuments(
        "Renamed to last_state_change in 426be8b4e (#561), same commit and same reason as `state` above."
    ),
}


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


#: ``Field`` keywords that decide the name a document is stored under. A field
#: whose *alias* moves renames the stored attribute while the Python name sits
#: still — ``Substrate.key`` is stored as ``_key`` — so the alias is part of the
#: population, not decoration.
_ALIAS_KEYWORDS = frozenset({"alias", "serialization_alias", "validation_alias"})


def _annotated_field_names(source: str) -> set[str]:
    """Every name a Pydantic model can persist an attribute under.

    Two things, because either one moving is a rename of the stored key:

    * class-level **annotated** attribute names (a bare ``x = 1`` is not a
      Pydantic field, and a module-level constant is not one either), and
    * the string **aliases** declared on them.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover - a historical revision that did not parse
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
                continue
            names.add(stmt.target.id)
            if isinstance(stmt.value, ast.Call):
                for keyword in stmt.value.keywords:
                    if (
                        keyword.arg in _ALIAS_KEYWORDS
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    ):
                        names.add(keyword.value.value)
    return names


@cache
def _vanished_fields() -> dict[tuple[str, str], None]:
    """``(file name, field name)`` for every field a model lost since the baseline.

    Cached: the derivation runs a few hundred ``git show`` calls and every test in
    this module asks for the same answer.
    """
    revisions = _git("log", "--format=%H", f"{_BASELINE_COMMIT}..HEAD", "--", _MODELS_DIR).split()

    historical: dict[str, set[str]] = {}
    for revision in revisions:
        touched = [
            path
            for path in _git("show", "--name-only", "--format=", revision).split()
            if path.startswith(_MODELS_DIR) and path.endswith(".py")
        ]
        for path in touched:
            # Both sides of the commit: the one that performs a rename holds only
            # the new name, so the parent is where the old one is still visible.
            for spec in (f"{revision}:{path}", f"{revision}^:{path}"):
                source = _git("show", spec)
                if source:
                    historical.setdefault(path, set()).update(_annotated_field_names(source))

    vanished: dict[tuple[str, str], None] = {}
    for path, names in historical.items():
        current_file = _REPO_ROOT / path
        current = _annotated_field_names(current_file.read_text(encoding="utf-8")) if current_file.exists() else set()
        for name in sorted(names - current):
            vanished[(Path(path).name, name)] = None
    return vanished


def _code_identifiers(path: Path) -> set[str]:
    """Every name and string literal in a module **except** its docstrings.

    The distinction is the point. ``v0047_reapply_corrected_substrate_values``
    mentions ``cec_meq_per_100g`` in its docstring — to say it is *deliberately
    not* migrating it. A substring search over the file would have read that
    sentence as coverage and reported the very gap #1468 is about as closed.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))

    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            first = node.body[0] if node.body else None
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                docstrings.add(id(first.value))

    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            found.add(node.value)
        elif isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.keyword) and node.arg:
            found.add(node.arg)
    return found


def _migration_module(version: str) -> Path:
    matches = sorted(_VERSIONS_DIR.glob(f"v{version}_*.py"))
    assert len(matches) == 1, f"expected exactly one migration module for version {version}, found {matches}"
    return matches[0]


class TestTheDerivationItself:
    """A guard whose measurement is broken reports green forever (NFR-018 §1)."""

    def test_the_history_this_derivation_needs_is_present(self):
        """A shallow checkout cannot see a rename, and would pass vacuously.

        A failure, not a skip: the backend workflow checks out with
        ``fetch-depth: 0`` on purpose, and a skip here reports like a pass.
        """
        assert _git("rev-parse", "--is-shallow-repository").strip() == "false", (
            "this checkout is shallow, so no field rename is visible in it. "
            "Unshallow it (`git fetch --unshallow`) — CI checks out full history for exactly this reason."
        )
        assert _git("cat-file", "-t", _BASELINE_COMMIT).strip() == "commit", (
            f"the baseline commit {_BASELINE_COMMIT} is not in this checkout"
        )

    def test_it_still_sees_the_rename_it_was_built_for(self):
        """The self-test: #1468's own rename must appear in the derived population.

        History is append-only, so this fact cannot expire; if it stops showing
        up, the derivation broke and everything else here went quiet with it.
        """
        assert ("substrate.py", "cec_meq_per_100g") in _vanished_fields()

    def test_prose_about_a_field_is_not_coverage(self):
        """The false positive this guard had to be built around.

        ``v0047`` names ``cec_meq_per_100g`` in its docstring to say it is
        *deliberately not* migrating it. A substring search — the obvious
        implementation — reads that as coverage.
        """
        v0047 = _migration_module("0047")

        assert "cec_meq_per_100g" in v0047.read_text(encoding="utf-8"), "precondition: v0047 mentions the old key"
        assert "cec_meq_per_100g" not in _code_identifiers(v0047)

    def test_an_alias_counts_as_a_stored_name(self):
        """The spelling of "the same thing" this pattern would otherwise miss.

        A field whose ``alias`` moves renames the **stored** attribute while the
        Python name sits still — and the alias is what ArangoDB holds. Measured on
        the real model: ``Substrate.key`` is stored as ``_key``.
        """
        substrate = _REPO_ROOT / _MODELS_DIR / "substrate.py"
        names = _annotated_field_names(substrate.read_text(encoding="utf-8"))

        assert {"key", "_key"} <= names

    def test_only_annotated_assignments_count_as_fields(self):
        """A class constant is not a persisted field and must not enter the population."""
        source = "class M(BaseModel):\n    field: str = Field(alias='stored_name')\n    NOT_A_FIELD = 3\n"

        assert _annotated_field_names(source) == {"field", "stored_name"}

    def test_a_field_named_in_code_is_coverage(self):
        """The other direction, so the check is not simply always-false."""
        assert "cec_meq_per_100g" in _code_identifiers(_migration_module("0051"))


class TestEveryVanishedFieldIsAccountedFor:
    def test_no_model_lost_a_field_without_a_verdict(self):
        unclassified = sorted(key for key in _vanished_fields() if key not in _CLASSIFIED)

        assert unclassified == [], (
            "These model fields vanished since the migration baseline and nothing says what "
            f"happened to the stored documents: {unclassified}. "
            "Renaming or removing a persisted field requires a migration in the same change "
            "(app/migrations/README.md, M-9) — #1174 renamed Substrate.cec_meq_per_100g without one "
            "and the whole substrate catalogue's CEC read as None until #1468. "
            "Ship the migration and record it in _CLASSIFIED, or record why no stored document "
            "can be affected."
        )

    def test_every_recorded_migration_touches_the_field_it_claims(self):
        offenders = []
        for (file_name, field_name), verdict in sorted(_CLASSIFIED.items()):
            if not isinstance(verdict, _MigratedBy):
                continue
            module = _migration_module(verdict.migration)
            if field_name not in _code_identifiers(module):
                offenders.append(f"{file_name}:{field_name} claims v{verdict.migration} ({module.name})")

        assert offenders == [], (
            "A migration is recorded as handling a renamed field but never names it in its code "
            f"(a docstring mention does not count): {offenders}"
        )

    def test_the_table_carries_no_stale_entry(self):
        """A classification for a field that is back — or was never gone — hides
        the next one behind a line nobody re-reads."""
        vanished = _vanished_fields()
        stale = sorted(key for key in _CLASSIFIED if key not in vanished)

        assert stale == [], f"_CLASSIFIED names fields that are not missing from their model: {stale}"

    @pytest.mark.parametrize(
        ("key", "verdict"),
        # Only the excused entries: a migrated one is checked by the test above,
        # and parametrising over both would buy a skip per migration for nothing —
        # this tier runs under a skip floor (#1434).
        sorted((key, verdict) for key, verdict in _CLASSIFIED.items() if isinstance(verdict, _NoStoredDocuments)),
    )
    def test_a_no_documents_verdict_states_its_evidence(self, key, verdict):
        """An excuse has to name the commit or the mechanism that makes it true."""
        assert len(verdict.reason) > 40, f"{key}: an excuse without evidence is not a verdict"
