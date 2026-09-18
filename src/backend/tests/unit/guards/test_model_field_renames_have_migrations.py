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
import re
import subprocess
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pytest
import yaml

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


#: The two request DTOs ``oidc_config.py`` carried beside the persisted model, and
#: the fields they declared. Named per field because the table is keyed per field:
#: a shared verdict must still be re-checkable entry by entry.
#:
#: The evidence is checked, not only asserted:
#: :class:`TestTheDeletedOidcRequestDtosWereNeverPersisted` holds the two facts the
#: reason below rests on.
_VANISHED_OIDC_REQUEST_FIELDS: tuple[tuple[str, str], ...] = tuple(
    (class_name, field_name)
    for class_name, fields in (
        (
            "OidcProviderConfigCreate",
            (
                "slug",
                "display_name",
                "provider_type",
                "issuer_url",
                "client_id",
                "client_secret",
                "scopes",
                "authorization_url",
                "token_url",
                "userinfo_url",
                "auto_discover",
                "enabled",
                "icon_url",
                "default_tenant_key",
            ),
        ),
        (
            "OidcProviderConfigUpdate",
            (
                "display_name",
                "provider_type",
                "issuer_url",
                "client_id",
                "client_secret",
                "scopes",
                "authorization_url",
                "token_url",
                "userinfo_url",
                "auto_discover",
                "enabled",
                "icon_url",
                "default_tenant_key",
            ),
        ),
    )
    for field_name in fields
)

_UNCALLED_OIDC_REQUEST_DTO = _NoStoredDocuments(
    "OidcProviderConfigCreate/Update were request DTOs sitting in the model module with "
    "no caller anywhere in the repository — the admin router has always built its bodies "
    "from app/api/v1/admin/oidc_providers/schemas.py — so no value ever reached a document "
    "through them. The PERSISTED model in the same file, OidcProviderConfig, is untouched "
    "and still declares every one of these names except client_secret, which the router "
    "encrypts into client_secret_encrypted and never stores in the clear. Deleted in "
    "302c742fd (#1497) on the review finding that maintaining them meant keeping a second, "
    "unprotected copy of the request shape. Measured read-only on the kind dev cluster "
    "2026-09-18: oidc_provider_configs holds zero documents."
)


#: Every field name that vanished from a model since the baseline commit.
#:
#: Add an entry when this test names a field you removed. ``_MigratedBy`` is the
#: normal answer; ``_NoStoredDocuments`` needs evidence that no persisted document
#: can be affected, and "I don't think anyone used it" is not evidence.
_CLASSIFIED: dict[tuple[str, str, str], _MigratedBy | _NoStoredDocuments] = {
    ("substrate.py", "Substrate", "cec_meq_per_100g"): _MigratedBy("0051"),
    ("actuator.py", "Actuator", "state"): _NoStoredDocuments(
        "Renamed to current_state in 426be8b4e (#561), the same commit whose v0015 "
        "CREATES the actuators collection — no actuator document can predate it."
    ),
    ("actuator.py", "Actuator", "last_changed_at"): _NoStoredDocuments(
        "Renamed to last_state_change in 426be8b4e (#561), same commit and same reason as `state` above."
    ),
    **{
        ("oidc_config.py", class_name, field_name): _UNCALLED_OIDC_REQUEST_DTO
        for class_name, field_name in _VANISHED_OIDC_REQUEST_FIELDS
    },
}


#: What makes an excuse re-checkable: a commit SHA (>= 7 hex), an issue (``#1234``)
#: or a migration version (``v0015``). Anchored to word boundaries so a number
#: inside a word cannot pass for one.
_EVIDENCE = re.compile(r"\b(?:[0-9a-f]{7,40}|#\d+|v\d{4})\b")


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


def _annotated_field_names(source: str) -> set[tuple[str, str]]:
    """``(class name, stored name)`` for every field a model can persist.

    **Per class, not per module.** ``substrate.py`` declares ``tenant_key`` on both
    ``Substrate`` and ``SubstrateBatch``: pooled per file, dropping it from one of
    them leaves the name present and the rename invisible — the population would
    have covered the file and decided nothing about either model.

    Two kinds of name, because either one moving renames the stored key:

    * class-level **annotated** attribute names (a bare ``x = 1`` is not a
      Pydantic field, and a module-level constant is not one either), and
    * the string **aliases** declared on them.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover - a historical revision that did not parse
        return set()
    names: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
                continue
            names.add((node.name, stmt.target.id))
            if isinstance(stmt.value, ast.Call):
                for keyword in stmt.value.keywords:
                    if (
                        keyword.arg in _ALIAS_KEYWORDS
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    ):
                        names.add((node.name, keyword.value.value))
    return names


@cache
def _vanished_fields() -> dict[tuple[str, str, str], None]:
    """``(file, class, field)`` for every field a model lost since the baseline.

    Cached: the derivation shells out to git a few hundred times — measured 4.9 s
    on this tree at 54 revisions (2026-09-18), and every test in this module asks
    for the same answer, so it is paid once per session.
    """
    revisions = _git("log", "--format=%H", f"{_BASELINE_COMMIT}..HEAD", "--", _MODELS_DIR).split()

    historical: dict[str, set[tuple[str, str]]] = {}
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

    vanished: dict[tuple[str, str, str], None] = {}
    for path, names in historical.items():
        current_file = _REPO_ROOT / path
        current = _annotated_field_names(current_file.read_text(encoding="utf-8")) if current_file.exists() else set()
        for class_name, field_name in sorted(names - current):
            vanished[(Path(path).name, class_name, field_name)] = None
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


#: Why a run cannot decide anything about renames, said once.
_SHALLOW_REASON = (
    "this checkout is shallow, so no field rename is visible in it — the run would "
    "measure nothing and report green. The `Write-route and tree guards` lane checks "
    "out full history and runs this file with --max-skipped 0; that is where the "
    "population is measured."
)


@cache
def _history_is_available() -> bool:
    """Whether this checkout can show a rename at all."""
    return (
        _git("rev-parse", "--is-shallow-repository").strip() == "false"
        and _git("cat-file", "-t", _BASELINE_COMMIT).strip() == "commit"
    )


@pytest.fixture
def history():
    """Skip a history-dependent test on a checkout that has none."""
    if not _history_is_available():
        pytest.skip(_SHALLOW_REASON)


def _migration_module(version: str) -> Path:
    matches = sorted(_VERSIONS_DIR.glob(f"v{version}_*.py"))
    assert len(matches) == 1, f"expected exactly one migration module for version {version}, found {matches}"
    return matches[0]


class TestTheDerivationItself:
    """A guard whose measurement is broken reports green forever (NFR-018 §1)."""

    def test_the_history_this_derivation_needs_is_present(self):
        """Either the history is here, or this run is not the one that measures.

        Measured on PR #1523: **three** lanes execute this file, and only two of
        them can be given a checkout depth. `Write-route and tree guards`
        (required) and `lint-test` both set ``fetch-depth: 0``; the `Coverage`
        lane runs the whole suite through ``nolte/gh-plumbing``'s reusable
        workflow, whose checkout step belongs to another repository.

        So the shallow case skips *here* and is caught *there*: the guards lane
        runs with ``--max-skipped 0``, which turns a skip in it — the only way its
        checkout could go shallow — into a red run.
        ``TestTheLaneThatRunsThisUnshallow`` below keeps that lane's
        ``fetch-depth: 0`` from being dropped, and needs no history itself.
        """
        if not _history_is_available():
            pytest.skip(_SHALLOW_REASON)

        assert _git("cat-file", "-t", _BASELINE_COMMIT).strip() == "commit", (
            f"the baseline commit {_BASELINE_COMMIT} is not in this checkout"
        )

    @pytest.mark.usefixtures("history")
    def test_it_still_sees_the_rename_it_was_built_for(self):
        """The self-test: #1468's own rename must appear in the derived population.

        History is append-only, so this fact cannot expire; if it stops showing
        up, the derivation broke and everything else here went quiet with it.
        """
        assert ("substrate.py", "Substrate", "cec_meq_per_100g") in _vanished_fields()

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

        assert {("Substrate", "key"), ("Substrate", "_key")} <= names

    def test_only_annotated_assignments_count_as_fields(self):
        """A class constant is not a persisted field and must not enter the population."""
        source = "class M(BaseModel):\n    field: str = Field(alias='stored_name')\n    NOT_A_FIELD = 3\n"

        assert _annotated_field_names(source) == {("M", "field"), ("M", "stored_name")}

    def test_two_classes_in_one_file_are_held_apart(self):
        """The spelling SCR-004 found: ``substrate.py`` declares ``tenant_key`` on
        ``Substrate`` **and** on ``SubstrateBatch``. Pooled per file, dropping it
        from one leaves the name present and the rename invisible."""
        before = "class A(BaseModel):\n    tenant_key: str\n\n\nclass B(BaseModel):\n    tenant_key: str\n"
        after = "class A(BaseModel):\n    owner_key: str\n\n\nclass B(BaseModel):\n    tenant_key: str\n"

        gone = _annotated_field_names(before) - _annotated_field_names(after)

        assert gone == {("A", "tenant_key")}

    def test_the_real_model_is_the_case_this_protects(self):
        substrate = _REPO_ROOT / _MODELS_DIR / "substrate.py"
        names = _annotated_field_names(substrate.read_text(encoding="utf-8"))

        assert {("Substrate", "tenant_key"), ("SubstrateBatch", "tenant_key")} <= names

    def test_a_field_named_in_code_is_coverage(self):
        """The other direction, so the check is not simply always-false."""
        assert "cec_meq_per_100g" in _code_identifiers(_migration_module("0051"))


class TestEveryVanishedFieldIsAccountedFor:
    @pytest.mark.usefixtures("history")
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
        for (file_name, class_name, field_name), verdict in sorted(_CLASSIFIED.items()):
            if not isinstance(verdict, _MigratedBy):
                continue
            module = _migration_module(verdict.migration)
            if field_name not in _code_identifiers(module):
                offenders.append(f"{file_name}:{class_name}.{field_name} claims v{verdict.migration} ({module.name})")

        assert offenders == [], (
            "A migration is recorded as handling a renamed field but never names it in its code "
            f"(a docstring mention does not count): {offenders}"
        )

    @pytest.mark.usefixtures("history")
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
        """An excuse has to point at something checkable.

        Length was the first criterion here and it decided nothing — a long
        sentence of belief passed it. What makes an excuse re-checkable is a
        **commit** somebody can read, an **issue** somebody can open, or the
        **migration** that created the collection; so that is what is required,
        and the reason still has to say something beside the reference.
        """
        references = _EVIDENCE.findall(verdict.reason)

        assert references, (
            f"{key}: the reason names no commit SHA, issue number or migration version, "
            f"so nobody can re-check it: {verdict.reason!r}"
        )
        assert len(verdict.reason) > len("".join(references)) + 40, (
            f"{key}: a reference on its own is not a reason — say what it shows: {verdict.reason!r}"
        )


class TestTheDeletedOidcRequestDtosWereNeverPersisted:
    """The evidence behind the `_UNCALLED_OIDC_REQUEST_DTO` verdict, as a check.

    A `_NoStoredDocuments` reason is prose, and prose is what nobody re-reads. The
    two facts this one rests on are decidable, so they are decided here: a later
    change that makes the excuse false — persisting one of those names under a
    different model, or dropping it from the persisted one — goes red instead of
    leaving a sentence standing.
    """

    def _oidc_model_fields(self) -> set[str]:
        source = (_REPO_ROOT / _MODELS_DIR / "oidc_config.py").read_text(encoding="utf-8")
        return {field for class_name, field in _annotated_field_names(source) if class_name == "OidcProviderConfig"}

    def test_the_persisted_model_still_declares_every_excused_name(self):
        """Every name but one is still on the model the repository writes."""
        excused = {field for _, field in _VANISHED_OIDC_REQUEST_FIELDS}
        assert excused - self._oidc_model_fields() == {"client_secret"}

    def test_the_one_exception_is_stored_encrypted_under_another_name(self):
        """`client_secret` is the exception on purpose: it is never stored as-is."""
        fields = self._oidc_model_fields()
        assert "client_secret" not in fields
        assert "client_secret_encrypted" in fields

    def test_the_deleted_classes_are_really_gone(self):
        """Otherwise the verdict would excuse fields that never vanished."""
        source = (_REPO_ROOT / _MODELS_DIR / "oidc_config.py").read_text(encoding="utf-8")
        classes = {class_name for class_name, _ in _annotated_field_names(source)}
        assert classes.isdisjoint({"OidcProviderConfigCreate", "OidcProviderConfigUpdate"})


class TestTheLaneThatRunsThisUnshallow:
    """The half of the enforcement that a shallow checkout cannot silence.

    Everything above needs history; this needs only the workflow file, so it runs
    in every lane — including the one whose checkout is a shallow default.
    """

    _WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "backend-guards.yml"

    def _guards_job(self) -> dict:
        workflow = yaml.safe_load(self._WORKFLOW.read_text(encoding="utf-8"))
        jobs = [
            job
            for job in workflow["jobs"].values()
            if any("tests/unit/guards" in str(step.get("run", "")) for step in job.get("steps", []))
        ]
        assert len(jobs) == 1, f"expected exactly one job running tests/unit/guards, found {len(jobs)}"
        return jobs[0]

    def test_the_guards_job_checks_out_full_history(self):
        """Without it, every history-dependent test here skips — and a skip in
        that lane is red only because the lane also declares ``--max-skipped 0``,
        which the test below holds in place."""
        checkouts = [step for step in self._guards_job()["steps"] if "actions/checkout" in str(step.get("uses", ""))]

        assert checkouts, "the guards job has no checkout step"
        for step in checkouts:
            assert step.get("with", {}).get("fetch-depth") == 0, (
                "the guards lane must check out full history: "
                "tests/unit/guards/test_model_field_renames_have_migrations.py derives the vanished "
                "model fields from it, and on a shallow checkout it can only skip (#1468)."
            )

    def test_the_guards_job_still_reddens_on_a_skip(self):
        """``--max-skipped 0`` is what makes the skip above an alarm rather than a
        quiet pass (#1434)."""
        runs = [
            str(step.get("run", ""))
            for step in self._guards_job()["steps"]
            if "tests/unit/guards" in str(step.get("run", ""))
        ]

        assert runs
        for run in runs:
            assert "--max-skipped 0" in run
