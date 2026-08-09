from typing import Any

from arango.database import StandardDatabase

from app.common.types import CultivarKey, FamilyKey, SpeciesKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.query_builder import AQLBuilder, escape_aql_like
from app.data_access.arango.tenant_scope import tenant_union_predicate
from app.domain.calculators.scientific_name import normalize_scientific_name
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.species import Cultivar, Species


class ArangoSpeciesRepository(BaseArangoRepository[Species], ISpeciesRepository):
    _model_cls = Species

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.SPECIES)
        self._cultivars = BaseArangoRepository[Cultivar](db, col.CULTIVARS, Cultivar)

    def get_all(self, offset: int = 0, limit: int = 50, *, tenant_key: str | None = None) -> tuple[list[Species], int]:
        """List the species catalogue, optionally scoped to a caller's tenant (F-5, #808).

        Species is a **hybrid catalogue**: globally seeded rows (``tenant_key ==
        ""``) shared by everyone, plus a tenant's own additions. ``tenant_key``
        selects the visibility:

        * ``None`` — no scoping: the whole catalogue. This is the *system-context*
          read used by seed/import/enrichment/reference-image/calendar paths that
          must see every species regardless of owner; it is never reachable from
          the global HTTP list route, which always passes a resolved key.
        * a string (including ``""``) — the three-arm hybrid-catalogue union
          (:func:`~app.data_access.arango.tenant_scope.tenant_union_predicate`):
          the caller's own rows **plus** the global seeds, never a *foreign*
          tenant's rows (#324 both directions). An empty ``""`` (anonymous /
          light-mode / no personal tenant) collapses the union to global-only.

        The union is the F-4 shared helper, not a fifth inline copy, so this read
        narrows the collection identically to the botanical-family species reads
        (``TestSpeciesScopeConsistency``, #816).
        """
        if tenant_key is None:
            return super().get_all(offset, limit)
        predicate, bind_vars = tenant_union_predicate(tenant_key)
        list_vars: dict[str, Any] = {**bind_vars, "offset": offset, "limit": limit}
        list_query = f"FOR doc IN {col.SPECIES} FILTER {predicate} SORT doc._key LIMIT @offset, @limit RETURN doc"
        cursor = self._db.aql.execute(list_query, bind_vars=list_vars)
        items = [Species(**self._from_doc(doc)) for doc in cursor]
        count_query = f"FOR doc IN {col.SPECIES} FILTER {predicate} COLLECT WITH COUNT INTO total RETURN total"
        count_cursor = self._db.aql.execute(count_query, bind_vars=dict(bind_vars))
        total = next(count_cursor, 0)
        return items, total

    def get_by_scientific_name(self, name: str) -> Species | None:
        return self.find_one_by_field("scientific_name", name)

    def get_by_normalized_scientific_name(self, name: str) -> Species | None:
        """Look up a species by the canonical dedup key (REQ-048 Stufe 1).

        The incoming ``name`` is run through the same
        :func:`normalize_scientific_name` utility that fills
        ``scientific_name_normalized`` on write, so a hybrid-marker/casing/
        whitespace variant (``Fragaria × ananassa``) resolves to the stored
        record (``Fragaria x ananassa``). This stays a fast indexed equality
        lookup — the persistent index on ``scientific_name_normalized``
        (``ensure_collections``) backs it, so it never degrades to a scan.
        """
        return self.find_one_by_field("scientific_name_normalized", normalize_scientific_name(name))

    def upsert_by_normalized_scientific_name(self, species: Species) -> Species:
        """Insert ``species`` or return the existing row with the same dedup key.

        A single atomic AQL ``UPSERT`` on ``scientific_name_normalized`` collapses
        the check-then-insert into one server round-trip (REQ-048 R5, SEC-003):
        on a match the existing document is returned unchanged (``UPDATE {}``),
        otherwise the new species is inserted. Behaviour is identical to the prior
        lookup-then-create, but the window between check and insert is closed
        server-side. The remaining TOCTOU-race guarantee against two simultaneous
        inserts of the same normalized key is provided by the DB-level *unique*
        index on ``scientific_name_normalized`` — promoted from the non-unique
        bootstrap index by migration v0025 once v0010 has de-duplicated every
        volume (Issue #624). All three create paths (service, import, seed) route
        through this UPSERT so no path bypasses the dedup.
        """
        doc = self._to_doc(species)
        now = self._now()
        doc["created_at"] = now
        doc["updated_at"] = now
        query = f"""
        UPSERT {{ scientific_name_normalized: @norm }}
        INSERT @doc
        UPDATE {{}} IN {col.SPECIES}
        RETURN NEW
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"norm": species.scientific_name_normalized, "doc": doc},
        )
        return Species(**self._from_doc(next(cursor)))

    def find_synonym_match_candidates(self, species: Species) -> list[Species]:
        """Find existing records synonym-linked to ``species`` (REQ-048, #975).

        Returns every stored species that is a *synonym shadow* of the incoming
        one — the exact case (same normalized name) is deliberately excluded, as
        that is already collapsed by :meth:`upsert_by_normalized_scientific_name`.
        A record is a candidate when, after normalization
        (:func:`normalize_scientific_name`), either:

        * its canonical name equals one of the new record's synonyms
          (``s.scientific_name_normalized IN @new_syn_norms`` — a fast, indexed
          equality against the persistent ``scientific_name_normalized`` index), or
        * one of its synonyms equals the new record's canonical name (the reverse
          direction).

        Direction 1 is precise and index-backed. Direction 2 cannot use the index
        (the stored ``synonyms`` are the human spellings, not normalized), so the
        AQL mirrors :func:`normalize_scientific_name` inline — casefold≈``LOWER``,
        the ``×`` hybrid marker → ``" x "``, whitespace collapsed and trimmed — as
        a *prefilter*. The service re-confirms every returned candidate with the
        real utility (``_is_synonym_linked``), so the AQL is never the authority on
        a match; it only narrows the set the service inspects. The ``synonyms``
        field is coalesced to ``[]`` so a legacy document missing it never errors.
        """
        new_norm = species.scientific_name_normalized
        new_syn_norms = sorted({n for raw in species.synonyms if (n := normalize_scientific_name(raw))})
        query = f"""
        FOR s IN {col.SPECIES}
          FILTER s.scientific_name_normalized != @new_norm
          FILTER (
            s.scientific_name_normalized IN @new_syn_norms
            OR @new_norm IN (
              FOR syn IN (s.synonyms == null ? [] : s.synonyms)
                RETURN TRIM(REGEX_REPLACE(LOWER(SUBSTITUTE(TO_STRING(syn), "×", " x ")), "\\\\s+", " "))
            )
          )
          RETURN s
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"new_norm": new_norm, "new_syn_norms": new_syn_norms},
        )
        return [Species(**self._from_doc(doc)) for doc in cursor]

    def list_all_species(self) -> list[Species]:
        """Return every species document — diagnostic read for the shadow report (#975).

        Backs :meth:`SpeciesService.list_shadow_pairs`, an operator-facing report
        that measures how many normalized-name / synonym shadow pairs the catalogue
        still carries. It is a deliberate full read (the report is inherently a
        cross-comparison of every record); species is a small reference collection
        and carries no ``tenant_key`` (#808), so no scoping applies.
        """
        query = f"FOR s IN {col.SPECIES} RETURN s"
        cursor = self._db.aql.execute(query)
        return [Species(**self._from_doc(doc)) for doc in cursor]

    def set_representative_image(
        self,
        key: SpeciesKey,
        *,
        url: str | None,
        attribution: str | None,
        license: str | None,  # noqa: A002 — matches the model field name
    ) -> None:
        """Partial update of only the representative-image fields (REQ-029-A §4).

        Used by the acquisition pipeline so it never clobbers other species data.
        """
        self.collection.update(
            {
                "_key": key,
                "representative_image_url": url,
                "representative_image_attribution": attribution,
                "representative_image_license": license,
            }
        )

    def search(
        self, name: str | None = None, family_key: FamilyKey | None = None, *, tenant_key: str | None = None
    ) -> list[Species]:
        # Both predicates filter on scalar document fields and compose with AND.
        # ``family_key`` is the scalar assignment written on every create/import/
        # seed path; the ``belongs_to_family`` graph edge is not maintained on the
        # normal path, so an edge traversal here would spuriously return nothing.
        if tenant_key is None:
            # Unscoped system-context search — the AQLBuilder path, unchanged.
            builder = AQLBuilder(col.SPECIES)
            if name:
                # Escape LIKE wildcards so user-typed %, _ or \ match literally
                # instead of acting as pattern metacharacters (SCR-007).
                builder.filter("scientific_name", "LIKE", f"%{escape_aql_like(name)}%")
            if family_key:
                builder.filter("family_key", "==", family_key)
            query, bind_vars = builder.build_list()
            cursor = self._db.aql.execute(query, bind_vars=bind_vars)
            return [Species(**self._from_doc(doc)) for doc in cursor]

        # Tenant-scoped search (SEC-005, #808): the same hybrid-catalogue union as
        # get_all — the caller's own rows plus the global seeds, never a foreign
        # tenant's — AND-composed with the optional name/family filters. The union
        # bind var is ``tenant_key``; the name/family filters bind under distinct
        # names, so there is no collision. Every value is bound, never interpolated.
        predicate, bind_vars = tenant_union_predicate(tenant_key)
        filters: list[str] = [predicate]
        query_vars: dict[str, Any] = dict(bind_vars)
        if name:
            filters.append("doc.scientific_name LIKE @name")
            query_vars["name"] = f"%{escape_aql_like(name)}%"
        if family_key:
            filters.append("doc.family_key == @family_key")
            query_vars["family_key"] = family_key
        filter_clause = " AND ".join(filters)
        query = f"FOR doc IN {col.SPECIES} FILTER {filter_clause} SORT doc._key RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars=query_vars)
        return [Species(**self._from_doc(doc)) for doc in cursor]

    def get_cultivars(self, species_key: SpeciesKey) -> list[Cultivar]:
        return self._cultivars.find_by_field("species_key", species_key)

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        created = self._cultivars.create(cultivar)
        species_id = f"{col.SPECIES}/{cultivar.species_key}"
        cultivar_id = f"{col.CULTIVARS}/{created.key}"
        self.create_edge(col.HAS_CULTIVAR, species_id, cultivar_id)
        return created

    def get_cultivar_by_key(self, key: CultivarKey) -> Cultivar | None:
        return self._cultivars.get_by_key(key)

    def get_cultivar_or_raise(self, key: CultivarKey) -> Cultivar:
        return self._cultivars.get_or_raise(key)

    def update_cultivar(self, key: CultivarKey, cultivar: Cultivar) -> Cultivar:
        return self._cultivars.update(key, cultivar)

    def delete_cultivar(self, key: CultivarKey) -> bool:
        return self._cultivars.delete(key)

    def update_field(self, key: SpeciesKey, field: str, value: Any) -> None:
        self.collection.update({"_key": key, field: value, "updated_at": self._now()})
