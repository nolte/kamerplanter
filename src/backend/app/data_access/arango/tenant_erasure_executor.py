"""REQ-024 / REQ-025 — the one executor of the declared tenant-erasure inventory (#1769).

Nothing here names a tenant-scoped collection. Every collection, parent chain and
pseudonymisation comes off the plan (:meth:`TenantErasureEngine.build_plan`);
the edge collections and the residue scan come off the database itself, so an
edge collection or a legacy collection nobody declared is still reached.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import Any

import structlog
from arango.database import StandardDatabase, TransactionDatabase

from app.domain.engines.erasure_engine import ANONYMIZED_MARKER, ErasureEngine
from app.domain.interfaces.tenant_erasure_executor import ITenantErasureExecutor
from app.domain.models.tenant_erasure import (
    TenantErasureEntry,
    TenantErasureOutcome,
    TenantErasurePlan,
    TenantErasurePseudonymization,
    TenantErasureReport,
)

logger = structlog.get_logger()

#: The same charset ``TenantService`` accepts for a storage prefix (SEC-004): an
#: empty or malformed key must never reach a filter.
_TENANT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._:@()=;$!*',+%-]+$")

#: The shape :meth:`ErasureEngine.compute_tombstone_hash` produces, for AQL.
_TOMBSTONE_REGEX = "^anon_[0-9a-f]{16}$"

_SELECT_IDS = "FOR doc IN @@collection FILTER {match} RETURN {{id: doc._id, key: doc._key}}"

_REMOVE_BY_KEYS = """
FOR doc IN @@collection
  FILTER doc._key IN @keys
  REMOVE doc IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

_REMOVE_EDGES = """
FOR edge IN @@collection
  FILTER edge._from IN @ids OR edge._to IN @ids
  REMOVE edge IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

_DISTINCT_VALUES = """
FOR doc IN @@collection
  FILTER doc._key IN @keys
  RETURN DISTINCT doc[@field]
"""

# ``{[@field]: …}`` is AQL's computed attribute name; ``@mapping`` holds only the
# account keys found on these rows, each mapped to its tombstone hash.
_PSEUDONYMIZE = """
FOR doc IN @@collection
  FILTER doc._key IN @keys
  LET current = doc[@field]
  LET replaced = IS_STRING(current) AND HAS(@mapping, current) ? @mapping[current] : current
  UPDATE doc WITH MERGE(@clear, {[@field]: replaced}) IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""

_COUNT_UNPSEUDONYMIZED = """
FOR doc IN @@collection
  FILTER {match}
  LET value = doc[@field]
  FILTER (IS_STRING(value) AND value != "" AND value != @marker AND NOT REGEX_TEST(value, @tombstone))
    OR LENGTH(FOR name IN @clear_fields FILTER doc[name] != null AND doc[name] != "" RETURN 1) > 0
  COLLECT WITH COUNT INTO remaining
  RETURN remaining
"""

_COUNT_MATCHING = "FOR doc IN @@collection FILTER {match} COLLECT WITH COUNT INTO remaining RETURN remaining"

_ANY_STAMPED = "FOR doc IN @@collection FILTER doc.tenant_key == @tenant_key LIMIT 1 RETURN 1"

_REMOVE_TENANT = """
FOR doc IN @@collection
  FILTER doc._key == @key
  REMOVE doc IN @@collection
  COLLECT WITH COUNT INTO affected
  RETURN affected
"""


class TenantErasurePlanError(ValueError):
    """The plan cannot be executed as declared — raised before any write."""


def _match(
    entry: TenantErasureEntry, parent_keys: dict[str, list[str]], tenant_collection: str
) -> tuple[str, dict[str, Any]]:
    """The FILTER that selects the tenant's rows of *entry*, and its bind variables.

    A row is the tenant's when it carries the tenant's key or points at a parent
    row of the tenant — minus the rows the entry keeps: a ``keep_when`` example
    (a system seed) and, with ``keep_if_granted_via``, a row another tenant was
    granted access to (#1769 code review). Field names, keys and predicates are
    bound; the only thing formatted into the string is the clause index.
    """
    clauses = ["doc[@tenant_field] == @tenant_key"]
    binds: dict[str, Any] = {"tenant_field": entry.tenant_field}
    for index, parent in enumerate(entry.parents):
        keys = parent_keys.get(parent.collection) or []
        if not keys:
            continue
        # A child stamped with ANOTHER tenant that points at this tenant's parent
        # is that tenant's row (a past cross-tenant reference), never ours to
        # delete (#1769 review SEC-004).
        clauses.append(
            f"(doc[@field{index}] IN @keys{index} AND MATCHES(doc, @where{index})"
            " AND (doc.tenant_key == null OR doc.tenant_key == '' OR doc.tenant_key == @tenant_key))"
        )
        binds[f"field{index}"] = parent.field
        binds[f"keys{index}"] = keys
        binds[f"where{index}"] = parent.where
    match = "(" + " OR ".join(clauses) + ")"
    for index, example in enumerate(entry.keep_when):
        match += f" AND NOT MATCHES(doc, @keep{index})"
        binds[f"keep{index}"] = example
    if entry.keep_if_granted_via is not None:
        # A grant from any tenant but this one: that tenant's rows point here.
        match += (
            " AND LENGTH(FOR grant IN @@grants FILTER grant._to == doc._id"
            " AND grant._from != CONCAT(@tenant_collection, '/', @tenant_key) LIMIT 1 RETURN 1) == 0"
        )
        binds["@grants"] = entry.keep_if_granted_via
        binds["tenant_collection"] = tenant_collection
    return match, binds


class ArangoTenantErasureExecutor(ITenantErasureExecutor):
    """Erases one tenant in one ArangoDB stream transaction, then counts the residue.

    **Atomicity.** Selection, edge sweep, removal, pseudonymisation and the tenant
    document all run in one transaction declaring every collection it writes; a
    failure aborts it, so the tenant is either fully erased in ArangoDB or not
    touched. The storage and derived-index phases cannot join it; they run before
    it in ``TenantService`` and are idempotent on their own.

    **Completion is measured, not assumed.** After the commit the executor counts,
    outside the transaction, what still holds the tenant: rows of every ``delete``
    entry, account keys left on ``pseudonymize`` rows, the tenant document, and — in
    every collection the plan does not classify — rows stamped with the tenant's
    key. A row written concurrently after the transaction's snapshot shows up
    here, as does a collection nobody declared.

    **Re-runnable.** Every selection filters on the tenant, so a second run finds
    only what the first did not reach.
    """

    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def run_tenant_erasure(
        self,
        plan: TenantErasurePlan,
        *,
        pseudonymize: Callable[[str], str],
    ) -> TenantErasureReport:
        self._refuse_unexecutable(plan)
        report = TenantErasureReport()

        existing = {c["name"]: c for c in self._db.collections() if not c["system"]}
        edge_collections = sorted(name for name, info in existing.items() if info["type"] == "edge")
        entries = [entry for entry in plan.entries if entry.collection in existing]
        report.absent_collections = [entry.collection for entry in plan.entries if entry.collection not in existing]

        writes = [entry.collection for entry in entries if entry.action != "retain"] + edge_collections
        reads = [entry.collection for entry in entries if entry.action == "retain"]
        if plan.tenant_collection in existing:
            writes.append(plan.tenant_collection)
        tenant_id = f"{plan.tenant_collection}/{plan.tenant_key}"

        parent_collections = {parent.collection for entry in plan.entries for parent in entry.parents}
        parent_keys: dict[str, list[str]] = {}
        transaction = self._db.begin_transaction(read=reads, write=writes, allow_implicit=False)
        try:
            rows: dict[str, list[dict[str, str]]] = {}
            for entry in entries:
                rows[entry.collection] = self._select(transaction, entry, plan, self._with_known(plan, parent_keys))
                parent_keys[entry.collection] = [row["key"] for row in rows[entry.collection]]

            deleted_ids = [row["id"] for entry in entries if entry.action == "delete" for row in rows[entry.collection]]
            deleted_ids.append(tenant_id)
            for edge_collection in edge_collections:
                report.edges_removed += self._counted(
                    transaction.aql.execute(
                        _REMOVE_EDGES, bind_vars={"@collection": edge_collection, "ids": deleted_ids}
                    )
                )

            for entry in entries:
                keys = parent_keys[entry.collection]
                affected = 0
                if keys and entry.action == "delete":
                    affected = self._counted(
                        transaction.aql.execute(
                            _REMOVE_BY_KEYS, bind_vars={"@collection": entry.collection, "keys": keys}
                        )
                    )
                elif keys and entry.action == "pseudonymize":
                    for rule in self._rules_of(plan, entry.collection):
                        affected += self._pseudonymize(transaction, rule, keys, pseudonymize)
                report.outcomes.append(
                    TenantErasureOutcome(
                        collection=entry.collection, action=entry.action, matched=len(keys), affected=affected
                    )
                )

            if plan.tenant_collection in existing:
                report.tenant_document_removed = bool(
                    self._counted(
                        transaction.aql.execute(
                            _REMOVE_TENANT,
                            bind_vars={"@collection": plan.tenant_collection, "key": plan.tenant_key},
                        )
                    )
                )
            transaction.commit_transaction()
        except BaseException:
            self._abort_quietly(transaction)
            raise

        resolved = self._with_known(plan, parent_keys)
        report.parent_keys = {name: keys for name, keys in resolved.items() if name in parent_collections and keys}
        report.unreached = self._residue(plan, entries, resolved, existing)
        logger.info(
            "tenant_erasure.arango_executed",
            tenant_key=plan.tenant_key,
            outcomes={o.collection: o.affected for o in report.outcomes if o.affected},
            edges_removed=report.edges_removed,
            tenant_document_removed=report.tenant_document_removed,
            unreached=report.unreached,
        )
        return report

    # ── validation (before any write) ──────────────────────────────────

    @staticmethod
    def _refuse_unexecutable(plan: TenantErasurePlan) -> None:
        if not plan.tenant_key or not _TENANT_KEY_PATTERN.match(plan.tenant_key):
            # ``doc.tenant_key == ""`` matches every global catalogue row.
            msg = "the plan names no valid tenant key; an empty key would match every global catalogue row"
            raise TenantErasurePlanError(msg)
        seen: set[str] = set()
        for entry in plan.entries:
            for parent in entry.parents:
                if parent.collection not in seen:
                    msg = f"'{entry.collection}' is reached via '{parent.collection}', which the plan declares later"
                    raise TenantErasurePlanError(msg)
            seen.add(entry.collection)
        anonymized = {entry.collection for entry in plan.entries if entry.action == "pseudonymize"}
        ruled = {rule.collection for rule in plan.pseudonymizations}
        if anonymized - ruled:
            msg = f"anonymised collections without a pseudonymisation rule: {sorted(anonymized - ruled)}"
            raise TenantErasurePlanError(msg)

    # ── steps ──────────────────────────────────────────────────────────

    def _select(
        self,
        transaction: TransactionDatabase,
        entry: TenantErasureEntry,
        plan: TenantErasurePlan,
        parent_keys: dict[str, list[str]],
    ) -> list[dict[str, str]]:
        tenant_key = plan.tenant_key
        match, binds = _match(entry, parent_keys, plan.tenant_collection)
        cursor = transaction.aql.execute(
            _SELECT_IDS.format(match=match),
            bind_vars={"@collection": entry.collection, "tenant_key": tenant_key, **binds},
        )
        return [dict(row) for row in cursor]

    @staticmethod
    def _with_known(plan: TenantErasurePlan, parent_keys: dict[str, list[str]]) -> dict[str, list[str]]:
        """This run's parent keys united with those earlier attempts resolved (SEC-001)."""
        merged = {name: list(keys) for name, keys in parent_keys.items()}
        for name, keys in plan.known_parent_keys.items():
            merged[name] = sorted({*merged.get(name, []), *keys})
        return merged

    @staticmethod
    def _rules_of(plan: TenantErasurePlan, collection: str) -> list[TenantErasurePseudonymization]:
        return [rule for rule in plan.pseudonymizations if rule.collection == collection]

    def _pseudonymize(
        self,
        transaction: TransactionDatabase,
        rule: TenantErasurePseudonymization,
        keys: list[str],
        pseudonymize: Callable[[str], str],
    ) -> int:
        """Replace every account key on the rows with its tombstone; empty the free-text names."""
        values = transaction.aql.execute(
            _DISTINCT_VALUES, bind_vars={"@collection": rule.collection, "keys": keys, "field": rule.user_field}
        )
        mapping = {
            value: pseudonymize(value)
            for value in values
            if isinstance(value, str) and value and value != ANONYMIZED_MARKER and not ErasureEngine.is_tombstone(value)
        }
        return self._counted(
            transaction.aql.execute(
                _PSEUDONYMIZE,
                bind_vars={
                    "@collection": rule.collection,
                    "keys": keys,
                    "field": rule.user_field,
                    "mapping": mapping,
                    "clear": dict.fromkeys(rule.clear_fields, ""),
                },
            )
        )

    # ── the completion measurement (after the commit) ───────────────────

    def _residue(
        self,
        plan: TenantErasurePlan,
        entries: Iterable[TenantErasureEntry],
        parent_keys: dict[str, list[str]],
        existing: dict[str, dict[str, Any]],
    ) -> list[str]:
        unreached: list[str] = []
        for entry in entries:
            match, binds = _match(entry, parent_keys, plan.tenant_collection)
            binds = {"@collection": entry.collection, "tenant_key": plan.tenant_key, **binds}
            if entry.action == "delete":
                remaining = self._counted(self._db.aql.execute(_COUNT_MATCHING.format(match=match), bind_vars=binds))
            elif entry.action == "pseudonymize":
                remaining = sum(
                    self._counted(
                        self._db.aql.execute(
                            _COUNT_UNPSEUDONYMIZED.format(match=match),
                            bind_vars={
                                **binds,
                                "field": rule.user_field,
                                "clear_fields": list(rule.clear_fields),
                                "marker": ANONYMIZED_MARKER,
                                "tombstone": _TOMBSTONE_REGEX,
                            },
                        )
                    )
                    for rule in self._rules_of(plan, entry.collection)
                )
            else:
                remaining = 0
            if remaining:
                unreached.append(entry.collection)

        if plan.tenant_collection in existing and self._db.collection(plan.tenant_collection).has(plan.tenant_key):
            unreached.append(plan.tenant_collection)

        classified = {entry.collection for entry in plan.entries} | set(plan.residue_exempt)
        classified.add(plan.tenant_collection)
        for name in sorted(existing):
            if name in classified:
                continue
            stamped = list(
                self._db.aql.execute(_ANY_STAMPED, bind_vars={"@collection": name, "tenant_key": plan.tenant_key})
            )
            if stamped:
                unreached.append(f"undeclared:{name}")
        return unreached

    # ── helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _counted(cursor: Any) -> int:
        return int(next(iter(cursor), 0))

    @staticmethod
    def _abort_quietly(transaction: TransactionDatabase) -> None:
        try:
            transaction.abort_transaction()
        except Exception as exc:  # noqa: BLE001 — the primary error is the one to raise
            logger.warning("tenant_erasure.transaction_abort_failed", error_type=type(exc).__name__)
