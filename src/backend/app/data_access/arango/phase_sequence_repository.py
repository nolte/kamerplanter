from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.phase_sequence_repository import IPhaseSequenceRepository
from app.domain.models.phase_sequence import (
    PhaseDefinition,
    PhaseSequence,
    PhaseSequenceEntry,
)


class ArangoPhaseSequenceRepository(IPhaseSequenceRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.PHASE_DEFINITIONS)

    # ── PhaseDefinition ──

    def get_all_definitions(
        self,
        offset: int,
        limit: int,
        name_filter: str | None = None,
    ) -> tuple[list[PhaseDefinition], int]:
        filter_parts: list[str] = []
        bind_vars: dict = {}
        if name_filter:
            filter_parts.append("LIKE(doc.name, @name_filter, true)")
            bind_vars["name_filter"] = f"%{name_filter}%"

        filt = ("FILTER " + " AND ".join(filter_parts)) if filter_parts else ""
        query = f"FOR doc IN {col.PHASE_DEFINITIONS} {filt} SORT doc.name LIMIT @offset, @limit RETURN doc"
        count_query = f"FOR doc IN {col.PHASE_DEFINITIONS} {filt} COLLECT WITH COUNT INTO total RETURN total"
        bind_vars["offset"] = offset
        bind_vars["limit"] = limit

        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [PhaseDefinition(**self._from_doc(doc)) for doc in cursor]

        count_bind = {k: v for k, v in bind_vars.items() if k not in ("offset", "limit")}
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_bind)
        total = next(count_cursor, 0)

        return items, total

    def get_definition_by_key(self, key: str) -> PhaseDefinition | None:
        doc = self._db.collection(col.PHASE_DEFINITIONS).get(key)
        return PhaseDefinition(**self._from_doc(doc)) if doc else None

    def get_definition_by_name(self, name: str) -> PhaseDefinition | None:
        query = f"FOR doc IN {col.PHASE_DEFINITIONS} FILTER doc.name == @name LIMIT 1 RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars={"name": name})
        doc = next(cursor, None)
        return PhaseDefinition(**self._from_doc(doc)) if doc else None

    def create_definition(self, defn: PhaseDefinition) -> PhaseDefinition:
        coll = self._db.collection(col.PHASE_DEFINITIONS)
        data = self._to_doc(defn)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        return PhaseDefinition(**self._from_doc(result["new"]))

    def update_definition(self, key: str, defn: PhaseDefinition) -> PhaseDefinition:
        coll = self._db.collection(col.PHASE_DEFINITIONS)
        data = self._to_doc(defn)
        data["updated_at"] = self._now()
        result = coll.update({"_key": key, **data}, return_new=True)
        return PhaseDefinition(**self._from_doc(result["new"]))

    def delete_definition(self, key: str) -> bool:
        try:
            self._db.collection(col.PHASE_DEFINITIONS).delete(key)
            return True
        except Exception:
            return False

    def get_definition_usage_count(self, key: str) -> int:
        query = (
            f"FOR doc IN {col.PHASE_SEQUENCE_ENTRIES} "
            f"FILTER doc.phase_definition_key == @key "
            f"COLLECT WITH COUNT INTO total RETURN total"
        )
        cursor = self._db.aql.execute(query, bind_vars={"key": key})
        return next(cursor, 0)

    def get_sequences_for_definition(self, key: str) -> list[PhaseSequence]:
        """Return all PhaseSequences that contain entries referencing this definition."""
        query = (
            f"FOR entry IN {col.PHASE_SEQUENCE_ENTRIES} "
            f"FILTER entry.phase_definition_key == @key "
            f"LET seq = DOCUMENT({col.PHASE_SEQUENCES}, entry.phase_sequence_key) "
            f"FILTER seq != null "
            f"COLLECT s = seq "
            f"RETURN s"
        )
        cursor = self._db.aql.execute(query, bind_vars={"key": key})
        return [PhaseSequence(**self._from_doc(doc)) for doc in cursor]

    # ── PhaseSequence ──

    def get_sequence_by_species(self, species_key: str) -> PhaseSequence | None:
        """Find the PhaseSequence linked to a species via HAS_PHASE_SEQUENCE edge."""
        query = f"FOR v IN 1..1 OUTBOUND @species_id {col.HAS_PHASE_SEQUENCE} RETURN v"
        species_id = f"{col.SPECIES}/{species_key}"
        cursor = self._db.aql.execute(query, bind_vars={"species_id": species_id})
        doc = next(cursor, None)
        return PhaseSequence(**self._from_doc(doc)) if doc else None

    def get_species_for_sequence(self, seq_key: str) -> list[dict]:
        """Return all species linked to a PhaseSequence via HAS_PHASE_SEQUENCE edge."""
        query = (
            f"FOR v IN 1..1 INBOUND @seq_id {col.HAS_PHASE_SEQUENCE} "
            f"FILTER v != null "
            f"RETURN {{ key: v._key, scientific_name: v.scientific_name, "
            f"common_names: v.common_names || [] }}"
        )
        seq_id = f"{col.PHASE_SEQUENCES}/{seq_key}"
        return list(self._db.aql.execute(query, bind_vars={"seq_id": seq_id}))

    def get_all_sequences(
        self,
        offset: int,
        limit: int,
    ) -> tuple[list[PhaseSequence], int]:
        query = f"FOR doc IN {col.PHASE_SEQUENCES} SORT doc.name LIMIT @offset, @limit RETURN doc"
        count_query = f"FOR doc IN {col.PHASE_SEQUENCES} COLLECT WITH COUNT INTO total RETURN total"
        cursor = self._db.aql.execute(
            query,
            bind_vars={"offset": offset, "limit": limit},
        )
        items = [PhaseSequence(**self._from_doc(doc)) for doc in cursor]

        count_cursor = self._db.aql.execute(count_query)
        total = next(count_cursor, 0)

        return items, total

    def get_sequence_by_key(self, key: str) -> PhaseSequence | None:
        doc = self._db.collection(col.PHASE_SEQUENCES).get(key)
        return PhaseSequence(**self._from_doc(doc)) if doc else None

    def create_sequence(self, seq: PhaseSequence) -> PhaseSequence:
        coll = self._db.collection(col.PHASE_SEQUENCES)
        data = self._to_doc(seq)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        created = PhaseSequence(**self._from_doc(result["new"]))
        if seq.species_key:
            self.create_edge(
                col.HAS_PHASE_SEQUENCE,
                f"{col.SPECIES}/{seq.species_key}",
                f"{col.PHASE_SEQUENCES}/{created.key}",
            )
        return created

    def update_sequence(self, key: str, seq: PhaseSequence) -> PhaseSequence:
        coll = self._db.collection(col.PHASE_SEQUENCES)
        data = self._to_doc(seq)
        data["updated_at"] = self._now()
        result = coll.update({"_key": key, **data}, return_new=True)
        return PhaseSequence(**self._from_doc(result["new"]))

    def delete_sequence(self, key: str) -> bool:
        seq_id = f"{col.PHASE_SEQUENCES}/{key}"

        # Cascade delete: remove all entries and their edges
        entries_query = f"FOR doc IN {col.PHASE_SEQUENCE_ENTRIES} FILTER doc.phase_sequence_key == @key RETURN doc._key"
        entry_cursor = self._db.aql.execute(entries_query, bind_vars={"key": key})
        entry_keys = list(entry_cursor)

        for entry_key in entry_keys:
            entry_id = f"{col.PHASE_SEQUENCE_ENTRIES}/{entry_key}"
            # Delete entry_uses_definition edges
            edge_query = (
                f"FOR e IN {col.ENTRY_USES_DEFINITION} "
                f"FILTER e._from == @entry_id "
                f"REMOVE e IN {col.ENTRY_USES_DEFINITION}"
            )
            self._db.aql.execute(edge_query, bind_vars={"entry_id": entry_id})

        # Delete seq_has_entry edges from this sequence
        edge_query = f"FOR e IN {col.SEQ_HAS_ENTRY} FILTER e._from == @seq_id REMOVE e IN {col.SEQ_HAS_ENTRY}"
        self._db.aql.execute(edge_query, bind_vars={"seq_id": seq_id})

        # Delete all entry documents
        delete_entries_query = (
            f"FOR doc IN {col.PHASE_SEQUENCE_ENTRIES} "
            f"FILTER doc.phase_sequence_key == @key "
            f"REMOVE doc IN {col.PHASE_SEQUENCE_ENTRIES}"
        )
        self._db.aql.execute(delete_entries_query, bind_vars={"key": key})

        # Delete the sequence itself
        try:
            self._db.collection(col.PHASE_SEQUENCES).delete(key)
            return True
        except Exception:
            return False

    def get_sequence_usage_count(self, key: str) -> int:
        """Count references to this sequence in workflow_templates and lifecycle_configs."""
        query = (
            f"LET wf_count = LENGTH("
            f"  FOR doc IN {col.WORKFLOW_TEMPLATES} "
            f"  FILTER doc.phase_sequence_key == @key RETURN 1"
            f") "
            f"LET lc_count = LENGTH("
            f"  FOR doc IN {col.LIFECYCLE_CONFIGS} "
            f"  FILTER doc.phase_sequence_key == @key RETURN 1"
            f") "
            f"RETURN wf_count + lc_count"
        )
        cursor = self._db.aql.execute(query, bind_vars={"key": key})
        return next(cursor, 0)

    # ── PhaseSequenceEntry ──

    def get_entries_for_sequence(self, seq_key: str) -> list[PhaseSequenceEntry]:
        query = (
            f"FOR doc IN {col.PHASE_SEQUENCE_ENTRIES} "
            f"FILTER doc.phase_sequence_key == @seq_key "
            f"SORT doc.sequence_order "
            f"RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars={"seq_key": seq_key})
        return [PhaseSequenceEntry(**self._from_doc(doc)) for doc in cursor]

    def get_entry_by_key(self, key: str) -> PhaseSequenceEntry | None:
        doc = self._db.collection(col.PHASE_SEQUENCE_ENTRIES).get(key)
        return PhaseSequenceEntry(**self._from_doc(doc)) if doc else None

    def create_entry(self, entry: PhaseSequenceEntry) -> PhaseSequenceEntry:
        coll = self._db.collection(col.PHASE_SEQUENCE_ENTRIES)
        data = self._to_doc(entry)
        now = self._now()
        data["created_at"] = now
        data["updated_at"] = now
        result = coll.insert(data, return_new=True)
        created = PhaseSequenceEntry(**self._from_doc(result["new"]))

        # Create edges: sequence → entry, entry → definition
        if entry.phase_sequence_key:
            self.create_edge(
                col.SEQ_HAS_ENTRY,
                f"{col.PHASE_SEQUENCES}/{entry.phase_sequence_key}",
                f"{col.PHASE_SEQUENCE_ENTRIES}/{created.key}",
            )
        if entry.phase_definition_key:
            self.create_edge(
                col.ENTRY_USES_DEFINITION,
                f"{col.PHASE_SEQUENCE_ENTRIES}/{created.key}",
                f"{col.PHASE_DEFINITIONS}/{entry.phase_definition_key}",
            )

        return created

    def update_entry(self, key: str, entry: PhaseSequenceEntry) -> PhaseSequenceEntry:
        coll = self._db.collection(col.PHASE_SEQUENCE_ENTRIES)
        data = self._to_doc(entry)
        data["updated_at"] = self._now()
        result = coll.update({"_key": key, **data}, return_new=True)
        return PhaseSequenceEntry(**self._from_doc(result["new"]))

    def delete_entry(self, key: str) -> bool:
        entry_id = f"{col.PHASE_SEQUENCE_ENTRIES}/{key}"

        # Delete edges first
        for edge_col in [col.ENTRY_USES_DEFINITION]:
            query = f"FOR e IN {edge_col} FILTER e._from == @entry_id REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"entry_id": entry_id})

        for edge_col in [col.SEQ_HAS_ENTRY]:
            query = f"FOR e IN {edge_col} FILTER e._to == @entry_id REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"entry_id": entry_id})

        try:
            self._db.collection(col.PHASE_SEQUENCE_ENTRIES).delete(key)
            return True
        except Exception:
            return False

    def reorder_entries(
        self,
        seq_key: str,
        orders: list[dict],
    ) -> list[PhaseSequenceEntry]:
        coll = self._db.collection(col.PHASE_SEQUENCE_ENTRIES)
        now = self._now()
        for item in orders:
            coll.update(
                {
                    "_key": item["key"],
                    "sequence_order": item["sequence_order"],
                    "updated_at": now,
                }
            )
        return self.get_entries_for_sequence(seq_key)
