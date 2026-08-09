"""ArangoDB repository for botanical families and their species assignments.

Species-visibility scope (Issue #808)
-------------------------------------
The three species-facing reads below — :meth:`~ArangoBotanicalFamilyRepository.get_species_by_family`,
:meth:`~ArangoBotanicalFamilyRepository.get_species_count_by_family` and
:meth:`~ArangoBotanicalFamilyRepository.get_species_counts_by_family` — all apply
the **same** hybrid-catalogue tenant-union predicate, and must keep doing so.

The rule (F-5, #808 R3/R8) is the hybrid-catalogue OR-union established by #324,
now the shared helper :func:`~app.data_access.arango.tenant_scope.tenant_union_predicate`::

    (s.tenant_key == @tenant_key OR s.tenant_key == "" OR s.tenant_key == null)

— own rows plus the global seeds, never another tenant's, never everything. Since
F-3 landed ``tenant_key`` on :mod:`app.domain.models.species` and stamps it on the
interactive create path, the predicate is now *protective* here rather than inert:
a tenant-owned species carries its owner's key, so a foreign tenant's rows fall
outside all three arms and disappear from these family-scoped reads exactly as
they disappear from ``GET /api/v1/species`` (which uses the same union via
``SpeciesService.list_species``).

``tenant_key`` is resolved on these global routes by
:func:`~app.common.auth.get_active_tenant_key` (the F-5 tenant-resolution
mechanism for global-but-tenant-aware routes) and threaded in by the
``botanical-families`` router. It is keyword-only and defaults to ``None`` — the
unscoped whole-catalogue read for the rare internal/system caller — but every HTTP
route supplies the caller's resolved key (``""`` → global-only for an anonymous
caller). ``origin`` (:class:`~app.common.enums.DataOrigin`) is a *provenance*
marker on a different axis (where the data came from), never who owns it, so it
plays no part in this scope.

The load-bearing invariant remains consistency: the count, the per-family count
and the species listing must never diverge in scope, because a count that
disagrees with the list it links to is worse than either alone. That is pinned by
``TestSpeciesScopeConsistency`` in
``tests/unit/data_access/arango/test_botanical_family_repository.py``.
"""

from typing import Any

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.tenant_scope import tenant_union_predicate
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.species import Species


class ArangoBotanicalFamilyRepository(BaseArangoRepository[BotanicalFamily]):
    _model_cls = BotanicalFamily

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.BOTANICAL_FAMILIES)

    def get_all_families(self, offset: int = 0, limit: int = 50) -> tuple[list[BotanicalFamily], int]:
        return super().get_all(offset, limit)

    def get_by_name(self, name: str) -> BotanicalFamily | None:
        return self.find_one_by_field("name", name)

    def create_family(self, family: BotanicalFamily) -> BotanicalFamily:
        return super().create(family)

    def update_family(self, key: str, family: BotanicalFamily) -> BotanicalFamily:
        return super().update(key, family)

    def delete_family(self, key: str) -> bool:
        return super().delete(key)

    @staticmethod
    def _species_scope(tenant_key: str | None) -> tuple[str, dict[str, Any]]:
        """Build the species tenant-scope ``FILTER`` line for these family reads (F-5, #808).

        Returns ``(filter_line, bind_vars)``. When ``tenant_key`` is ``None`` the
        line is empty (unscoped whole-catalogue read); otherwise it is the shared
        three-arm hybrid-catalogue union
        (:func:`~app.data_access.arango.tenant_scope.tenant_union_predicate`) bound
        to the ``s`` loop variable — own rows plus global seeds, never a foreign
        tenant's. All three species reads compose this so their scope can never
        diverge (``TestSpeciesScopeConsistency``, #816).
        """
        if tenant_key is None:
            return "", {}
        predicate, bind_vars = tenant_union_predicate(tenant_key, doc_var="s")
        return f"FILTER {predicate}", bind_vars

    def get_species_by_family(self, family_key: str, *, tenant_key: str | None = None) -> list[Species]:
        """Return every species assigned to ``family_key``, tenant-scoped (F-5, #808).

        Species are related to their family through the scalar ``family_key``
        field written on every create/import/seed path — the ``belongs_to_family``
        graph edge is only produced by the dedup migration and is absent for the
        vast majority of species. Filtering on the scalar field is therefore the
        authoritative assignment and matches how the frontend groups species by
        family.

        ``tenant_key`` applies the hybrid-catalogue union (see
        :meth:`_species_scope`): own rows plus global seeds, never a foreign
        tenant's. It narrows the collection identically to
        :meth:`get_species_count_by_family` and :meth:`get_species_counts_by_family`
        so the listing and the count that links to it can never disagree (#816).
        """
        scope_filter, scope_vars = self._species_scope(tenant_key)
        query = f"""
        FOR s IN {col.SPECIES}
          FILTER s.family_key == @family_key
          {scope_filter}
          SORT s.scientific_name ASC
          RETURN s
        """
        bind_vars = {"family_key": family_key, **scope_vars}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Species(**self._from_doc(doc)) for doc in cursor]

    def get_species_count_by_family(self, family_key: str, *, tenant_key: str | None = None) -> int:
        """Count species assigned to a single family via the scalar ``family_key``.

        See :meth:`get_species_by_family` for why the scalar field — not the
        ``belongs_to_family`` edge — is the source of truth. Used by the single
        family endpoints (``GET/POST/PUT /botanical-families[/{key}]``), which
        need exactly one count; the list endpoint uses the bulk
        :meth:`get_species_counts_by_family` to avoid one count query per row.

        ``tenant_key`` applies the same hybrid-catalogue union as the listing, so
        the number never contradicts the list it links to (#816).
        """
        scope_filter, scope_vars = self._species_scope(tenant_key)
        query = f"""
        RETURN LENGTH(
          FOR s IN {col.SPECIES}
            FILTER s.family_key == @family_key
            {scope_filter}
            RETURN 1
        )
        """
        bind_vars = {"family_key": family_key, **scope_vars}
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, 0)

    def get_species_counts_by_family(self, *, tenant_key: str | None = None) -> dict[str, int]:
        """Return ``{family_key: species_count}`` for all families in one query.

        Aggregates the whole species collection by its scalar ``family_key`` so
        the list endpoint (``GET /botanical-families``) resolves every count in a
        single round-trip instead of one :meth:`get_species_count_by_family` call
        per row. Families with no species are simply absent from the map, so
        callers default a missing key to ``0``.

        ``tenant_key`` applies the same hybrid-catalogue union as the per-family
        count and the listing, so every count on the list page is consistent with
        what the caller can actually list (#816).
        """
        scope_filter, scope_vars = self._species_scope(tenant_key)
        query = f"""
        FOR s IN {col.SPECIES}
          FILTER s.family_key != null AND s.family_key != ""
          {scope_filter}
          COLLECT fam = s.family_key WITH COUNT INTO count
          RETURN {{ family_key: fam, count: count }}
        """
        cursor = self._db.aql.execute(query, bind_vars=scope_vars)
        return {row["family_key"]: row["count"] for row in cursor}
