"""REQ-025 Art. 17 — the one executor of the declared ArangoDB erasure plan (#1664).

Until #1664 the declared plan had a single partial reader: the account cascade in
``ArangoUserRepository.delete`` walked the ``account_cascade`` slice, the
membership repository hand-wrote its own ``delete_all_for_user`` AQL, and
nothing at all applied ``ANONYMIZE_COLLECTIONS`` or the audit pseudonymisation.
Every rule was declared, guarded and never executed (the class #1622 and #1645
catalogue). This module is the single place a plan becomes ArangoDB writes; both
account-deletion paths reach it through :meth:`PrivacyService.erase_account`, and
the unverified-account cleanup reaches its ``account_cascade`` slice through
:meth:`ArangoUserRepository.delete`.

Nothing here names a personal-data collection. Every collection, filter field
and rule comes off the plan; ``scripts/check_privacy_inventory.py`` refuses a
second written-down list (R4).
"""

from __future__ import annotations

from collections.abc import Collection, Iterable
from typing import Any

import structlog
from arango.database import StandardDatabase, TransactionDatabase

from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.interfaces.erasure_executor import IErasureExecutor
from app.domain.models.privacy import (
    AnonymizationRule,
    ErasureExecutionReport,
    ErasureExecutor,
    ErasurePlan,
    ErasureRuleOutcome,
    ErasureStep,
    ErasureStepOutcome,
    PseudonymizationRule,
)

logger = structlog.get_logger()

#: Phases that are not ArangoDB writes. Their executors run before this one
#: (object storage, pgvector); a plan step carrying one is recorded as
#: delegated, never silently dropped.
_DELEGATED_PHASE_EXECUTORS: frozenset[str] = frozenset({"storage_cleanup", "reference_index_cleanup"})

# The AQL below binds the collection (``@@collection``), the attribute name
# (``doc[@field]``) and the value. Nothing a caller controls is interpolated.
_REMOVE_DOCUMENTS = """
FOR doc IN @@collection
  FILTER doc[@field] == @value
  REMOVE doc IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

_REMOVE_EDGES_VIA_PARENT = """
FOR parent IN @@parent
  FILTER parent[@parent_field] == @value
  FOR edge IN @@collection
    FILTER edge[@endpoint] == parent._id
    REMOVE edge IN @@collection
    COLLECT WITH COUNT INTO affected
    RETURN affected
"""

_REMOVE_USER = """
FOR doc IN @@collection
  FILTER doc._key == @value
  REMOVE doc IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

_REWRITE_REFERENCE = """
FOR doc IN @@collection
  FILTER doc[@field] == @value
  UPDATE doc WITH @patch IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""


class ErasurePlanError(ValueError):
    """The plan cannot be executed as declared — raised before any write."""


class ArangoErasureExecutor(IErasureExecutor):
    """Applies the ArangoDB steps of an :class:`ErasurePlan` in one stream transaction.

    **Atomicity.** Every write of a run happens inside one ArangoDB stream
    transaction that declares all collections the run touches. A failure at
    step 17 of 30 aborts the transaction, so the account is either fully erased
    in ArangoDB or not touched at all — never half-erased with the user
    document gone and its anonymisation rules unapplied. The pre-ArangoDB
    phases (object storage, pgvector) cannot join the transaction; they run
    before it and are idempotent on their own.

    **Re-runnability.** Every step filters on the subject's key, and every
    rewrite replaces exactly that key, so a second run finds only what the first
    did not reach: removed rows are gone, anonymised rows no longer match,
    pseudonymised audit rows carry the hash instead of the key. A re-run after a
    crash (the transaction aborted, or the process died before the commit and
    the server discarded it) therefore repeats the whole plan and skips
    nothing. This does not depend on the transaction: a store that committed
    half a run would still converge on the second one.

    **Order.** The plan's declared order is the execution order. The
    pseudonymisation phase must run after every step that filters on the key
    (it changes the key of the audit rows) and the user document last; the
    engine declares it so and ``test_privacy_engines.py`` pins it.
    """

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def run_erasure_plan(
        self,
        plan: ErasurePlan,
        *,
        tombstone: str | None,
        executors: Collection[ErasureExecutor] | None = None,
    ) -> ErasureExecutionReport:
        steps = [step for step in plan.steps if executors is None or step.executor in executors]
        report = ErasureExecutionReport()
        self._refuse_unexecutable(plan, steps, tombstone)

        touched = self._collections_touched(plan, steps)
        present = [name for name in touched if self._db.has_collection(name)]
        report.absent_collections = [name for name in touched if name not in present]
        if not present:
            return report

        transaction = self._db.begin_transaction(write=present, allow_implicit=False)
        try:
            for step in steps:
                self._run_step(transaction, plan, step, tombstone, set(present), report)
            transaction.commit_transaction()
        except BaseException:
            self._abort_quietly(transaction)
            raise

        logger.info(
            "erasure.arango_executed",
            steps={step.collection: step.affected for step in report.steps},
            rules=[f"{rule.collection}.{rule.user_field}={rule.affected}" for rule in report.rules],
            delegated=report.delegated,
            absent_collections=report.absent_collections,
        )
        return report

    # ── validation (before any write) ──────────────────────────────────

    @staticmethod
    def _refuse_unexecutable(plan: ErasurePlan, steps: list[ErasureStep], tombstone: str | None) -> None:
        """Reject a plan this executor would have to guess at, before it writes anything."""
        documents = {step.collection: step for step in plan.steps if step.kind == "document"}
        for step in steps:
            if step.kind == "phase":
                if step.executor in _DELEGATED_PHASE_EXECUTORS:
                    continue
                if step.collection not in (ErasureEngine.ANONYMIZE_PHASE, ErasureEngine.PSEUDONYMIZE_AUDIT_PHASE):
                    msg = f"erasure phase '{step.collection}' has no ArangoDB implementation"
                    raise ErasurePlanError(msg)
            if step.via is not None and step.via not in documents:
                msg = f"edge step '{step.collection}' is reached via '{step.via}', which the plan does not declare"
                raise ErasurePlanError(msg)
        needs_hash = any(
            step.collection == ErasureEngine.PSEUDONYMIZE_AUDIT_PHASE and plan.pseudonymize_audit for step in steps
        ) or any(
            step.collection == ErasureEngine.ANONYMIZE_PHASE
            and any(rule.replacement_strategy == "tombstone_hash" for rule in plan.anonymize)
            for step in steps
        )
        if needs_hash and not tombstone:
            msg = "the plan pseudonymises user keys but no tombstone hash was supplied"
            raise ErasurePlanError(msg)

    @staticmethod
    def _collections_touched(plan: ErasurePlan, steps: Iterable[ErasureStep]) -> list[str]:
        """Every collection the run writes to or reads through, each once, in plan order."""
        names: list[str] = []

        def add(name: str) -> None:
            if name not in names:
                names.append(name)

        for step in steps:
            if step.kind in ("edge", "document", "user"):
                add(step.collection)
                if step.via is not None:
                    add(step.via)
            elif step.collection == ErasureEngine.ANONYMIZE_PHASE:
                for rule in plan.anonymize:
                    add(rule.collection)
            elif step.collection == ErasureEngine.PSEUDONYMIZE_AUDIT_PHASE:
                for audit_rule in plan.pseudonymize_audit:
                    add(audit_rule.collection)
        return names

    # ── steps ──────────────────────────────────────────────────────────

    def _run_step(
        self,
        transaction: TransactionDatabase,
        plan: ErasurePlan,
        step: ErasureStep,
        tombstone: str | None,
        present: set[str],
        report: ErasureExecutionReport,
    ) -> None:
        if step.kind == "phase":
            if step.executor in _DELEGATED_PHASE_EXECUTORS:
                report.delegated.append(step.collection)
                return
            if step.collection == ErasureEngine.ANONYMIZE_PHASE:
                outcomes = [
                    self._anonymize(transaction, rule, plan.user_key, tombstone, present) for rule in plan.anonymize
                ]
            else:
                outcomes = [
                    self._pseudonymize(transaction, audit_rule, plan.user_key, tombstone, present)
                    for audit_rule in plan.pseudonymize_audit
                ]
            report.rules.extend(outcomes)
            affected = sum(outcome.affected for outcome in outcomes)
        elif step.collection not in present or (step.via is not None and step.via not in present):
            # A collection the database lacks holds no rows (see ``absent_collections``).
            affected = 0
        elif step.kind == "user":
            affected = self._counted(
                transaction.aql.execute(
                    _REMOVE_USER, bind_vars={"@collection": step.collection, "value": plan.user_key}
                )
            )
        elif step.kind == "edge" and step.via is not None:
            parent = next(s for s in plan.steps if s.kind == "document" and s.collection == step.via)
            affected = self._counted(
                transaction.aql.execute(
                    _REMOVE_EDGES_VIA_PARENT,
                    bind_vars={
                        "@collection": step.collection,
                        "@parent": step.via,
                        "parent_field": parent.user_field,
                        "endpoint": step.user_field,
                        "value": plan.user_key,
                    },
                )
            )
        else:
            # ``edge`` without ``via`` runs ``users -> <document>``: its endpoint is
            # the user vertex id, built from the plan's own ``user`` step.
            value = self._user_vertex_id(plan) if step.kind == "edge" else plan.user_key
            affected = self._counted(
                transaction.aql.execute(
                    _REMOVE_DOCUMENTS,
                    bind_vars={"@collection": step.collection, "field": step.user_field, "value": value},
                )
            )
        report.steps.append(
            ErasureStepOutcome(collection=step.collection, kind=step.kind, executor=step.executor, affected=affected)
        )

    def _anonymize(
        self,
        transaction: TransactionDatabase,
        rule: AnonymizationRule,
        user_key: str,
        tombstone: str | None,
        present: set[str],
    ) -> ErasureRuleOutcome:
        """Replace the rule's user reference and empty its free-text companions; keep the row."""
        replacement = tombstone if rule.replacement_strategy == "tombstone_hash" else rule.anonymized_value
        patch: dict[str, Any] = {rule.user_field: replacement}
        patch.update(dict.fromkeys(rule.clear_fields, ""))
        affected = 0
        if rule.collection in present:
            affected = self._counted(
                transaction.aql.execute(
                    _REWRITE_REFERENCE,
                    bind_vars={
                        "@collection": rule.collection,
                        "field": rule.user_field,
                        "value": user_key,
                        "patch": patch,
                    },
                )
            )
        return ErasureRuleOutcome(
            phase=ErasureEngine.ANONYMIZE_PHASE,
            collection=rule.collection,
            user_field=rule.user_field,
            affected=affected,
        )

    def _pseudonymize(
        self,
        transaction: TransactionDatabase,
        rule: PseudonymizationRule,
        user_key: str,
        tombstone: str | None,
        present: set[str],
    ) -> ErasureRuleOutcome:
        """Replace the key on a retained audit row with the tombstone hash."""
        affected = 0
        if rule.collection in present:
            affected = self._counted(
                transaction.aql.execute(
                    _REWRITE_REFERENCE,
                    bind_vars={
                        "@collection": rule.collection,
                        "field": rule.user_field,
                        "value": user_key,
                        "patch": {rule.user_field: tombstone},
                    },
                )
            )
        return ErasureRuleOutcome(
            phase=ErasureEngine.PSEUDONYMIZE_AUDIT_PHASE,
            collection=rule.collection,
            user_field=rule.user_field,
            affected=affected,
        )

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _user_vertex_id(plan: ErasurePlan) -> str:
        user_step = next((step for step in plan.steps if step.kind == "user"), None)
        if user_step is None:
            msg = "the plan declares edges from the user vertex but no user step to name its collection"
            raise ErasurePlanError(msg)
        return f"{user_step.collection}/{plan.user_key}"

    @staticmethod
    def _counted(cursor: Any) -> int:
        """The single ``COLLECT WITH COUNT`` row every executor write returns."""
        return int(next(iter(cursor), 0))

    @staticmethod
    def _abort_quietly(transaction: TransactionDatabase) -> None:
        """Roll back without masking the failure that got us here."""
        try:
            transaction.abort_transaction()
        except Exception as exc:  # noqa: BLE001 — the primary error is the one to raise
            logger.warning("erasure.transaction_abort_failed", error=str(exc))
