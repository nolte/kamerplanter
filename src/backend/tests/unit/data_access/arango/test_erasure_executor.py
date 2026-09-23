"""#1664 — ``ArangoErasureExecutor`` runs the declared plan, in order, as declared.

The reach against a real server is measured in
``tests/integration/test_account_erasure_reach.py``. This tier pins what a server
cannot show cheaply: the *order* of the writes, the exact patch each rule
strategy writes, the bound (never interpolated) values, and that an
unexecutable plan is refused before the first write.

Expected values are derived from the engine's declared plan, so a new step is
covered without editing this file — but the ordering assertions compare
*positions*, which a reordered inventory changes.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango.erasure_executor import ArangoErasureExecutor, ErasurePlanError
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.models.privacy import ErasurePlan, ErasureStep

USER_KEY = "u-42"
TOMBSTONE = ErasureEngine.compute_tombstone_hash(USER_KEY, "s" * 32)


class _FakeAql:
    def __init__(self, calls: list[tuple[str, dict[str, Any]]], fail_on: str | None) -> None:
        self._calls = calls
        self._fail_on = fail_on

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None):
        bind_vars = bind_vars or {}
        if self._fail_on is not None and bind_vars.get("@collection") == self._fail_on:
            raise RuntimeError(f"write to {self._fail_on} failed")
        self._calls.append((query, bind_vars))
        return iter([1])


class _FakeTransaction:
    def __init__(self, calls: list[tuple[str, dict[str, Any]]], fail_on: str | None) -> None:
        self.aql = _FakeAql(calls, fail_on)
        self.committed = False
        self.aborted = False

    def commit_transaction(self) -> None:
        self.committed = True

    def abort_transaction(self) -> None:
        self.aborted = True


class _FakeDb:
    def __init__(self, *, missing: frozenset[str] = frozenset(), fail_on: str | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.missing = missing
        self.fail_on = fail_on
        self.transactions: list[_FakeTransaction] = []
        self.declared_write: list[str] = []

    def has_collection(self, name: str) -> bool:
        return name not in self.missing

    def begin_transaction(self, write: list[str], allow_implicit: bool) -> _FakeTransaction:
        assert allow_implicit is False, "every collection the run touches must be declared"
        self.declared_write = list(write)
        transaction = _FakeTransaction(self.calls, self.fail_on)
        self.transactions.append(transaction)
        return transaction


def _plan() -> ErasurePlan:
    return ErasureEngine().build_erasure_plan(USER_KEY)


def _run(db: _FakeDb, plan: ErasurePlan | None = None, **kwargs: Any):
    kwargs.setdefault("tombstone", TOMBSTONE)
    return ArangoErasureExecutor(db).run_erasure_plan(plan or _plan(), **kwargs)  # type: ignore[arg-type]


def _written(db: _FakeDb) -> list[str]:
    return [binds["@collection"] for _, binds in db.calls]


def _expected_write_order(plan: ErasurePlan) -> list[str]:
    order: list[str] = []
    for step in plan.steps:
        if step.kind in ("edge", "document", "user"):
            order.append(step.collection)
        elif step.collection == ErasureEngine.ANONYMIZE_PHASE:
            order.extend(rule.collection for rule in plan.anonymize)
        elif step.collection == ErasureEngine.PSEUDONYMIZE_AUDIT_PHASE:
            order.extend(rule.collection for rule in plan.pseudonymize_audit)
    return order


class TestOrder:
    def test_writes_follow_the_declared_plan_order(self):
        db = _FakeDb()
        _run(db)
        assert _written(db) == _expected_write_order(_plan())

    def test_the_audit_hash_runs_after_every_key_filter_and_before_the_user(self):
        """The pseudonymisation rewrites the key; anything filtering on it after would find nothing."""
        db = _FakeDb()
        plan = _plan()
        _run(db, plan)
        written = _written(db)
        audit = {rule.collection for rule in plan.pseudonymize_audit}
        users = next(s.collection for s in plan.steps if s.kind == "user")
        audit_positions = [i for i, (_, b) in enumerate(db.calls) if b["@collection"] in audit and "patch" in b]
        other_positions = [i for i in range(len(written)) if i not in audit_positions and written[i] != users]
        assert audit_positions, "no audit pseudonymisation was written"
        assert max(other_positions) < min(audit_positions)
        assert written.index(users) == len(written) - 1

    def test_everything_runs_in_one_committed_transaction_over_every_touched_collection(self):
        db = _FakeDb()
        _run(db)
        assert len(db.transactions) == 1
        assert db.transactions[0].committed is True
        assert set(_written(db)) <= set(db.declared_write)
        vias = {s.via for s in _plan().steps if s.via}
        assert vias <= set(db.declared_write)


class TestStrategies:
    def test_tombstone_rules_write_the_hash_and_empty_their_display_fields(self):
        db = _FakeDb()
        plan = _plan()
        _run(db, plan)
        patches = {(b["@collection"], b["field"]): b["patch"] for _, b in db.calls if "patch" in b}
        for rule in plan.anonymize:
            expected_value = TOMBSTONE if rule.replacement_strategy == "tombstone_hash" else rule.anonymized_value
            expected = {rule.user_field: expected_value, **dict.fromkeys(rule.clear_fields, "")}
            assert patches[(rule.collection, rule.user_field)] == expected

    def test_at_least_one_rule_of_each_strategy_is_declared(self):
        """Otherwise the test above would be vacuous for the missing strategy."""
        strategies = {rule.replacement_strategy for rule in _plan().anonymize}
        assert strategies == {"marker", "tombstone_hash"}

    def test_audit_rules_write_only_the_hash(self):
        db = _FakeDb()
        plan = _plan()
        _run(db, plan)
        for rule in plan.pseudonymize_audit:
            patches = [b["patch"] for _, b in db.calls if b["@collection"] == rule.collection and "patch" in b]
            assert patches == [{rule.user_field: TOMBSTONE}]

    def test_an_edge_from_the_user_filters_on_the_user_vertex_id(self):
        db = _FakeDb()
        plan = _plan()
        _run(db, plan)
        users = next(s.collection for s in plan.steps if s.kind == "user")
        for step in plan.steps:
            if step.kind != "edge" or step.via:
                continue
            (binds,) = [b for _, b in db.calls if b["@collection"] == step.collection]
            assert binds["field"] == step.user_field
            assert binds["value"] == f"{users}/{USER_KEY}"

    def test_a_via_edge_filters_through_its_parent_documents_user_field(self):
        db = _FakeDb()
        plan = _plan()
        _run(db, plan)
        via_steps = [s for s in plan.steps if s.kind == "edge" and s.via]
        assert via_steps, "the inventory declares via edges; this test must not be vacuous"
        for step in via_steps:
            parent = next(s for s in plan.steps if s.kind == "document" and s.collection == step.via)
            (binds,) = [b for _, b in db.calls if b["@collection"] == step.collection]
            assert binds["@parent"] == step.via
            assert binds["parent_field"] == parent.user_field
            assert binds["endpoint"] == step.user_field
            assert binds["value"] == USER_KEY

    def test_a_document_step_filters_on_its_declared_user_field(self):
        db = _FakeDb()
        plan = _plan()
        _run(db, plan)
        for step in plan.steps:
            if step.kind != "document":
                continue
            (binds,) = [b for _, b in db.calls if b["@collection"] == step.collection]
            assert binds["field"] == step.user_field
            assert binds["value"] == USER_KEY

    def test_the_user_key_is_bound_never_interpolated(self):
        db = _FakeDb()
        _run(db)
        assert db.calls
        for query, _ in db.calls:
            assert USER_KEY not in query
            assert TOMBSTONE not in query


class TestRefusals:
    def test_a_hashing_plan_without_a_tombstone_is_refused_before_any_write(self):
        db = _FakeDb()
        with pytest.raises(ErasurePlanError, match="tombstone"):
            _run(db, tombstone=None)
        assert db.transactions == []

    def test_an_unknown_phase_is_refused_before_any_write(self):
        plan = _plan()
        plan.steps.insert(0, ErasureStep(collection="_mystery_phase", kind="phase", executor="retention_worker"))
        db = _FakeDb()
        with pytest.raises(ErasurePlanError, match="_mystery_phase"):
            _run(db, plan)
        assert db.transactions == []

    def test_a_failed_write_aborts_and_never_commits(self):
        plan = _plan()
        db = _FakeDb(fail_on=plan.anonymize[0].collection)
        with pytest.raises(RuntimeError):
            _run(db, plan)
        assert db.transactions[0].aborted is True
        assert db.transactions[0].committed is False


class TestSlices:
    def test_the_account_cascade_slice_touches_only_its_steps_and_needs_no_hash(self):
        db = _FakeDb()
        report = _run(db, tombstone=None, executors=("account_cascade",))
        expected = [s.collection for s in ErasureEngine.steps_for("account_cascade")]
        assert _written(db) == expected
        assert report.rules == []
        assert [s.collection for s in report.steps] == expected

    def test_non_arango_phases_are_reported_as_delegated(self):
        db = _FakeDb()
        report = _run(db)
        delegated = [
            s.collection for s in _plan().steps if s.executor in ("storage_cleanup", "reference_index_cleanup")
        ]
        assert report.delegated == delegated

    def test_a_missing_collection_is_skipped_and_named(self):
        plan = _plan()
        missing = next(s.collection for s in plan.steps if s.kind == "document")
        db = _FakeDb(missing=frozenset({missing}))
        report = _run(db, plan)
        assert missing not in _written(db)
        assert missing not in db.declared_write
        assert report.absent_collections == [missing]
        assert report.affected(missing) == 0
