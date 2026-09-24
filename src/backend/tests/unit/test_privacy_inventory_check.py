"""Tests for the privacy-inventory gate (``scripts/check_privacy_inventory.py``).

**What is under test.** The detection logic, driven against *constructed* engine
trees written into ``tmp_path`` — never against the real ``src/backend/app``. A
test asserting "the inventory has 29 entries" would go red on the next
legitimate collection and teach nobody anything; what is worth pinning is what
the check does with a given input.

**A gate nobody has watched fail is a gate nobody knows works.** Each rule has a
test that builds the exact pre-#1622 shape and asserts the check goes red and
names it: an entry with no executor (R1), a collection declared for export and
absent from erasure (R2), an inventory method with no caller (R3), and a cascade
that spells its collections out (R4), and a filtered step that does not say which
field it filters on (R5, #1663). Since #1645 R1's closed set is read from the
model's ``ErasureExecutor`` alias; :class:`TestR1ClosedSetComesFromTheModel` pins
that a name retired there is refused here without a second edit.

**The vacuum direction.** :class:`TestACommentCannotSatisfyIt` writes a module
whose only mention of ``build_export_manifest`` is a comment that even spells the
call, and pins that R3 still fires. That is the trap repaired in #1545, #1610 and
#1624 and generalised in #1456: prose answering for code.

Traces to issue #1622 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from tests.support.repo_scripts import load_repo_script

checker = load_repo_script("check_privacy_inventory")


# ── A miniature app tree ─────────────────────────────────────────────────────

ERASURE_HEAD = """
class ErasureEngine:
    ANONYMIZE_COLLECTIONS: list[AnonymizationRule] = [
        AnonymizationRule(collection="harvest_batches", user_field="harvester"),
    ]
    PSEUDONYMIZE_AUDIT_COLLECTIONS: list[PseudonymizationRule] = [
        PseudonymizationRule(collection="erasure_requests", user_field="user_key"),
    ]
    DELETE_STEPS: list[ErasureStep] = [
{steps}
    ]

    def build_erasure_plan(self, user_key):
        return self.DELETE_STEPS
"""

EXPORT_HEAD = """
class DataExportEngine:
    USER_DATA_MANIFEST: list[DataSourceDefinition] = [
{sources}
    ]

    def build_export_manifest(self, user_key):
        return self.USER_DATA_MANIFEST
"""

#: Ten well-formed steps, comfortably above the anti-vacuity floors. Each names
#: the field it filters the subject on (R5): two edges keyed on an endpoint, eight
#: documents keyed on a model field.
GOOD_STEPS = "\n".join(
    f'        ErasureStep(collection="c{i}", kind="{"edge" if i < 2 else "document"}", '
    f'executor="{"account_cascade" if i % 2 else "account_erasure"}", '
    f'user_field="{"_from" if i < 2 else "user_key"}"),'
    for i in range(10)
)

#: Ten manifest sources that the erasure inventory above declares, plus the
#: collections of its two rules — since #1719 every erasure target must be
#: disclosed too (R2, reverse direction).
GOOD_SOURCES = "\n".join(
    f'        DataSourceDefinition(collection="{name}", label="L"),'
    for name in (*(f"c{i}" for i in range(10)), "harvest_batches", "erasure_requests")
)

#: The closed executor set as ``domain/models/privacy.py`` declares it.
MODELS_HEAD = """
from typing import Literal

type ErasureExecutor = Literal[
{executors}
]
"""

GOOD_EXECUTORS = ("account_cascade", "account_erasure", "pest_image_cleanup", "storage_cleanup")

READER = """
from app.domain.engines.erasure_engine import ErasureEngine


def cascade(repo, key):
    for step in ErasureEngine().build_erasure_plan(key).steps:
        repo._remove_docs_for_user(step.collection, key)


def export_run(engine, user_key):
    return engine.build_export_manifest(user_key)
"""


#: #1700 (R6) — eight stored models, each carrying ``user_key`` and bound by a
#: repository to one of the document collections c2..c9 that GOOD_STEPS erases.
OWNED_MODELS = "\n".join(f"class M{i}(BaseModel):\n    user_key: str\n" for i in range(2, 10))
COLLECTIONS = "\n".join(f'C{i} = "c{i}"' for i in range(2, 10)) + '\nLOOSE = "loose"\n'
REPOSITORIES = "from app.data_access.arango import collections as col\n\n" + "\n".join(
    f"class R{i}(BaseArangoRepository[M{i}]):\n    def __init__(self, db):\n        super().__init__(db, col.C{i})\n"
    for i in range(2, 10)
)


def _tree(
    tmp_path: Path,
    *,
    steps: str = GOOD_STEPS,
    sources: str = GOOD_SOURCES,
    reader: str = READER,
    executors: tuple[str, ...] | None = GOOD_EXECUTORS,
    owned_models: str = OWNED_MODELS,
    repositories: str = REPOSITORIES,
) -> Path:
    app = tmp_path / "app"
    engines = app / "domain" / "engines"
    engines.mkdir(parents=True)
    models = app / "domain" / "models"
    models.mkdir(parents=True)
    (models / "owned.py").write_text(owned_models, encoding="utf-8")
    arango = app / "data_access" / "arango"
    arango.mkdir(parents=True)
    (arango / "collections.py").write_text(COLLECTIONS, encoding="utf-8")
    (arango / "repositories.py").write_text(repositories, encoding="utf-8")
    if executors is not None:
        (models / "privacy.py").write_text(
            textwrap.dedent(MODELS_HEAD).format(executors="\n".join(f'    "{name}",' for name in executors)),
            encoding="utf-8",
        )
    (engines / "erasure_engine.py").write_text(textwrap.dedent(ERASURE_HEAD).format(steps=steps), encoding="utf-8")
    (engines / "data_export_engine.py").write_text(
        textwrap.dedent(EXPORT_HEAD).format(sources=sources), encoding="utf-8"
    )
    (app / "executor.py").write_text(textwrap.dedent(reader), encoding="utf-8")
    return app


@pytest.fixture(autouse=True)
def _constructed_tree_floor(request, monkeypatch):
    """Constructed trees carry nine user-reference fields, not the real tree's ~50.

    ``MIN_USER_REFERENCE_FIELDS`` tracks the real tree (#1700 review); every test
    here builds a miniature one, so the R6 floor is lowered to what those carry.
    The tests that read the real tree or the constant itself keep the real value.
    """
    if "real" not in request.node.name:
        monkeypatch.setattr(checker, "MIN_USER_REFERENCE_FIELDS", 6)


def _codes(violations: list[str]) -> set[str]:
    return {v.split(" ", 1)[0] for v in violations}


class TestAConformingTreePasses:
    def test_no_violation(self, tmp_path: Path) -> None:
        assert checker.check(_tree(tmp_path)) == []


class TestR1Attribution:
    def test_an_entry_without_an_executor_is_named(self, tmp_path: Path) -> None:
        steps = GOOD_STEPS + '\n        ErasureStep(collection="orphan", kind="document"),'
        violations = checker.check(_tree(tmp_path, steps=steps))
        assert "R1" in _codes(violations)
        assert any("orphan" in v for v in violations)

    def test_an_executor_outside_the_closed_set_is_named(self, tmp_path: Path) -> None:
        steps = GOOD_STEPS + '\n        ErasureStep(collection="odd", kind="document", executor="someone"),'
        violations = checker.check(_tree(tmp_path, steps=steps))
        assert any(v.startswith("R1") and "someone" in v for v in violations)


class TestR1ClosedSetComesFromTheModel:
    """#1645 — the closed set is the model's alias, not a copy kept in the script."""

    def test_a_name_retired_from_the_model_is_refused_in_the_inventory(self, tmp_path: Path) -> None:
        """``retention_worker`` meant "declared, no executor yet"; once retired it may not linger."""
        steps = (
            GOOD_STEPS
            + '\n        ErasureStep(collection="late", kind="document", executor="retention_worker", '
            + 'user_field="user_key"),'
        )
        violations = checker.check(_tree(tmp_path, steps=steps))
        assert any(v.startswith("R1") and "retention_worker" in v and "late" in v for v in violations)

    def test_a_name_added_to_the_model_is_accepted_without_editing_the_script(self, tmp_path: Path) -> None:
        steps = (
            GOOD_STEPS
            + '\n        ErasureStep(collection="fresh", kind="document", executor="new_executor", '
            + 'user_field="user_key"),'
        )
        sources = GOOD_SOURCES + '\n        DataSourceDefinition(collection="fresh", label="F"),'
        tree = _tree(tmp_path, steps=steps, sources=sources, executors=(*GOOD_EXECUTORS, "new_executor"))
        assert checker.check(tree) == []

    def test_an_unreadable_closed_set_is_reported_not_treated_as_empty(self, tmp_path: Path) -> None:
        """No alias to read: every entry would be refused — or, worse, accepted by a default."""
        violations = checker.check(_tree(tmp_path, executors=None))
        assert any(v.startswith("R1") and "ErasureExecutor" in v for v in violations)


class TestR2Reconciliation:
    def test_export_only_personal_data_is_named(self, tmp_path: Path) -> None:
        """The ``tasks`` shape: declared for Art. 15, absent from Art. 17."""
        sources = GOOD_SOURCES + '\n        DataSourceDefinition(collection="tasks", label="T"),'
        violations = checker.check(_tree(tmp_path, sources=sources))
        assert any(v.startswith("R2") and "tasks" in v for v in violations)

    def test_an_edge_collection_counts_as_declared_personal_data(self, tmp_path: Path) -> None:
        sources = (
            GOOD_SOURCES + '\n        DataSourceDefinition(collection="c0", label="T", edge_collection="has_thing"),'
        )
        violations = checker.check(_tree(tmp_path, sources=sources))
        assert any(v.startswith("R2") and "has_thing" in v for v in violations)


class TestR2ReverseEveryErasureTargetIsDisclosed:
    """#1719 — the direction R2 did not check.

    ``user_favorites`` was deleted on erasure — the proof it is the subject's
    data — and absent from the Art. 15 manifest. The forward direction only asks
    whether what is disclosed can be erased, so it stayed green.
    """

    FAVOURITES_STEP = (
        '\n        ErasureStep(collection="user_favorites", kind="edge", executor="account_erasure", '
        'user_field="_from"),'
    )

    @staticmethod
    def _with_exclusions(app: Path, entries: str) -> Path:
        engine = app / "domain" / "engines" / "data_export_engine.py"
        engine.write_text(
            engine.read_text(encoding="utf-8").replace(
                "    def build_export_manifest",
                f"    EXCLUDED_FROM_DISCLOSURE: list[DisclosureExclusion] = [\n        {entries}\n    ]\n\n"
                "    def build_export_manifest",
            ),
            encoding="utf-8",
        )
        return app

    def test_an_erased_collection_that_is_not_disclosed_is_named(self, tmp_path: Path) -> None:
        """The ``user_favorites`` shape, exactly."""
        violations = checker.check(_tree(tmp_path, steps=GOOD_STEPS + self.FAVOURITES_STEP))
        assert any(v.startswith("R2") and "'user_favorites'" in v and "not disclosed" in v for v in violations)

    def test_an_anonymised_collection_that_is_not_disclosed_is_named(self, tmp_path: Path) -> None:
        sources = GOOD_SOURCES.replace('        DataSourceDefinition(collection="harvest_batches", label="L"),\n', "")
        assert sources != GOOD_SOURCES
        violations = checker.check(_tree(tmp_path, sources=sources))
        assert any(v.startswith("R2") and "'harvest_batches'" in v and "not disclosed" in v for v in violations)

    def test_disclosing_it_satisfies_the_rule(self, tmp_path: Path) -> None:
        sources = GOOD_SOURCES + '\n        DataSourceDefinition(collection="user_favorites", label="F"),'
        assert checker.check(_tree(tmp_path, steps=GOOD_STEPS + self.FAVOURITES_STEP, sources=sources)) == []

    def test_an_exclusion_with_its_reason_satisfies_the_rule(self, tmp_path: Path) -> None:
        app = _tree(tmp_path, steps=GOOD_STEPS + self.FAVOURITES_STEP)
        app = self._with_exclusions(app, 'DisclosureExclusion(collection="user_favorites", reason="plumbing"),')
        assert checker.check(app) == []

    def test_an_exclusion_without_a_reason_is_refused(self, tmp_path: Path) -> None:
        app = _tree(tmp_path, steps=GOOD_STEPS + self.FAVOURITES_STEP)
        app = self._with_exclusions(app, 'DisclosureExclusion(collection="user_favorites", reason=" "),')
        violations = checker.check(app)
        assert any(v.startswith("R2") and "reason" in v for v in violations)
        assert any(v.startswith("R2") and "'user_favorites'" in v and "not disclosed" in v for v in violations)

    def test_a_stale_exclusion_is_named(self, tmp_path: Path) -> None:
        app = self._with_exclusions(_tree(tmp_path), 'DisclosureExclusion(collection="gone", reason="was an edge"),')
        violations = checker.check(app)
        assert any(v.startswith("R2") and "'gone'" in v and "stale" in v for v in violations)

    def test_an_exclusion_of_a_disclosed_collection_is_named(self, tmp_path: Path) -> None:
        app = self._with_exclusions(_tree(tmp_path), 'DisclosureExclusion(collection="c3", reason="twice"),')
        violations = checker.check(app)
        assert any(v.startswith("R2") and "'c3'" in v and "both" in v for v in violations)


class TestR3Readership:
    def test_an_inventory_with_no_caller_is_named(self, tmp_path: Path) -> None:
        violations = checker.check(_tree(tmp_path, reader="x = 1\n"))
        r3 = [v for v in violations if v.startswith("R3")]
        assert len(r3) == 2
        assert any("build_erasure_plan" in v for v in r3)
        assert any("build_export_manifest" in v for v in r3)


class TestACommentCannotSatisfyIt:
    def test_a_comment_spelling_the_call_does_not_count(self, tmp_path: Path) -> None:
        reader = '''
from app.domain.engines.erasure_engine import ErasureEngine


def cascade(repo, key):
    for step in ErasureEngine().build_erasure_plan(key).steps:
        repo._remove_docs_for_user(step.collection, key)


def export_run(engine, user_key):
    """Walks build_export_manifest(user_key) for the Art. 15 scope."""
    # The scope comes from build_export_manifest(user_key).
    return None
'''
        violations = checker.check(_tree(tmp_path, reader=reader))
        assert any(v.startswith("R3") and "build_export_manifest" in v for v in violations)
        assert not any("build_erasure_plan" in v for v in violations)


class TestR4NoHandWrittenCollection:
    def test_a_string_literal_collection_is_named(self, tmp_path: Path) -> None:
        reader = (
            READER
            + """

def legacy(repo, key):
    repo._remove_docs_for_user("api_keys", key)
"""
        )
        violations = checker.check(_tree(tmp_path, reader=reader))
        assert any(v.startswith("R4") and "legacy" in v for v in violations)

    def test_a_collections_constant_is_named(self, tmp_path: Path) -> None:
        reader = (
            READER
            + """

def legacy(repo, key):
    repo._remove_docs_for_user(col.API_KEYS, key)
"""
        )
        violations = checker.check(_tree(tmp_path, reader=reader))
        assert any(v.startswith("R4") and "legacy" in v for v in violations)

    def test_an_edge_removal_beside_it_is_named(self, tmp_path: Path) -> None:
        reader = (
            READER
            + """

def legacy(repo, key, user_id):
    repo.delete_edges(col.HAS_SESSION, user_id)
    repo._remove_docs_for_user(step.collection, key)
"""
        )
        violations = checker.check(_tree(tmp_path, reader=reader))
        assert any(v.startswith("R4") and "legacy" in v for v in violations)

    def test_an_edge_removal_elsewhere_is_left_alone(self, tmp_path: Path) -> None:
        """A repository deleting its own edges is not an erasure cascade."""
        reader = (
            READER
            + """

def unrelated(repo, parent_id):
    repo.delete_edges(col.HAS_PHASE, parent_id)
"""
        )
        violations = checker.check(_tree(tmp_path, reader=reader))
        assert not any(v.startswith("R4") and "unrelated" in v for v in violations)


class TestR5EveryFilteredStepNamesItsUserField:
    """#1663 — a step that removes "the user's rows" must say how they are found.

    Before #1663 ``ErasureStep`` carried no user field at all: the one executor
    that existed hard-coded ``doc.user_key`` / ``e._from`` for its slice, and
    every other step was a name without a filter. An executor walking such a
    step either matches nothing (silent under-erasure) or has to guess — and a
    guessed filter on the wrong field deletes somebody else's data.
    """

    def test_a_document_step_without_a_user_field_is_named(self, tmp_path: Path) -> None:
        steps = GOOD_STEPS + '\n        ErasureStep(collection="unkeyed", kind="document", executor="account_erasure"),'
        violations = checker.check(_tree(tmp_path, steps=steps))
        assert any(v.startswith("R5") and "unkeyed" in v for v in violations)

    def test_an_edge_step_without_a_user_field_is_named(self, tmp_path: Path) -> None:
        steps = GOOD_STEPS + '\n        ErasureStep(collection="has_unkeyed", kind="edge", executor="account_cascade"),'
        violations = checker.check(_tree(tmp_path, steps=steps))
        assert any(v.startswith("R5") and "has_unkeyed" in v for v in violations)

    def test_an_empty_user_field_is_named(self, tmp_path: Path) -> None:
        steps = (
            GOOD_STEPS
            + '\n        ErasureStep(collection="blank", kind="document", executor="account_erasure", user_field=""),'
        )
        violations = checker.check(_tree(tmp_path, steps=steps))
        assert any(v.startswith("R5") and "blank" in v for v in violations)

    def test_an_edge_keyed_on_a_document_field_is_named(self, tmp_path: Path) -> None:
        """An edge reaches the user through ``_from`` or ``_to``, never through a body field."""
        steps = (
            GOOD_STEPS
            + '\n        ErasureStep(collection="has_odd", kind="edge", executor="account_cascade", '
            + 'user_field="user_key"),'
        )
        violations = checker.check(_tree(tmp_path, steps=steps))
        assert any(v.startswith("R5") and "has_odd" in v for v in violations)

    def test_an_anonymisation_rule_without_a_user_field_is_named(self, tmp_path: Path) -> None:
        app = _tree(tmp_path)
        engine = app / "domain" / "engines" / "erasure_engine.py"
        engine.write_text(
            engine.read_text(encoding="utf-8").replace(
                'AnonymizationRule(collection="harvest_batches", user_field="harvester")',
                'AnonymizationRule(collection="quality_assessments", user_field=FIELD)',
            ),
            encoding="utf-8",
        )
        violations = checker.check(app)
        assert any(v.startswith("R5") and "quality_assessments" in v for v in violations)

    def test_a_phase_and_the_user_document_need_no_user_field(self, tmp_path: Path) -> None:
        steps = (
            GOOD_STEPS
            + '\n        ErasureStep(collection="_storage_cleanup", kind="phase", executor="storage_cleanup"),'
            + '\n        ErasureStep(collection="users", kind="user", executor="account_cascade"),'
        )
        sources = GOOD_SOURCES + '\n        DataSourceDefinition(collection="users", label="Profile"),'
        assert checker.check(_tree(tmp_path, steps=steps, sources=sources)) == []

    def test_a_step_whose_kind_the_reader_cannot_see_is_not_waved_through(self, tmp_path: Path) -> None:
        """A non-literal ``kind`` must not read as "phase" and skip R5 silently."""
        steps = GOOD_STEPS + '\n        ErasureStep(collection="opaque", kind=KIND, executor="account_erasure"),'
        violations = checker.check(_tree(tmp_path, steps=steps))
        assert any(v.startswith("R5") and "opaque" in v for v in violations)


class TestR6EveryStoredUserReferenceIsInventoried:
    """#1700 — an anchor outside the two lists R2 compares with each other.

    Measured before the repair: twelve personal-data surfaces were in neither
    the export manifest nor the erasure inventory, and R2 stayed green because
    it only compared those two. These trees rebuild that shape.
    """

    def _with_loose_model(self, tmp_path: Path, field: str = "user_key", exclusion: str = "") -> Path:
        models = OWNED_MODELS + f"\nclass Loose(BaseModel):\n    {field}: str\n"
        repositories = (
            REPOSITORIES
            + "\nclass LooseRepository(BaseArangoRepository[Loose]):\n"
            + "    def __init__(self, db):\n        super().__init__(db, col.LOOSE)\n"
        )
        app = _tree(tmp_path, owned_models=models, repositories=repositories)
        if exclusion:
            engine = app / "domain" / "engines" / "erasure_engine.py"
            engine.write_text(
                engine.read_text(encoding="utf-8").replace(
                    "    def build_erasure_plan",
                    f"    EXCLUDED_USER_REFERENCES: list[ErasureExclusion] = [\n        {exclusion}\n    ]\n\n"
                    "    def build_erasure_plan",
                ),
                encoding="utf-8",
            )
        return app

    def test_a_stored_user_key_in_neither_inventory_is_named(self, tmp_path: Path) -> None:
        """The #1700 shape: ``calendar_feeds.user_key``, declared nowhere, R2 green."""
        violations = checker.check(self._with_loose_model(tmp_path))
        assert [v for v in violations if not v.startswith("R6")] == []
        assert any(v.startswith("R6") and "'loose.user_key'" in v for v in violations)

    def test_each_field_shape_of_the_pattern_is_caught(self, tmp_path: Path) -> None:
        for i, field in enumerate(("owner_user_key", "harvested_by_key", "service_account_key", "promoted_by")):
            violations = checker.check(self._with_loose_model(tmp_path / str(i), field=field))
            assert any(v.startswith("R6") and f"'loose.{field}'" in v for v in violations), field

    def test_an_exclusion_with_its_reason_satisfies_it(self, tmp_path: Path) -> None:
        exclusion = 'ErasureExclusion(collection="loose", user_field="user_key", reason="free text"),'
        assert checker.check(self._with_loose_model(tmp_path, exclusion=exclusion)) == []

    def test_an_exclusion_without_a_reason_is_refused(self, tmp_path: Path) -> None:
        exclusion = 'ErasureExclusion(collection="loose", user_field="user_key", reason=" "),'
        violations = checker.check(self._with_loose_model(tmp_path, exclusion=exclusion))
        assert any(v.startswith("R6") and "reason" in v for v in violations)

    def test_a_stale_exclusion_is_named(self, tmp_path: Path) -> None:
        """An exclusion for a field no model has would hide the next field of that name."""
        app = _tree(tmp_path)
        engine = app / "domain" / "engines" / "erasure_engine.py"
        engine.write_text(
            engine.read_text(encoding="utf-8").replace(
                "    def build_erasure_plan",
                "    EXCLUDED_USER_REFERENCES: list[ErasureExclusion] = [\n"
                '        ErasureExclusion(collection="gone", user_field="created_by", reason="was free text"),\n'
                "    ]\n\n    def build_erasure_plan",
            ),
            encoding="utf-8",
        )
        violations = checker.check(app)
        assert any(v.startswith("R6") and "gone.created_by" in v and "stale" in v for v in violations)

    def test_a_model_no_repository_binds_is_reported_not_skipped(self, tmp_path: Path) -> None:
        """Fail closed: an unplaceable model is exactly where a new surface would hide."""
        models = OWNED_MODELS + "\nclass Unbound(BaseModel):\n    created_by: str\n"
        violations = checker.check(_tree(tmp_path, owned_models=models))
        assert any(v.startswith("R6") and "'Unbound'" in v for v in violations)

    def test_an_inline_repository_binding_is_read(self, tmp_path: Path) -> None:
        """``BaseArangoRepository[M](db, col.X, M)`` — the second spelling in ``data_access``."""
        models = OWNED_MODELS + "\nclass Inline(BaseModel):\n    user_key: str\n"
        repositories = REPOSITORIES + "\nINLINE = BaseArangoRepository[Inline](db, col.LOOSE, Inline)\n"
        violations = checker.check(_tree(tmp_path, owned_models=models, repositories=repositories))
        assert any(v.startswith("R6") and "'loose.user_key' (Inline)" in v for v in violations)

    def test_a_clear_field_of_a_rule_counts_as_covered(self, tmp_path: Path) -> None:
        """``harvest_batches.harvester`` style: the free-text companion is emptied by the rule."""
        models = OWNED_MODELS + "\nclass Harvest(BaseModel):\n    harvested_by: str\n"
        repositories = (
            REPOSITORIES
            + "\nclass HarvestRepository(BaseArangoRepository[Harvest]):\n"
            + '    def __init__(self, db):\n        super().__init__(db, "harvest_batches")\n'
        )
        app = _tree(tmp_path, owned_models=models, repositories=repositories)
        engine = app / "domain" / "engines" / "erasure_engine.py"
        engine.write_text(
            engine.read_text(encoding="utf-8").replace(
                'AnonymizationRule(collection="harvest_batches", user_field="harvester")',
                'AnonymizationRule(collection="harvest_batches", user_field="harvester", '
                'clear_fields=["harvested_by"])',
            ),
            encoding="utf-8",
        )
        assert checker.check(app) == []

    def test_no_models_at_all_is_a_floor_violation(self, tmp_path: Path) -> None:
        violations = checker.check(_tree(tmp_path, owned_models=""))
        assert any(v.startswith("FLOOR") and "user-reference" in v for v in violations)

    def test_the_real_tree_sits_just_above_the_floor(self) -> None:
        """#1700 review — a floor of 6 under 52 would let 46 fields vanish unnoticed.

        The floor tracks the measured count with a small margin, so a reader that
        loses a whole module (or the base-class walk) trips it.
        """
        from pathlib import Path as _Path

        app_root = _Path(__file__).resolve().parents[2] / "app"
        references = checker._user_reference_fields(app_root)
        assert len(references) >= checker.MIN_USER_REFERENCE_FIELDS
        assert len(references) - checker.MIN_USER_REFERENCE_FIELDS <= 6, (
            f"measured {len(references)} user-reference fields; raise MIN_USER_REFERENCE_FIELDS "
            f"(now {checker.MIN_USER_REFERENCE_FIELDS}) to within a few of it"
        )
        # The two hand tables name only models that exist: a stale entry is
        # validated nowhere else (the check reads an entry only when its model is found).
        # ``MODEL_COLLECTIONS_BY_HAND`` is shared with the #1708 tenant-scope guard
        # since it moved to ``arango_repository_bindings.py``, so it also places
        # models that carry no user reference — "exists" is the question for it,
        # not "carries a reference".
        models = {model for _path, _line, model, _field in references}
        defined = {name for _module, name in load_repo_script("arango_repository_bindings").model_fields(app_root)}
        assert set(checker.MODEL_COLLECTIONS_BY_HAND) <= defined
        assert set(checker.NOT_PERSISTED_MODELS) <= models


class TestR6PartialStepIsNotFullCoverage:
    """#1700 review — a ``where``-filtered document step removes only some rows.

    ``attachments`` is deleted only for ``category == "pest_reference"``; the rest
    of the rows keep ``created_by`` unless a rule or an exclusion covers them.
    """

    def _tree_with_partial_c2(self, tmp_path: Path, extra_rule: str = "") -> Path:
        steps = GOOD_STEPS.replace(
            'ErasureStep(collection="c2", kind="document", executor="account_erasure", user_field="user_key"),',
            'ErasureStep(collection="c2", kind="document", executor="account_erasure", user_field="user_key", '
            'where={"category": "pest_reference"}),',
        )
        assert steps != GOOD_STEPS
        app = _tree(tmp_path, steps=steps)
        if extra_rule:
            engine = app / "domain" / "engines" / "erasure_engine.py"
            engine.write_text(
                engine.read_text(encoding="utf-8").replace(
                    'AnonymizationRule(collection="harvest_batches", user_field="harvester"),',
                    'AnonymizationRule(collection="harvest_batches", user_field="harvester"),\n        ' + extra_rule,
                ),
                encoding="utf-8",
            )
        return app

    def test_a_partial_step_alone_is_named(self, tmp_path: Path) -> None:
        violations = checker.check(self._tree_with_partial_c2(tmp_path))
        assert any(v.startswith("R6") and "'c2.user_key'" in v and "where" in v for v in violations), violations

    def test_a_rule_covering_the_rest_satisfies_it(self, tmp_path: Path) -> None:
        rule = 'AnonymizationRule(collection="c2", user_field="user_key"),'
        assert checker.check(self._tree_with_partial_c2(tmp_path, extra_rule=rule)) == []

    def test_an_empty_where_is_full_coverage(self, tmp_path: Path) -> None:
        steps = GOOD_STEPS.replace('user_field="user_key"),', 'user_field="user_key", where={}),', 1)
        assert checker.check(_tree(tmp_path, steps=steps)) == []


class TestR6InheritedFields:
    """#1700 review — a field declared on a base class is stored by every subclass."""

    def _tree(self, tmp_path: Path, models: str, not_persisted: dict[str, str] | None = None) -> list[str]:
        repositories = (
            REPOSITORIES
            + "\nclass ChildRepository(BaseArangoRepository[Child]):\n"
            + "    def __init__(self, db):\n        super().__init__(db, col.LOOSE)\n"
        )
        app = _tree(tmp_path, owned_models=OWNED_MODELS + models, repositories=repositories)
        return checker.check(app)

    def test_an_inherited_field_is_checked_on_the_subclass_collection(self, tmp_path: Path) -> None:
        models = "\nclass Stamped(BaseModel):\n    created_by: str\n\nclass Child(Stamped):\n    name: str\n"
        violations = self._tree(tmp_path, models)
        assert any(v.startswith("R6") and "'loose.created_by' (Child)" in v for v in violations), violations

    def test_a_base_across_modules_is_resolved(self, tmp_path: Path) -> None:
        repositories = (
            REPOSITORIES
            + "\nclass ChildRepository(BaseArangoRepository[Child]):\n"
            + "    def __init__(self, db):\n        super().__init__(db, col.LOOSE)\n"
        )
        app = _tree(
            tmp_path,
            owned_models=OWNED_MODELS + "\nclass Child(base.Stamped):\n    name: str\n",
            repositories=repositories,
        )
        (app / "domain" / "models" / "base.py").write_text(
            "class Stamped(BaseModel):\n    owner_user_key: str\n", encoding="utf-8"
        )
        violations = checker.check(app)
        assert any(v.startswith("R6") and "'loose.owner_user_key' (Child)" in v for v in violations), violations

    def test_a_not_persisted_base_does_not_hide_its_persisted_subclass(self, tmp_path: Path, monkeypatch) -> None:
        monkeypatch.setitem(checker.NOT_PERSISTED_MODELS, "Stamped", "a mixin, never stored itself")
        models = "\nclass Stamped(BaseModel):\n    created_by: str\n\nclass Child(Stamped):\n    name: str\n"
        violations = self._tree(tmp_path, models)
        assert any(v.startswith("R6") and "'loose.created_by' (Child)" in v for v in violations), violations


class TestTheFloorsSitBelowTodaysInventory:
    def test_a_collapsed_reader_is_reported(self, tmp_path: Path) -> None:
        violations = checker.check(_tree(tmp_path, steps="", sources=""))
        assert any(v.startswith("FLOOR") for v in violations)

    def test_an_inventory_without_filtered_steps_is_reported(self, tmp_path: Path) -> None:
        """R5 over zero edge/document steps is vacuous, so the reader must have found some."""
        steps = (
            "\n".join(
                f'        ErasureStep(collection="p{i}", kind="phase", executor="account_erasure"),' for i in range(10)
            )
            + '\n        ErasureStep(collection="users", kind="user", executor="account_cascade"),'
        )
        violations = checker.check(_tree(tmp_path, steps=steps))
        assert any(v.startswith("FLOOR") and "filtered" in v for v in violations)

    def test_the_floors_are_below_the_real_inventory(self) -> None:
        """Deliberately below today's 29 / 6 / 15, so a legitimate shrink passes."""
        from app.domain.engines.data_export_engine import DataExportEngine
        from app.domain.engines.erasure_engine import ErasureEngine

        assert len(ErasureEngine.DELETE_STEPS) > checker.MIN_STEPS
        filtered = [s for s in ErasureEngine.DELETE_STEPS if s.kind in ("edge", "document")]
        assert len(filtered) > checker.MIN_FILTERED_STEPS
        assert len({s.executor for s in ErasureEngine.DELETE_STEPS}) > checker.MIN_EXECUTORS
        assert len(DataExportEngine.USER_DATA_MANIFEST) > checker.MIN_MANIFEST_SOURCES
