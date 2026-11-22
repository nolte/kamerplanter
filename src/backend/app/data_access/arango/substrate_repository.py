from arango.database import StandardDatabase

from app.common.exceptions import ValidationError
from app.common.types import BatchKey, SlotKey, SubstrateKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.graph_edges import edges_touching, remove_edges
from app.data_access.arango.query_builder import escape_aql_like
from app.data_access.arango.tenant_scope import tenant_union_predicate
from app.data_access.arango.transactions import stream_transaction
from app.domain.interfaces.substrate_repository import ISubstrateRepository
from app.domain.models.substrate import Substrate, SubstrateBatch

#: Every named-graph edge that can end at a substrate (``uses_type`` from its batches) — derived (#2560).
_SUBSTRATE_EDGES = edges_touching(col.SUBSTRATES)
_SUBSTRATE_DELETE_WRITE: tuple[str, ...] = tuple(dict.fromkeys((col.SUBSTRATES, *(e for e, _ in _SUBSTRATE_EDGES))))
_SUBSTRATE_DELETE_READ: tuple[str, ...] = (
    col.PLANT_INSTANCES,
    col.PLANTING_RUNS,
    col.SUBSTRATE_BATCHES,
    col.RUN_USES_SUBSTRATE,
)

#: The substrate (no row when it does not exist) with the plants and planting runs that use it (D2, #2560).
_SUBSTRATE_REFERRERS = """
LET s = DOCUMENT(@id)
FILTER s != null
LET batch_ids = (FOR b IN @@batches FILTER b.substrate_key == @key RETURN b._id)
LET batch_keys = (FOR b IN batch_ids RETURN PARSE_IDENTIFIER(b).key)
RETURN {
    plants: LENGTH(FOR p IN @@plants FILTER p.substrate_key == @key RETURN 1),
    runs: LENGTH(UNION_DISTINCT(
        (FOR r IN @@runs FILTER r.substrate_batch_key != null AND r.substrate_batch_key IN batch_keys
            RETURN r._id),
        (FOR e IN @@run_uses FILTER e._to IN batch_ids RETURN e._from)
    ))
}
"""


class ArangoSubstrateRepository(BaseArangoRepository[Substrate], ISubstrateRepository):
    _model_cls = Substrate
    tenant_scope_exempt_reason = (
        "hybrid catalogue (global base media with tenant_key '' plus tenant mixes): get_all_substrates "
        "reads the own-or-global union for a tenant and tenant_key=None is the system-context read of the "
        "seed loaders and the mix resolver (#1195); strict mode would make that read raise and the base "
        "strict filter would hide the global media (#324)"
    )

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.SUBSTRATES)
        self._batches = BaseArangoRepository[SubstrateBatch](db, col.SUBSTRATE_BATCHES, SubstrateBatch)

    # ── Substrate CRUD ────────────────────────────────────────────────

    def get_global_substrates(self) -> list[Substrate]:
        """Every global substrate, the whole catalogue, no row limit (#2027).

        The substrate seed decides whether a seed medium already exists through this
        and nothing wider — the twin of ``ArangoNutrientPlanRepository.get_global_plans``
        (#1957). A row is global when its ``tenant_key`` is empty or absent, so a
        tenant's own mix that carries a seed's identity can no longer stand in for the
        global row and keep it from being created for every tenant. Ordered by
        ``_key`` so the result is the same on every boot.
        """
        cursor = self._db.aql.execute(
            f"""
            FOR doc IN {col.SUBSTRATES}
                FILTER doc.tenant_key == "" OR doc.tenant_key == null
                SORT doc._key
                RETURN doc
            """
        )
        return [Substrate(**self._from_doc(doc)) for doc in cursor]

    def get_all_substrates(
        self, offset: int = 0, limit: int = 50, query: str | None = None, *, tenant_key: str | None = None
    ) -> tuple[list[Substrate], int]:
        """List the substrate catalogue, optionally scoped to a caller's tenant (#1195).

        Substrate is a **hybrid catalogue**: the seeded base media
        (``tenant_key == ""``) plus a tenant's own mixes. ``tenant_key`` selects
        the visibility:

        * ``None`` — no scoping: the whole catalogue. The *system-context* read
          the seed loaders and the mix resolver depend on; never reachable from a
          raw HTTP read, which always passes a resolved key.
        * a string (including ``""``) — the hybrid union via the shared F-4 helper:
          the caller's own mixes **plus** the global media, never a foreign
          tenant's mix. ``""`` (anonymous / light mode) collapses it to
          global-only.

        The union is the shared helper rather than an inline copy, so this read
        narrows the collection identically to the species reads (#324, #816).
        """
        scope, scope_binds = tenant_union_predicate(tenant_key) if tenant_key is not None else ("true", {})

        if query is None or not query.strip():
            if tenant_key is None:
                return super().get_all(offset, limit)
            list_query = (
                f"FOR doc IN {self._collection_name} FILTER {scope} SORT doc._key LIMIT @offset, @limit RETURN doc"
            )
            cursor = self._db.aql.execute(list_query, bind_vars={**scope_binds, "offset": offset, "limit": limit})
            items = self._wrap_many([self._from_doc(doc) for doc in cursor])
            count_query = (
                f"FOR doc IN {self._collection_name} FILTER {scope} COLLECT WITH COUNT INTO total RETURN total"
            )
            total = int(next(self._db.aql.execute(count_query, bind_vars=dict(scope_binds)), 0))
            return items, total

        # Case-insensitive substring match over the two catalogue names and the
        # brand, so the natural pre-create duplicate check ("does a BioBizz
        # Light-Mix already exist?") actually finds it. Before this the endpoint
        # took only offset/limit, so every ``query`` was dropped and the check
        # always said "no such substrate" — a wrong answer that lets agents seed
        # duplicates (#1099 defect 5). The term is wrapped in a LIKE pattern with
        # its wildcards escaped and bound as a parameter (never interpolated), and
        # the third LIKE argument makes the match case-insensitive.
        pattern = f"%{escape_aql_like(query.strip())}%"
        # The scope is AND-composed *around* the name/brand OR-group. Without the
        # inner parentheses the tenant arm would bind against only the first LIKE
        # and a foreign tenant's mix would surface on a brand match — the widest
        # possible leak, from operator precedence.
        filter_clause = (
            f"FILTER {scope} AND ("
            "LIKE(doc.name_de, @pattern, true) "
            "OR LIKE(doc.name_en, @pattern, true) "
            "OR LIKE(doc.brand, @pattern, true))"
        )
        list_query = (
            f"FOR doc IN {self._collection_name} {filter_clause} SORT doc._key LIMIT @offset, @limit RETURN doc"
        )
        cursor = self._db.aql.execute(
            list_query,
            bind_vars={**scope_binds, "pattern": pattern, "offset": offset, "limit": limit},
        )
        items = self._wrap_many([self._from_doc(doc) for doc in cursor])

        count_query = f"FOR doc IN {self._collection_name} {filter_clause} COLLECT WITH COUNT INTO total RETURN total"
        count_cursor = self._db.aql.execute(count_query, bind_vars={**scope_binds, "pattern": pattern})
        total = int(next(count_cursor, 0))
        return items, total

    def get_substrate_by_key(self, key: SubstrateKey) -> Substrate | None:
        return super().get_by_key(key)

    def get_substrate_or_raise(self, key: SubstrateKey) -> Substrate:
        return super().get_or_raise(key)

    def create_substrate(self, substrate: Substrate) -> Substrate:
        return super().create(substrate)

    def update_substrate(self, key: SubstrateKey, substrate: Substrate) -> Substrate:
        return super().update(key, substrate)

    def delete_substrate(self, key: SubstrateKey) -> bool:
        """Remove the substrate and every graph edge on it — refused while a plant or a run uses it (#2560, D2).

        One stream transaction: the references are counted and the row removed under the same snapshot, so a plant
        written between a check and the delete cannot slip through. A plant references the substrate by its
        ``substrate_key``; a planting run through its batch (``substrate_batch_key`` or a ``run_uses_substrate``
        edge to a batch whose ``substrate_key`` is this one). Referrers are counted across tenants: a global
        medium may be used by any tenant, and nulling another tenant's field silently is what D2 rules out.

        The edges are derived (:data:`_SUBSTRATE_EDGES`): ``uses_type`` from the batches used to stay behind. The
        remaining field referrers — a batch's ``substrate_key``, a mix component, a bed's
        ``soil_profile.substrate_key`` — are not settled here; ``tests/unit/guards/
        test_deletes_reach_their_derived_edges.py`` holds the reason for each.

        Raises:
            ValidationError: 422 while a plant or a planting run references the substrate.

        Returns:
            ``True`` when the substrate was removed, ``False`` when it did not exist (nothing is written then).
        """
        substrate_id = f"{col.SUBSTRATES}/{key}"
        with stream_transaction(
            self._db, write=_SUBSTRATE_DELETE_WRITE, read=_SUBSTRATE_DELETE_READ, entity="substrate"
        ) as txn:
            rows = list(
                txn.aql.execute(
                    _SUBSTRATE_REFERRERS,
                    bind_vars={
                        "id": substrate_id,
                        "key": key,
                        "@batches": col.SUBSTRATE_BATCHES,
                        "@plants": col.PLANT_INSTANCES,
                        "@runs": col.PLANTING_RUNS,
                        "@run_uses": col.RUN_USES_SUBSTRATE,
                    },
                )
            )
            if not rows:
                return False
            plants, runs = int(rows[0]["plants"]), int(rows[0]["runs"])
            if plants or runs:
                raise ValidationError(
                    "A substrate that plants or planting runs still use cannot be deleted.",
                    details=[
                        {
                            "field": "key",
                            "reason": f"used by {plants} plant(s) and {runs} planting run(s)",
                            "code": "SUBSTRATE_IN_USE",
                        }
                    ],
                )
            for edge, field_name in _SUBSTRATE_EDGES:
                remove_edges(txn, edge, field_name, [substrate_id])
            txn.collection(col.SUBSTRATES).delete(key)
        return True

    # ── Substrate Batch CRUD ──────────────────────────────────────────

    def get_batch_by_key(self, key: BatchKey) -> SubstrateBatch | None:
        return self._batches.get_by_key(key)

    def get_batch_or_raise(self, key: BatchKey) -> SubstrateBatch:
        return self._batches.get_or_raise(key)

    def get_batches_by_substrate(self, substrate_key: SubstrateKey, *, tenant_key: str | None) -> list[SubstrateBatch]:
        """List a substrate's batches, scoped to one tenant (#1195).

        **Strict equality, not the hybrid union.** A batch belongs to exactly one
        tenant — there is no global batch to share — so ``== @tenant_key`` is the
        correct filter and admitting ``""`` would hand every caller the rows the
        ``v0043`` backfill could not attribute.

        ``tenant_key=None`` is the unscoped system-context read the migration and
        the reuse engine use. Before #1195 that was the *only* behaviour, and it
        was reachable straight from ``GET /substrates/{key}/batches`` — which
        returned every tenant's batches to any authenticated caller.
        """
        if tenant_key is None:
            return self._batches.find_by_field("substrate_key", substrate_key)
        query = (
            f"FOR doc IN {col.SUBSTRATE_BATCHES} "
            "FILTER doc.substrate_key == @substrate_key AND doc.tenant_key == @tenant_key "
            "SORT doc._key RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"substrate_key": substrate_key, "tenant_key": tenant_key})
        return [SubstrateBatch(**self._from_doc(doc)) for doc in cursor]

    def create_batch(self, batch: SubstrateBatch) -> SubstrateBatch:
        created = self._batches.create(batch)
        if batch.substrate_key:
            batch_id_full = f"{col.SUBSTRATE_BATCHES}/{created.key}"
            substrate_id = f"{col.SUBSTRATES}/{batch.substrate_key}"
            self.create_edge(
                col.USES_TYPE,
                batch_id_full,
                substrate_id,
                data={
                    "batch_id": batch.batch_id,
                },
            )
        return created

    def update_batch(self, key: BatchKey, batch: SubstrateBatch) -> SubstrateBatch:
        return self._batches.update(key, batch)

    def delete_batch(self, key: BatchKey) -> bool:
        batch_id = f"{col.SUBSTRATE_BATCHES}/{key}"
        self.delete_edges(col.USES_TYPE, batch_id)
        self.delete_edges(col.FILLED_WITH, batch_id, direction="inbound")
        return self._batches.delete(key)

    def assign_batch_to_slot(self, batch_key: BatchKey, slot_key: SlotKey) -> dict:
        slot_id = f"{col.SLOTS}/{slot_key}"
        batch_id = f"{col.SUBSTRATE_BATCHES}/{batch_key}"
        return self.create_edge(col.FILLED_WITH, slot_id, batch_id)
