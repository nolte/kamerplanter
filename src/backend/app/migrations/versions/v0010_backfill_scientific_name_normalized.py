"""v0010_backfill_scientific_name_normalized — canonicalize species dedup keys.

REQ-048 Stufe 1 (Issue #436). Two jobs, both idempotent:

1. **Backfill** — populate ``scientific_name_normalized`` on every existing
   species from its ``scientific_name`` via the shared
   :func:`normalize_scientific_name` utility. Records written before the field
   existed have no stored key; without it the fast indexed dedup lookup finds
   nothing and the identify→create path keeps minting duplicates.

2. **Reconcile duplicate groups** — species whose ``scientific_name`` differs
   only by the hybrid marker (``×`` U+00D7 vs ASCII ``x``), casing or whitespace
   collapse onto one normalized key. Any such group with more than one document
   is merged **generically** (not hard-coded to the observed ``Fragaria`` pair):

   * The **survivor** is chosen deterministically — the row with the most active
     plants first (so active-plant references are never orphaned, risk R-C),
     then the metadata-richer row, then the lexicographically smallest ``_key``.
   * **Every** reference to a loser is moved onto the survivor before the loser
     is deleted — no reference is left dangling (SEC-001, SEC-101). The complete
     set of species-referencing collections/fields and species-incident edges is
     kept in ONE place (``_SPECIES_KEY_SCALAR_REFS`` / ``_SPECIES_KEY_LIST_REFS`` /
     ``_SPECIES_KEY_NESTED_ARRAY_REFS`` / ``_SPECIES_DERIVED_DOCS`` /
     ``_SPECIES_RELATION_EDGES`` / ``_SPECIES_SINGLETON_CHILD_EDGES`` /
     ``_ALL_SPECIES_INCIDENT_EDGES``), so a future new ``species_key`` field is a
     single-line addition — and a pre-flight guard (:meth:`_assert_no_dangling`)
     aborts the merge (rather than orphaning) if any reference to the loser within
     the mapped collections survives the repoint.
   * Species keys nested inside an array of embedded documents are repointed too:
     ``identification_requests.results[].matched_species_key`` records each stored
     candidate's local-master-data match (REQ-029); rewriting the loser key in
     place stops a historical identification request from later resolving a
     deleted species (SEC-101), which would otherwise surface a 404 on the
     "create plant from selection" path.
   * Scalar and list ``species_key`` fields (active grow runs, tasks, retention-
     bound harvest indicators, succession/overwintering/onboarding/starter-kit
     data, cultivars, plants …) are repointed loser→survivor. ``reference_image_
     jobs`` is a derived, species-keyed singleton doc with a *unique* index and a
     deterministic ``_key`` — it cannot be repointed, so the loser's job is
     deleted (it is regenerated per species on the next acquisition run).
   * Species-incident **edges** are repointed onto the survivor rather than blindly
     deleted (SEC-002): companion/enrichment/favourite/starter-kit/run-entry links
     survive the merge, with de-duplication against edges the survivor already has
     and self-loops dropped. The 1:1 child-owning edges (``has_lifecycle`` /
     ``has_phase_sequence``) are repointed only when the survivor has none;
     otherwise the loser's now-redundant child document is deleted, never orphaned.
   * The survivor adopts the loser's *richer metadata*: any field that is empty on
     the survivor is filled from the loser (e.g. the ``Fragaria`` ASCII row's
     ``family_key`` = Rosaceae moves onto the ×-row that carries the live plant).
     The human-facing ``scientific_name`` and the server-managed ``origin`` are
     never overwritten (REQ-048 R3). When the survivor thereby adopts a
     ``family_key`` it had none of, a ``belongs_to_family`` edge is (re)established.

For the concrete observed case — ``Fragaria × ananassa`` (1 active plant, no
family) vs ``Fragaria x ananassa`` (0 active plants, Rosaceae) — the survivor is
the ×-row (active plant); it adopts Rosaceae and the ASCII row is merged away.

Idempotent (M-3): after the first run every normalized key maps to exactly one
document, so the reconcile loop finds no groups and the backfill finds every key
already correct — a re-run is a no-op. Dry-run (M-5) computes the full plan —
including per-collection planned reference moves — and writes nothing.
Irreversible (M-6): the merge deletes the loser document, so there is no honest
inverse.

SEC-003 (accepted follow-up): the ``scientific_name_normalized`` bootstrap index
is intentionally NON-unique so this migration can populate it on volumes that
still carry duplicates without crashing startup. ``create_species`` therefore
resolves duplicates via an atomic UPSERT, but a fully TOCTOU-race-free guarantee
against two concurrent inserts of the same normalized key requires promoting the
index to *unique* — which is only safe in a FOLLOW-UP migration once v0010 has
run on every volume (a unique index cannot be created while duplicates exist).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.domain.calculators.scientific_name import normalize_scientific_name
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

#: Values treated as "empty" when deciding whether a survivor field may adopt the
#: loser's value. Numeric ``0`` and ``False`` are meaningful and intentionally
#: excluded from this set.
_EMPTY_VALUES: tuple[Any, ...] = (None, "", [], {})

#: Document fields never touched by a merge: identity, the display spelling and
#: its derived key (R3), timestamps and the server-managed provenance marker.
_PROTECTED_FIELDS: frozenset[str] = frozenset(
    {"scientific_name", "scientific_name_normalized", "created_at", "updated_at", "origin"}
)

# ── The single source of truth for every species reference (SEC-001) ─────────
# Verified against the domain models and collections.py graph edge definitions.

#: ``(collection, field)`` pairs holding a scalar ``species_key`` reference that
#: is repointed loser→survivor. ``lifecycle_configs`` / ``phase_sequences`` carry
#: a scalar key here *and* a 1:1 child-owning edge below — the edge phase deletes
#: the child on a survivor collision, so the field repoint is harmless either way.
_SPECIES_KEY_SCALAR_REFS: tuple[tuple[str, str], ...] = (
    (col.PLANT_INSTANCES, "species_key"),
    (col.CULTIVARS, "species_key"),
    (col.LIFECYCLE_CONFIGS, "species_key"),
    (col.PHASE_SEQUENCES, "species_key"),
    (col.HARVEST_INDICATORS, "species_key"),
    (col.OVERWINTERING_PROFILE_TEMPLATES, "species_key"),
    (col.TASKS, "species_key"),
    (col.PLANTING_RUN_ENTRIES, "species_key"),
    (col.SUCCESSION_PLANS, "species_key"),
    (col.ONBOARDING_STATES, "species_key"),
)

#: ``(collection, field)`` pairs holding a ``list[str]`` of species keys; the
#: loser key is replaced by the survivor key and the list de-duplicated.
_SPECIES_KEY_LIST_REFS: tuple[tuple[str, str], ...] = (
    (col.ONBOARDING_STATES, "favorite_species_keys"),
    (col.STARTER_KITS, "species_keys"),
)

#: ``(collection, array_field, nested_field)`` triples holding a species key nested
#: inside an array of embedded documents. ``identification_requests.results[]``
#: stores each candidate's local-master-data match (``matched_species_key``, REQ-
#: 029); the loser key is rewritten to the survivor in place so a historical
#: identification request never resolves a deleted species (SEC-101).
_SPECIES_KEY_NESTED_ARRAY_REFS: tuple[tuple[str, str, str], ...] = (
    (col.IDENTIFICATION_REQUESTS, "results", "matched_species_key"),
)

#: Derived, species-keyed singleton documents that carry a *unique* index and a
#: deterministic ``_key`` and thus cannot be repointed — the loser's document is
#: deleted (regenerated per species on demand).
_SPECIES_DERIVED_DOCS: tuple[tuple[str, str], ...] = ((col.REFERENCE_IMAGE_JOBS, "species_key"),)

#: Edges with a species endpoint that are repointed loser→survivor (dedup against
#: existing survivor edges, self-loops dropped). Covers both ``_from`` and
#: ``_to`` species endpoints (``compatible_with`` is species↔species).
_SPECIES_RELATION_EDGES: tuple[str, ...] = (
    col.HAS_CULTIVAR,
    col.COMPATIBLE_WITH,
    col.INCOMPATIBLE_WITH,
    col.ENRICHED_BY,
    col.ENTRY_FOR_SPECIES,
    col.INCLUDES_SPECIES,
    col.USER_FAVORITES,
    col.HAS_HARVEST_INDICATOR,
)

#: 1:1 child-owning edges (species → child). The survivor keeps its own child; on
#: a collision the loser's child document is deleted instead of orphaned.
_SPECIES_SINGLETON_CHILD_EDGES: tuple[tuple[str, str], ...] = (
    (col.HAS_LIFECYCLE, col.LIFECYCLE_CONFIGS),
    (col.HAS_PHASE_SEQUENCE, col.PHASE_SEQUENCES),
)

#: Every edge collection with a species endpoint — the pre-flight orphan guard
#: asserts none remain incident to the loser before it is deleted.
_ALL_SPECIES_INCIDENT_EDGES: tuple[str, ...] = (
    col.BELONGS_TO_FAMILY,
    col.HAS_CULTIVAR,
    col.HAS_LIFECYCLE,
    col.HAS_PHASE_SEQUENCE,
    col.HAS_HARVEST_INDICATOR,
    col.COMPATIBLE_WITH,
    col.INCOMPATIBLE_WITH,
    col.ENRICHED_BY,
    col.ENTRY_FOR_SPECIES,
    col.INCLUDES_SPECIES,
    col.USER_FAVORITES,
)

_EDGE_SYSTEM_FIELDS: frozenset[str] = frozenset({"_key", "_id", "_rev", "_from", "_to"})


def _is_empty(value: Any) -> bool:
    return value in _EMPTY_VALUES


def _richness(doc: dict[str, Any]) -> int:
    """Count the non-empty, non-system fields of a species document.

    A metadata-richer row (more filled fields) beats a sparser one when active
    plant counts tie during survivor selection.
    """
    return sum(1 for k, v in doc.items() if not k.startswith("_") and not _is_empty(v))


def _select_survivor(group: list[dict[str, Any]], active_counts: dict[str, int]) -> dict[str, Any]:
    """Deterministically pick the survivor of a duplicate group.

    Priority: most active plants (avoids orphaning live plants), then richer
    metadata, then the lexicographically smallest ``_key`` as a stable final
    tie-break.
    """
    return sorted(
        group,
        key=lambda d: (-active_counts.get(d["_key"], 0), -_richness(d), d["_key"]),
    )[0]


def _merge_fields(survivor: dict[str, Any], loser: dict[str, Any]) -> dict[str, Any]:
    """Return the survivor fields to fill from the loser (empty-only, no clobber)."""
    updates: dict[str, Any] = {}
    for key, value in loser.items():
        if key.startswith("_") or key in _PROTECTED_FIELDS:
            continue
        if _is_empty(value):
            continue
        if _is_empty(survivor.get(key)):
            updates[key] = value
    return updates


class BackfillScientificNameNormalizedMigration(Migration):
    version = "0010"
    name = "backfill_scientific_name_normalized"
    description = (
        "Backfill species.scientific_name_normalized and reconcile hybrid-marker/"
        "casing/whitespace duplicate species (REQ-048 Stufe 1, Issue #436)."
    )
    reversible = False

    # ── read helpers (top-level — must be no-op-safe on an empty database) ────

    def _load_species(self, db: StandardDatabase) -> list[dict[str, Any]]:
        return list(db.aql.execute(f"FOR d IN {col.SPECIES} RETURN d"))

    def _active_plant_counts(self, db: StandardDatabase) -> dict[str, int]:
        """Map species ``_key`` → number of active (not-removed) plant instances."""
        rows = db.aql.execute(
            f"FOR p IN {col.PLANT_INSTANCES} "
            "FILTER p.removed_on == null "
            "COLLECT sk = p.species_key WITH COUNT INTO n "
            "RETURN {species_key: sk, count: n}"
        )
        return {r["species_key"]: r["count"] for r in rows if r.get("species_key")}

    # ── planning (shared by dry-run and apply) ───────────────────────────────

    def _duplicate_groups(self, species: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group species by their computed normalized key, keeping only collisions."""
        by_key: dict[str, list[dict[str, Any]]] = {}
        for doc in species:
            norm = normalize_scientific_name(doc.get("scientific_name", "") or "")
            by_key.setdefault(norm, []).append(doc)
        return {norm: docs for norm, docs in by_key.items() if len(docs) > 1}

    def _backfill_pairs(self, species: list[dict[str, Any]], skip_keys: set[str]) -> list[dict[str, str]]:
        """Species (excluding merged-away losers) whose stored key is stale/missing."""
        pairs: list[dict[str, str]] = []
        for doc in species:
            if doc["_key"] in skip_keys:
                continue
            computed = normalize_scientific_name(doc.get("scientific_name", "") or "")
            if doc.get("scientific_name_normalized") != computed:
                pairs.append({"key": doc["_key"], "norm": computed})
        return pairs

    def _count_references(self, db: StandardDatabase, loser_key: str) -> dict[str, int]:
        """Count every reference to ``loser_key`` (read-only — powers the dry-run)."""
        loser_id = f"{col.SPECIES}/{loser_key}"
        counts: dict[str, int] = {}
        for collection, field in (*_SPECIES_KEY_SCALAR_REFS, *_SPECIES_DERIVED_DOCS):
            if not db.has_collection(collection):
                continue
            n = sum(1 for d in db.collection(collection).all() if d.get(field) == loser_key)
            if n:
                counts[collection] = counts.get(collection, 0) + n
        for collection, field in _SPECIES_KEY_LIST_REFS:
            if not db.has_collection(collection):
                continue
            n = sum(1 for d in db.collection(collection).all() if loser_key in (d.get(field) or []))
            if n:
                counts[collection] = counts.get(collection, 0) + n
        for collection, array_field, nested_field in _SPECIES_KEY_NESTED_ARRAY_REFS:
            if not db.has_collection(collection):
                continue
            n = sum(
                1
                for d in db.collection(collection).all()
                if any(
                    isinstance(item, dict) and item.get(nested_field) == loser_key
                    for item in (d.get(array_field) or [])
                )
            )
            if n:
                counts[collection] = counts.get(collection, 0) + n
        for edge in _ALL_SPECIES_INCIDENT_EDGES:
            if not db.has_collection(edge):
                continue
            n = sum(1 for e in db.collection(edge).all() if e.get("_from") == loser_id or e.get("_to") == loser_id)
            if n:
                counts[edge] = counts.get(edge, 0) + n
        return counts

    # ── reconcile writes (only ever run when a duplicate group exists) ────────

    def _repoint_scalar_refs(
        self, db: StandardDatabase, loser_key: str, survivor_key: str, moves: dict[str, int]
    ) -> None:
        for collection, field in _SPECIES_KEY_SCALAR_REFS:
            if not db.has_collection(collection):
                continue
            handle = db.collection(collection)
            for doc in list(handle.all()):
                if doc.get(field) == loser_key:
                    handle.update({"_key": doc["_key"], field: survivor_key})
                    moves[collection] = moves.get(collection, 0) + 1

    def _repoint_list_refs(
        self, db: StandardDatabase, loser_key: str, survivor_key: str, moves: dict[str, int]
    ) -> None:
        for collection, field in _SPECIES_KEY_LIST_REFS:
            if not db.has_collection(collection):
                continue
            handle = db.collection(collection)
            for doc in list(handle.all()):
                values = doc.get(field) or []
                if loser_key not in values:
                    continue
                new_values: list[str] = []
                for value in values:
                    replaced = survivor_key if value == loser_key else value
                    if replaced not in new_values:
                        new_values.append(replaced)
                handle.update({"_key": doc["_key"], field: new_values})
                moves[collection] = moves.get(collection, 0) + 1

    def _repoint_nested_array_refs(
        self, db: StandardDatabase, loser_key: str, survivor_key: str, moves: dict[str, int]
    ) -> None:
        for collection, array_field, nested_field in _SPECIES_KEY_NESTED_ARRAY_REFS:
            if not db.has_collection(collection):
                continue
            handle = db.collection(collection)
            for doc in list(handle.all()):
                items = doc.get(array_field) or []
                touched = False
                for item in items:
                    if isinstance(item, dict) and item.get(nested_field) == loser_key:
                        item[nested_field] = survivor_key
                        touched = True
                if touched:
                    handle.update({"_key": doc["_key"], array_field: items})
                    moves[collection] = moves.get(collection, 0) + 1

    def _delete_derived_docs(self, db: StandardDatabase, loser_key: str, moves: dict[str, int]) -> None:
        for collection, field in _SPECIES_DERIVED_DOCS:
            if not db.has_collection(collection):
                continue
            handle = db.collection(collection)
            for doc in list(handle.all()):
                if doc.get(field) == loser_key:
                    handle.delete(doc["_key"])
                    moves[collection] = moves.get(collection, 0) + 1

    def _repoint_relation_edges(
        self, db: StandardDatabase, edge: str, loser_id: str, survivor_id: str, moves: dict[str, int]
    ) -> None:
        if not db.has_collection(edge):
            return
        handle = db.collection(edge)
        edges = list(handle.all())
        survivor_pairs = {(e["_from"], e["_to"]) for e in edges if survivor_id in (e.get("_from"), e.get("_to"))}
        for e in edges:
            if loser_id not in (e.get("_from"), e.get("_to")):
                continue
            new_from = survivor_id if e["_from"] == loser_id else e["_from"]
            new_to = survivor_id if e["_to"] == loser_id else e["_to"]
            handle.delete(e["_key"])  # loser edge always removed
            if new_from == new_to:  # self-loop after the merge → drop
                continue
            if (new_from, new_to) in survivor_pairs:  # survivor already has it → drop
                continue
            copy = {k: v for k, v in e.items() if k not in _EDGE_SYSTEM_FIELDS}
            copy["_from"] = new_from
            copy["_to"] = new_to
            handle.insert(copy)
            survivor_pairs.add((new_from, new_to))
            moves[edge] = moves.get(edge, 0) + 1

    def _merge_singleton_child_edges(
        self, db: StandardDatabase, loser_id: str, survivor_id: str, moves: dict[str, int]
    ) -> None:
        for edge, child_col in _SPECIES_SINGLETON_CHILD_EDGES:
            if not db.has_collection(edge):
                continue
            handle = db.collection(edge)
            edges = list(handle.all())
            survivor_has = any(e.get("_from") == survivor_id for e in edges)
            for e in edges:
                if e.get("_from") != loser_id:
                    continue
                if survivor_has:
                    # Survivor already owns this 1:1 relation → drop the loser's
                    # now-redundant child document rather than orphaning it.
                    child_key = e["_to"].split("/")[-1]
                    if db.has_collection(child_col):
                        db.collection(child_col).delete(child_key)
                    handle.delete(e["_key"])
                else:
                    copy = {k: v for k, v in e.items() if k not in _EDGE_SYSTEM_FIELDS}
                    copy["_from"] = survivor_id
                    copy["_to"] = e["_to"]
                    handle.insert(copy)
                    handle.delete(e["_key"])
                    survivor_has = True
                moves[edge] = moves.get(edge, 0) + 1

    def _ensure_family_edge(self, db: StandardDatabase, survivor_id: str, family_key: str) -> None:
        family_id = f"{col.BOTANICAL_FAMILIES}/{family_key}"
        handle = db.collection(col.BELONGS_TO_FAMILY)
        if not any(e.get("_from") == survivor_id and e.get("_to") == family_id for e in handle.all()):
            handle.insert({"_from": survivor_id, "_to": family_id, "created_at": datetime.now(UTC).isoformat()})

    def _handle_family(
        self,
        db: StandardDatabase,
        loser_id: str,
        survivor_id: str,
        survivor: dict[str, Any],
        had_family: bool,
    ) -> None:
        # The survivor adopted a family it lacked → (re)establish its family edge.
        if not had_family and not _is_empty(survivor.get("family_key")):
            self._ensure_family_edge(db, survivor_id, survivor["family_key"])
        # Drop the loser's own family edge (the loser is about to be deleted).
        if db.has_collection(col.BELONGS_TO_FAMILY):
            handle = db.collection(col.BELONGS_TO_FAMILY)
            for e in list(handle.all()):
                if e.get("_from") == loser_id:
                    handle.delete(e["_key"])

    def _assert_no_dangling(self, db: StandardDatabase, loser_key: str) -> None:
        """Fail loudly if a mapped reference to the loser survived the repoint.

        Re-runs :meth:`_count_references` over every mapped collection (scalar,
        list, nested-array, derived and species-incident edges, SEC-001/SEC-101):
        if a repoint step left one behind, the migration aborts before deleting
        the loser rather than orphaning it. This catches an added ``species_key``
        field whose repoint was wired but whose count/repoint has a bug — it does
        *not* see a reference in a collection missing from the reference map, so
        every new species-referencing collection must be added to that map.
        """
        remaining = self._count_references(db, loser_key)
        if remaining:
            raise RuntimeError(
                f"Refusing to delete species '{loser_key}': unresolved references remain {remaining}. "
                "A species reference was added without updating v0010's reference map."
            )

    def _reconcile_group(
        self,
        db: StandardDatabase,
        norm: str,
        group: list[dict[str, Any]],
        active_counts: dict[str, int],
    ) -> dict[str, Any]:
        """Merge one duplicate group into its survivor; return a report entry."""
        survivor = _select_survivor(group, active_counts)
        survivor_key = survivor["_key"]
        survivor_id = f"{col.SPECIES}/{survivor_key}"
        losers = [d for d in group if d["_key"] != survivor_key]

        moves: dict[str, int] = {}
        merged_fields: set[str] = set()

        for loser in losers:
            loser_key = loser["_key"]
            loser_id = f"{col.SPECIES}/{loser_key}"

            # 1. Move every document-level reference (SEC-001, SEC-101).
            self._repoint_scalar_refs(db, loser_key, survivor_key, moves)
            self._repoint_list_refs(db, loser_key, survivor_key, moves)
            self._repoint_nested_array_refs(db, loser_key, survivor_key, moves)
            self._delete_derived_docs(db, loser_key, moves)

            # 2. Move every species-incident edge (SEC-002) — no blind deletion.
            for edge in _SPECIES_RELATION_EDGES:
                self._repoint_relation_edges(db, edge, loser_id, survivor_id, moves)
            self._merge_singleton_child_edges(db, loser_id, survivor_id, moves)

            # 3. Adopt the loser's richer metadata (never clobber the survivor).
            had_family = not _is_empty(survivor.get("family_key"))
            updates = _merge_fields(survivor, loser)
            if updates:
                db.collection(col.SPECIES).update({"_key": survivor_key, **updates})
                survivor.update(updates)  # keep the in-memory survivor current for the next loser
                merged_fields.update(updates.keys())
            self._handle_family(db, loser_id, survivor_id, survivor, had_family)

            # 4. Verify nothing dangles, then delete the loser (SEC-001 guard).
            self._assert_no_dangling(db, loser_key)
            db.collection(col.SPECIES).delete(loser_key)

        return {
            "normalized": norm,
            "survivor": survivor_key,
            "losers": [d["_key"] for d in losers],
            "plants_repointed": moves.get(col.PLANT_INSTANCES, 0),
            "cultivars_repointed": moves.get(col.CULTIVARS, 0),
            "reference_moves": moves,
            "merged_fields": sorted(merged_fields),
        }

    # ── entry point ──────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        species = self._load_species(db)
        active_counts = self._active_plant_counts(db)
        groups = self._duplicate_groups(species)

        # Survivor selection previewed up front so the dry-run report is honest
        # about which rows would be merged away and which data would move.
        planned_losers: set[str] = set()
        planned_groups: list[dict[str, Any]] = []
        for norm, group in groups.items():
            survivor = _select_survivor(group, active_counts)
            losers = [d["_key"] for d in group if d["_key"] != survivor["_key"]]
            planned_losers.update(losers)
            planned_groups.append({"normalized": norm, "survivor": survivor["_key"], "losers": losers})

        backfill_pairs = self._backfill_pairs(species, planned_losers)
        scanned = len(species)

        if dry_run:
            planned_moves: dict[str, int] = {}
            for loser_key in planned_losers:
                for collection, count in self._count_references(db, loser_key).items():
                    planned_moves[collection] = planned_moves.get(collection, 0) + count
            logger.info(
                "backfill_scientific_name_normalized_dry_run",
                scanned=scanned,
                backfill=len(backfill_pairs),
                groups=len(planned_groups),
                losers=len(planned_losers),
                planned_reference_moves=planned_moves,
            )
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=scanned,
                changed=0,
                dry_run=True,
                details={
                    "backfilled": len(backfill_pairs),
                    "reconciled_groups": planned_groups,
                    "planned_reference_moves": planned_moves,
                },
            )

        # 1. Reconcile duplicate groups first (deletes losers).
        reconciled: list[dict[str, Any]] = []
        for norm, group in groups.items():
            reconciled.append(self._reconcile_group(db, norm, group, active_counts))
        merged_away = sum(len(g["losers"]) for g in reconciled)

        # 2. Backfill the normalized key on every surviving species with a stale/
        #    missing value (single batched update; idempotent by value equality).
        backfilled = 0
        if backfill_pairs:
            db.aql.execute(
                f"FOR pair IN @pairs UPDATE {{_key: pair.key, scientific_name_normalized: pair.norm}} IN {col.SPECIES}",
                bind_vars={"pairs": backfill_pairs},
            )
            backfilled = len(backfill_pairs)

        changed = backfilled + merged_away
        logger.info(
            "backfill_scientific_name_normalized_applied",
            scanned=scanned,
            backfilled=backfilled,
            merged_away=merged_away,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=False,
            details={"backfilled": backfilled, "reconciled_groups": reconciled},
        )


migration = BackfillScientificNameNormalizedMigration()
