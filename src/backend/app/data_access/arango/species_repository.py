from typing import Any

from arango.database import StandardDatabase

from app.common.types import CultivarKey, FamilyKey, SpeciesKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.query_builder import AQLBuilder, escape_aql_like
from app.data_access.arango.tenant_scope import (
    tenant_union_predicate,
    tenant_union_with_grants_predicate,
)
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
        # Own ∪ global ∪ explicitly granted (#1092). The grant arm is opt-in and
        # only masterdata readers take it — the shared two-arm predicate has 24
        # call sites, one of which narrows further on purpose, and widening it
        # centrally would have widened all of them.
        predicate, bind_vars = tenant_union_with_grants_predicate(tenant_key)
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

    # ── explicit masterdata grants (#1092) ──────────────────────────────────
    #
    # One set of edge primitives serves both catalogues. Species and cultivars are
    # the same hybrid-catalogue shape and share the ``tenant_has_access`` edge, so
    # writing the AQL twice would only create two places for the visibility rule to
    # drift apart — and a grant that behaves differently per record type is the
    # kind of asymmetry nobody discovers until a share silently does nothing.

    def _grant(self, collection: str, record_key: str, to_tenant_key: str) -> None:
        from_id = f"{col.TENANTS}/{to_tenant_key}"
        to_id = f"{collection}/{record_key}"
        existing = list(
            self._db.aql.execute(
                f"FOR g IN {col.TENANT_HAS_ACCESS} FILTER g._from == @f AND g._to == @t LIMIT 1 RETURN 1",
                bind_vars={"f": from_id, "t": to_id},
            )
        )
        if existing:
            return
        self._db.collection(col.TENANT_HAS_ACCESS).insert({"_from": from_id, "_to": to_id})

    def _revoke(self, collection: str, record_key: str, from_tenant_key: str) -> bool:
        cursor = self._db.aql.execute(
            f"FOR g IN {col.TENANT_HAS_ACCESS} FILTER g._from == @f AND g._to == @t "
            f"REMOVE g IN {col.TENANT_HAS_ACCESS} RETURN 1",
            bind_vars={"f": f"{col.TENANTS}/{from_tenant_key}", "t": f"{collection}/{record_key}"},
        )
        return bool(list(cursor))

    def _grants(self, collection: str, record_key: str) -> list[str]:
        cursor = self._db.aql.execute(
            f"FOR g IN {col.TENANT_HAS_ACCESS} FILTER g._to == @t RETURN PARSE_IDENTIFIER(g._from).key",
            bind_vars={"t": f"{collection}/{record_key}"},
        )
        return sorted(cursor)

    def _is_granted(self, collection: str, record_key: str, tenant_key: str) -> bool:
        cursor = self._db.aql.execute(
            f"FOR g IN {col.TENANT_HAS_ACCESS} FILTER g._from == @f AND g._to == @t LIMIT 1 RETURN 1",
            bind_vars={"f": f"{col.TENANTS}/{tenant_key}", "t": f"{collection}/{record_key}"},
        )
        return bool(list(cursor))

    def grant_access(self, species_key: str, to_tenant_key: str) -> None:
        """Let ``to_tenant_key`` see this species without owning it.

        Idempotent: re-granting is a no-op rather than a second edge, so a
        double submit cannot make a later revocation partial.
        """
        self._grant(col.SPECIES, species_key, to_tenant_key)

    def revoke_access(self, species_key: str, from_tenant_key: str) -> bool:
        """Withdraw a grant. Returns whether one was removed.

        The half that gets forgotten: a grant nobody can take back is a permanent
        share dressed as a revocable one.
        """
        return self._revoke(col.SPECIES, species_key, from_tenant_key)

    def list_grants(self, species_key: str) -> list[str]:
        """Tenant keys this species has been granted to."""
        return self._grants(col.SPECIES, species_key)

    def is_granted_to(self, species_key: str, tenant_key: str) -> bool:
        """Does an explicit grant let ``tenant_key`` see this species?

        The by-key counterpart of the grant arm in
        :func:`~app.data_access.arango.tenant_scope.tenant_union_with_grants_predicate`
        — the detail read resolves one document rather than filtering a set, so it
        cannot reuse the predicate and asks the same question directly instead.
        """
        return self._is_granted(col.SPECIES, species_key, tenant_key)

    def grant_cultivar_access(self, cultivar_key: str, to_tenant_key: str) -> None:
        """Share one cultivar with another tenant. See :meth:`grant_access`."""
        self._grant(col.CULTIVARS, cultivar_key, to_tenant_key)

    def revoke_cultivar_access(self, cultivar_key: str, from_tenant_key: str) -> bool:
        """Withdraw a cultivar grant. See :meth:`revoke_access`."""
        return self._revoke(col.CULTIVARS, cultivar_key, from_tenant_key)

    def list_cultivar_grants(self, cultivar_key: str) -> list[str]:
        """Tenant keys this cultivar has been granted to."""
        return self._grants(col.CULTIVARS, cultivar_key)

    def is_cultivar_granted_to(self, cultivar_key: str, tenant_key: str) -> bool:
        """Does an explicit grant let ``tenant_key`` see this cultivar?"""
        return self._is_granted(col.CULTIVARS, cultivar_key, tenant_key)

    def find_visible_by_normalized_scientific_name(self, name: str, tenant_key: str) -> Species | None:
        """Is a species with this dedup key *visible to this caller*? (#1162)

        The third of three questions the same key can be asked, and they are not
        interchangeable — which is the whole point of making the key per-tenant:

        * :meth:`get_by_normalized_scientific_name` — *any* row, unscoped. For
          migrations and reporting, where "does this exist anywhere" is the
          question.
        * :meth:`get_by_normalized_scientific_name_for_tenant` — the caller's
          **own** row. The create path asks this: another tenant's row must not
          stop me minting mine.
        * this one — the hybrid **visibility** union (own ∪ global). The
          identification flow asks this, because "already in the catalogue"
          means "you can see it".

        Using the unscoped one here would report a *foreign* tenant's private
        species as catalogued — an existence oracle in a user-facing flow, and one
        that only became reachable when the key stopped being global.
        """
        predicate, binds = tenant_union_predicate(tenant_key, doc_var="s")
        query = f"""
        FOR s IN {col.SPECIES}
          FILTER s.scientific_name_normalized == @norm AND {predicate}
          LIMIT 1
          RETURN s
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"norm": normalize_scientific_name(name), **binds},
        )
        doc = next(cursor, None)
        return Species(**self._from_doc(doc)) if doc else None

    def get_by_normalized_scientific_name_for_tenant(self, name: str, tenant_key: str) -> Species | None:
        """The tenant-scoped sibling of the lookup above (#1162).

        Since the dedup key became ``(tenant_key, scientific_name_normalized)``,
        "does this taxon already exist?" is only answerable *within a tenant*. The
        unscoped method above still has callers that legitimately want any row
        (reporting, migrations), so it stays — but a create path must use this one,
        or it would find a foreign tenant's row and decline to insert its own.
        """
        query = f"""
        FOR s IN {col.SPECIES}
          FILTER s.scientific_name_normalized == @norm AND s.tenant_key == @tenant
          LIMIT 1
          RETURN s
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"norm": normalize_scientific_name(name), "tenant": tenant_key},
        )
        doc = next(cursor, None)
        return Species(**self._from_doc(doc)) if doc else None

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
        # The dedup key is (tenant_key, scientific_name_normalized) since #1162 —
        # the filter and the unique index must name the same pair, or the UPSERT
        # would look for one thing and the database enforce another. `tenant_key`
        # comes off the model the caller already stamped; the system context
        # ("" = global) therefore keeps exactly one row per taxon in the shared
        # catalogue, which is what REQ-048 Stufe 1 was really protecting.
        query = f"""
        UPSERT {{ scientific_name_normalized: @norm, tenant_key: @tenant }}
        INSERT @doc
        UPDATE {{}} IN {col.SPECIES}
        RETURN NEW
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "norm": species.scientific_name_normalized,
                "tenant": species.tenant_key,
                "doc": doc,
            },
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
        still carries. It is a deliberate **unscoped** full read: the report is
        inherently a cross-comparison of every record, and a shadow pair that spans
        the global catalogue and a tenant's own row is exactly the kind the operator
        must see.

        Species *does* carry a ``tenant_key`` since #808 / PR #1087 — an earlier
        version of this docstring claimed it did not, which was already false when
        written (E2, #1090). The absence of scoping here is therefore a deliberate
        system-context choice, not an "the entity has no owner" consequence: this
        method is reachable only from the operator report, never from a tenant-facing
        route. Any future caller that *is* tenant-facing must not reuse it — use
        :meth:`get_all` with a ``tenant_key`` instead.
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
        # get_all — the caller's own rows plus the global seeds and anything
        # explicitly granted (#1092), never an ungranted foreign tenant's —
        # AND-composed with the optional name/family filters. Search and list must
        # take the *same* arms: a granted species that lists but cannot be found by
        # name reads to the recipient as a broken share rather than a scoping rule.
        # The union bind var is ``tenant_key``; the name/family filters bind under
        # distinct names, so there is no collision. Every value is bound.
        predicate, bind_vars = tenant_union_with_grants_predicate(tenant_key)
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

    def get_cultivars(self, species_key: SpeciesKey, *, tenant_key: str | None = None) -> list[Cultivar]:
        """List a species' cultivars, optionally scoped to a caller's tenant (C-3, #1090).

        Cultivars are a **hybrid catalogue** exactly like species: globally seeded
        rows (``tenant_key == ""``) shared by everyone, plus a tenant's own
        additions. ``tenant_key`` selects the visibility:

        * ``None`` (the default) — no scoping: every cultivar of the species. This
          is the *system-context* read the seed loaders
          (:func:`~app.migrations.seed_data.seed_cultivars` and its siblings) and
          the dereference paths depend on; the seeders in particular must see
          tenant-owned rows, because their name matching is ownership-aware and
          would otherwise re-create a shadow of a tenant's cultivar.
        * a string (including ``""``) — the three-arm hybrid-catalogue union
          (:func:`~app.data_access.arango.tenant_scope.tenant_union_predicate`):
          the caller's own rows **plus** the global seeds, never a *foreign*
          tenant's (#324 both directions). Keeping the ``== ""`` arm is
          load-bearing: migration ``v0038`` deliberately left every pre-#1090
          cultivar global, so a strict ``== @tenant_key`` filter would blank the
          whole catalogue for every real tenant.
          An empty ``""`` (anonymous / light-mode / no personal tenant) collapses
          the union to global-only — never an error, never all tenants.

        The scoped branch is hand-written AQL because the union is an ``OR`` over
        three arms and :meth:`~app.data_access.arango.base_repository.BaseArangoRepository.find_by_field`
        AND-joins its ``extra_filters`` (P3). It calls the F-4 shared helper rather
        than inlining a fifth copy of the predicate, so this read narrows the
        collection identically to the species reads (#816).
        """
        if tenant_key is None:
            return self._cultivars.find_by_field("species_key", species_key)
        # Since #1092 a fourth arm: cultivars shared with this tenant by explicit
        # grant. Community gardens maintain cultivars, so this is the record type
        # the grant feature was actually asked for — species-only would have
        # shipped the mechanism without the use case. The helper needs no
        # collection argument: the arm matches ``__g._to == doc._id``, and an
        # ArangoDB ``_id`` already carries its collection.
        predicate, bind_vars = tenant_union_with_grants_predicate(tenant_key)
        query_vars: dict[str, Any] = {**bind_vars, "species_key": species_key}
        query = (
            f"FOR doc IN {col.CULTIVARS} "
            f"FILTER doc.species_key == @species_key AND {predicate} "
            "SORT doc._key RETURN doc"
        )
        cursor = self._db.aql.execute(query, bind_vars=query_vars)
        return [Cultivar(**self._from_doc(doc)) for doc in cursor]

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
        """Replace a cultivar, keeping the *stored* owning tenant (#1090).

        Tenant ownership is not part of the payload of an update: it is assigned
        once at create time and afterwards only ever changed by an explicit
        migration. This method therefore reads the stored owner and writes it back
        over whatever ``cultivar.tenant_key`` carries — in both directions, so an
        update can neither erase an owner nor grant one.

        The guard lives here rather than only in :class:`SpeciesService` because the
        service is not the only writer. The plant-info seed run calls this method
        **repository-direct** and matches rows by *name*
        (``migrations/seed_data.py``): it hands over a YAML-built ``Cultivar`` whose
        ``tenant_key`` is the model default ``""``. Since the base update is a full
        model dump and an empty string is not ``None``, that value would be written
        — silently moving a tenant-owned cultivar that shares a seeded name into the
        global catalogue every tenant can read and edit. Putting the invariant at
        the last layer before the write covers today's two callers and any future
        repository-direct one alike.

        A key with no stored document falls through untouched, so the base
        repository keeps raising its own :class:`NotFoundError`; a legacy row
        predating the field resolves to the model default ``""`` (global), which is
        exactly the cutover rule.
        """
        stored = self._cultivars.get_by_key(key)
        if stored is not None:
            cultivar.tenant_key = stored.tenant_key
        return self._cultivars.update(key, cultivar)

    def delete_cultivar(self, key: CultivarKey) -> bool:
        return self._cultivars.delete(key)

    def update_field(self, key: SpeciesKey, field: str, value: Any) -> None:
        self.collection.update({"_key": key, field: value, "updated_at": self._now()})
