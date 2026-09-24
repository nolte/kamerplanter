"""REQ-025 Art. 17 — the one executor of the declared ArangoDB erasure plan (#1664).

Until #1664 the declared plan had a single partial reader: the account cascade in
``ArangoUserRepository.delete`` walked the ``account_cascade`` slice, the
membership repository hand-wrote its own ``delete_all_for_user`` AQL, and
nothing at all applied ``ANONYMIZE_COLLECTIONS`` or the audit pseudonymisation.
Every rule was declared, guarded and never executed (the class #1622 and #1645
catalogue). This module is the single place a plan becomes ArangoDB writes; both
account-deletion paths reach it through :meth:`PrivacyService.erase_account`, and
since the #1700 review so does the unverified-account cleanup.
:meth:`ArangoUserRepository.delete` still runs the ``account_cascade`` slice, but
no production path calls it any more.

Nothing here names a personal-data collection. Every collection, filter field
and rule comes off the plan; ``scripts/check_privacy_inventory.py`` refuses a
second written-down list (R4).
"""

from __future__ import annotations

from collections.abc import Collection, Iterable
from typing import Any

import structlog
from arango.database import StandardDatabase, TransactionDatabase

from app.domain.engines.erasure_engine import ANONYMIZED_KEY_PREFIX, ErasureEngine
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
  FILTER doc[@field] == @value AND MATCHES(doc, @where)
  REMOVE doc IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

# A ``via`` step matches the rows that point at the subject's parent rows. The
# parent rows are resolved first (:meth:`_parent_rows`, recursively when the
# parent is itself reached ``via`` another collection) and bound as a list.
_REMOVE_BY_REFERENCE = """
FOR doc IN @@collection
  FILTER doc[@field] IN @values AND MATCHES(doc, @where)
  REMOVE doc IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

_SELECT_ROWS = """
FOR doc IN @@collection
  FILTER doc[@field] == @value AND MATCHES(doc, @where)
  RETURN {id: doc._id, key: doc._key}
"""

_SELECT_ROWS_BY_REFERENCE = """
FOR doc IN @@collection
  FILTER doc[@field] IN @values AND MATCHES(doc, @where)
  RETURN {id: doc._id, key: doc._key}
"""

_REMOVE_USER = """
FOR doc IN @@collection
  FILTER doc._key == @value
  REMOVE doc IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

# ``renamed`` is ``ErasureEngine.anonymized_rename_value(@tombstone, doc._key)``
# spelled in AQL (SHA256 returns lower-case hex, as ``hexdigest`` does).
_REWRITE_REFERENCE = """
FOR doc IN @@collection
  FILTER doc[@field] == @value
  LET renamed = LENGTH(@rename_fields) > 0 AND MATCHES(doc, @rename_when)
    ? ZIP(
        @rename_fields,
        (FOR name IN @rename_fields
          RETURN CONCAT(@rename_prefix, SUBSTRING(SHA256(CONCAT(@tombstone, ":", doc._key)), 0, 16)))
      )
    : {}
  UPDATE doc WITH MERGE(@patch, renamed) IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""


def _via_chain(plan: ErasurePlan, step: ErasureStep) -> list[str]:
    """The collections *step* is reached through, nearest first (validated acyclic before use)."""
    documents = {s.collection: s for s in plan.steps if s.kind == "document"}
    chain: list[str] = []
    via = step.via
    while via is not None and via not in chain and via in documents:
        chain.append(via)
        via = documents[via].via
    return chain


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
        if not plan.user_key or not plan.user_key.strip():
            # #1664 — ``doc[@field] == ""`` matches every unattributed row
            # (``pest_detections.user_key`` defaults to ``""``): other users' data.
            msg = "the plan names no user key; an empty key would match every unattributed row"
            raise ErasurePlanError(msg)
        documents = {step.collection: step for step in plan.steps if step.kind == "document"}
        for step in steps:
            if step.kind == "phase":
                if step.executor in _DELEGATED_PHASE_EXECUTORS:
                    continue
                if step.collection not in (ErasureEngine.ANONYMIZE_PHASE, ErasureEngine.PSEUDONYMIZE_AUDIT_PHASE):
                    msg = f"erasure phase '{step.collection}' has no ArangoDB implementation"
                    raise ErasurePlanError(msg)
            if step.via is not None:
                seen = {step.collection}
                via: str | None = step.via
                while via is not None:
                    if via not in documents:
                        msg = (
                            f"{step.kind} step '{step.collection}' is reached via '{via}', "
                            "which the plan does not declare as a document step"
                        )
                        raise ErasurePlanError(msg)
                    if via in seen:
                        msg = f"{step.kind} step '{step.collection}' is reached through a via cycle at '{via}'"
                        raise ErasurePlanError(msg)
                    seen.add(via)
                    via = documents[via].via
        needs_hash = any(
            step.collection == ErasureEngine.PSEUDONYMIZE_AUDIT_PHASE and plan.pseudonymize_audit for step in steps
        ) or any(
            step.collection == ErasureEngine.ANONYMIZE_PHASE
            and any(rule.replacement_strategy == "tombstone_hash" or rule.rename_fields for rule in plan.anonymize)
            for step in steps
        )
        if needs_hash and not tombstone:
            msg = "the plan pseudonymises user keys but no tombstone hash was supplied"
            raise ErasurePlanError(msg)
        if tombstone is not None and not ErasureEngine.is_tombstone(tombstone):
            # A rename is keyed on the tombstone precisely because it is not
            # guessable (#1700); anything else would reopen slug squatting.
            msg = "the supplied tombstone is not a tombstone hash"
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
                for parent in _via_chain(plan, step):
                    add(parent)
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
        elif step.collection not in present or any(parent not in present for parent in _via_chain(plan, step)):
            # A collection the database lacks holds no rows (see ``absent_collections``).
            affected = 0
        elif step.kind == "user":
            affected = self._counted(
                transaction.aql.execute(
                    _REMOVE_USER, bind_vars={"@collection": step.collection, "value": plan.user_key}
                )
            )
        elif step.via is not None:
            # An edge points at its parent by ``_id``; a document carries the
            # parent's ``_key`` (``location_assignments.membership_key``).
            parents = self._parent_rows(transaction, plan, step.via)
            values = [row["id"] if step.kind == "edge" else row["key"] for row in parents]
            affected = 0
            if values:
                affected = self._counted(
                    transaction.aql.execute(
                        _REMOVE_BY_REFERENCE,
                        bind_vars={
                            "@collection": step.collection,
                            "field": step.user_field,
                            "values": values,
                            "where": step.where,
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
                    bind_vars={
                        "@collection": step.collection,
                        "field": step.user_field,
                        "value": value,
                        "where": step.where,
                    },
                )
            )
        report.steps.append(
            ErasureStepOutcome(collection=step.collection, kind=step.kind, executor=step.executor, affected=affected)
        )

    def _parent_rows(
        self, transaction: TransactionDatabase, plan: ErasurePlan, collection: str
    ) -> list[dict[str, str]]:
        """``{id, key}`` of the subject's rows in *collection*, as its document step matches them.

        Resolved through the parent's own step, recursively: the assignment edges
        run ``location_assignments -> …``, whose rows are the subject's through
        ``memberships``. ``_refuse_unexecutable`` has already checked every
        ``via`` names a declared document step and that the chain ends.
        """
        parent = next(s for s in plan.steps if s.kind == "document" and s.collection == collection)
        if parent.via is None:
            cursor = transaction.aql.execute(
                _SELECT_ROWS,
                bind_vars={
                    "@collection": parent.collection,
                    "field": parent.user_field,
                    "value": plan.user_key,
                    "where": parent.where,
                },
            )
            return [dict(row) for row in cursor]
        keys = [row["key"] for row in self._parent_rows(transaction, plan, parent.via)]
        if not keys:
            return []
        cursor = transaction.aql.execute(
            _SELECT_ROWS_BY_REFERENCE,
            bind_vars={
                "@collection": parent.collection,
                "field": parent.user_field,
                "values": keys,
                "where": parent.where,
            },
        )
        return [dict(row) for row in cursor]

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
                        "rename_fields": list(rule.rename_fields),
                        "rename_when": rule.rename_when,
                        "rename_prefix": ANONYMIZED_KEY_PREFIX,
                        "tombstone": tombstone or "",
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
                        "rename_fields": [],
                        "rename_when": {},
                        "rename_prefix": ANONYMIZED_KEY_PREFIX,
                        "tombstone": tombstone or "",
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
