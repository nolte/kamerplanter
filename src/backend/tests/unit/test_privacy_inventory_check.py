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
that spells its collections out (R4).

**The vacuum direction.** :class:`TestACommentCannotSatisfyIt` writes a module
whose only mention of ``build_export_manifest`` is a comment that even spells the
call, and pins that R3 still fires. That is the trap repaired in #1545, #1610 and
#1624 and generalised in #1456: prose answering for code.

Traces to issue #1622 (no TC-ID: a source-tree gate is not a user-facing case).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

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

#: Ten well-formed steps, comfortably above the anti-vacuity floors.
GOOD_STEPS = "\n".join(
    f'        ErasureStep(collection="c{i}", kind="document", '
    f'executor="{"account_cascade" if i % 2 else "retention_worker"}"),'
    for i in range(10)
)

#: Ten manifest sources that the erasure inventory above declares.
GOOD_SOURCES = "\n".join(f'        DataSourceDefinition(collection="c{i}", label="L{i}"),' for i in range(10))

READER = """
from app.domain.engines.erasure_engine import ErasureEngine


def cascade(repo, key):
    for step in ErasureEngine().build_erasure_plan(key).steps:
        repo._remove_docs_for_user(step.collection, key)


def export_run(engine, user_key):
    return engine.build_export_manifest(user_key)
"""


def _tree(
    tmp_path: Path,
    *,
    steps: str = GOOD_STEPS,
    sources: str = GOOD_SOURCES,
    reader: str = READER,
) -> Path:
    app = tmp_path / "app"
    engines = app / "domain" / "engines"
    engines.mkdir(parents=True)
    (engines / "erasure_engine.py").write_text(textwrap.dedent(ERASURE_HEAD).format(steps=steps), encoding="utf-8")
    (engines / "data_export_engine.py").write_text(
        textwrap.dedent(EXPORT_HEAD).format(sources=sources), encoding="utf-8"
    )
    (app / "executor.py").write_text(textwrap.dedent(reader), encoding="utf-8")
    return app


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


class TestTheFloorsSitBelowTodaysInventory:
    def test_a_collapsed_reader_is_reported(self, tmp_path: Path) -> None:
        violations = checker.check(_tree(tmp_path, steps="", sources=""))
        assert any(v.startswith("FLOOR") for v in violations)

    def test_the_floors_are_below_the_real_inventory(self) -> None:
        """Deliberately below today's 29 / 6 / 15, so a legitimate shrink passes."""
        from app.domain.engines.data_export_engine import DataExportEngine
        from app.domain.engines.erasure_engine import ErasureEngine

        assert len(ErasureEngine.DELETE_STEPS) > checker.MIN_STEPS
        assert len({s.executor for s in ErasureEngine.DELETE_STEPS}) > checker.MIN_EXECUTORS
        assert len(DataExportEngine.USER_DATA_MANIFEST) > checker.MIN_MANIFEST_SOURCES
