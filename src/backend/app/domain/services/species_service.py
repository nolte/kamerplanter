from collections.abc import Callable

from app.common.enums import DataOrigin, TenantRole
from app.common.exceptions import ForbiddenError, NotFoundError
from app.common.types import CultivarKey, FamilyKey, SpeciesKey
from app.domain.calculators.scientific_name import normalize_scientific_name
from app.domain.engines.companion_planting_engine import CompanionPlantingEngine
from app.domain.engines.membership_engine import MembershipEngine
from app.domain.interfaces.graph_repository import IGraphRepository
from app.domain.interfaces.species_repository import ISpeciesRepository
from app.domain.models.species import Cultivar, Species
from app.domain.services.phase_sequence_binder import PhaseSequenceBinder

#: Identity / provenance fields the synonym-inheritance (#975) must NEVER copy or
#: overwrite. ``scientific_name``/``scientific_name_normalized`` are the record's
#: identity (and the dedup key), ``origin`` is server-managed provenance,
#: ``synonyms`` is the very field the match is derived from, ``key`` is the
#: document key, and ``created_at``/``updated_at`` are set by the repository.
_INHERIT_PROTECTED_FIELDS: frozenset[str] = frozenset(
    {
        "key",
        "scientific_name",
        "scientific_name_normalized",
        "origin",
        "synonyms",
        "created_at",
        "updated_at",
    }
)

#: Provenance markers that identify the authoritative catalogue — a synonym match
#: against one of these is preferred over a tenant/import record when several
#: fuller candidates exist (REQ-048, #975).
_AUTHORITATIVE_ORIGINS: frozenset[DataOrigin] = frozenset({DataOrigin.SYSTEM, DataOrigin.ENRICHMENT})


def _is_unset(value: object) -> bool:
    """Whether ``value`` is genuinely unset for inheritance purposes (#975).

    "Unset" is exactly ``None``, an empty string, an empty list or an empty dict.
    Everything else — crucially ``0``, ``0.0``, ``False`` and any non-empty enum
    (e.g. ``growth_habit=HERB``) — counts as *set* and is never touched. This is
    why a field left at a non-empty default (``growth_habit`` defaults to ``HERB``,
    ``base_temp`` to ``10.0``) is NOT corrected: the value carries no signal about
    whether it was chosen or defaulted, so the safe rule is to leave every
    non-empty value alone and only fill true blanks.
    """
    return value is None or value == "" or value == [] or value == {}


def _populated_field_count(species: Species) -> int:
    """Count the genuinely-populated fields on a species (fuller-record ranking).

    Used both to pick the *more-populated* synonym match and to rank shadow pairs
    in the report. A field is populated when it is not :func:`_is_unset`.
    """
    return sum(1 for value in species.model_dump().values() if not _is_unset(value))


class SpeciesService:
    def __init__(
        self,
        species_repo: ISpeciesRepository,
        graph_repo: IGraphRepository,
        phase_sequence_binder: PhaseSequenceBinder | None = None,
    ) -> None:
        self._repo = species_repo
        self._graph = graph_repo
        # Optional so the many call sites constructing this service for read paths
        # (and their tests) keep working; when absent, create_species simply does not
        # bind — the same state as before #1006, not a crash.
        self._phase_sequence_binder = phase_sequence_binder

    def list_species(
        self, offset: int = 0, limit: int = 50, *, tenant_key: str | None = None
    ) -> tuple[list[Species], int]:
        """List the species catalogue, tenant-scoped when a ``tenant_key`` is given (F-5, #808).

        ``tenant_key`` is threaded straight to the repository's hybrid-catalogue
        union: the caller's own rows plus the global seeds, never a foreign
        tenant's (#324 both directions). ``None`` (the default) is the unscoped
        system-context read for internal callers; the global HTTP list route
        always supplies the caller's resolved active tenant (``""`` for an
        anonymous/light-mode caller → global-only).
        """
        return self._repo.get_all(offset, limit, tenant_key=tenant_key)

    def get_species(self, key: SpeciesKey, *, tenant_key: str | None = None) -> Species:
        """Return one species by key, tenant-scoped when ``tenant_key`` is given (SEC-001, #808).

        ``tenant_key`` mirrors :meth:`list_species`:

        * ``None`` (the default) — the unscoped **system-context** load internal
          callers use (the update/delete ownership check below, the cultivar and
          companion existence checks, migrations/enrichment): they must resolve a
          species regardless of owner. Never reachable from a raw HTTP read.
        * a string (including ``""``) — the hybrid-catalogue read check: the
          caller's own rows plus the global seeds (``tenant_key == ""``) are
          visible, but a *foreign* tenant's species raises
          :class:`NotFoundError`. It is a 404, never a 403 — ownership hiding, so
          the by-key endpoint cannot be used as a cross-tenant existence oracle.
          An empty ``""`` (anonymous / light-mode / no personal tenant) collapses
          the check to global-only.
        """
        species = self._repo.get_or_raise(key)
        if tenant_key is not None and species.tenant_key not in (tenant_key, ""):
            raise NotFoundError("Species", key)
        return species

    def create_species(self, species: Species) -> Species:
        # Idempotent create (REQ-048 Stufe 1 / R5): when a species with the same
        # canonical dedup key already exists — even if it only differs by the
        # hybrid marker (× vs x), casing or whitespace — return that existing
        # record instead of raising or inserting a duplicate. This is the
        # operator-confirmed resolution: the identify→create path must never
        # accumulate normalization duplicates. The dedup is an atomic UPSERT on
        # scientific_name_normalized (SEC-003), so the check-then-insert window is
        # closed server-side.
        #
        # REQ-048 / #975 — synonym-shadow field inheritance. When no exact
        # normalized duplicate exists, a *new* record may still be a sparse shadow
        # of a fuller one that only differs by name but is linked through synonyms
        # (the sparse `Yucca gigantea` listing the full `Yucca elephantipes` among
        # its synonyms). Before inserting, fill the new record's genuinely-empty
        # fields from that fuller record so the phase-sequence resolver sees the
        # same inputs regardless of which record a plant hangs off — this is what
        # #949 (evergreen perennial routed onto a 126-day annual cycle) tripped on.
        # Additive only: it never overwrites a caller-set value, never touches
        # identity/provenance, and never hides the fuller/global record (#324).
        # Gated on "no exact match" so an idempotent re-create of an existing
        # taxon stays a plain no-op resolve; the UPSERT below still closes the
        # insert race.
        if self._repo.get_by_normalized_scientific_name(species.scientific_name) is None:
            species = self._inherit_unset_from_synonym_match(species)
        created = self._repo.upsert_by_normalized_scientific_name(species)
        # Give the species the phase sequence the seed would have given it (#1006).
        # Without this, every plant created for a runtime-minted species (identify →
        # create, REQ-048) resolved no initial phase and was stored with
        # ``current_phase_key: null`` — the lifecycle engine had nothing to run against.
        # Idempotent: the binder is a no-op when a binding already exists, so the
        # dedup-upsert path returning an existing record does not rebind it.
        if self._phase_sequence_binder is not None:
            self._phase_sequence_binder.bind_default(created)
        return created

    # ── REQ-048 / #975 — synonym-shadow field inheritance ────────────────────

    def _inherit_unset_from_synonym_match(self, species: Species) -> Species:
        """Return ``species`` with its unset fields filled from a fuller synonym match.

        Returns the input unchanged when no more-populated synonym-linked record
        exists. Never mutates the matched record (it is read-only here), so the
        global/system catalogue is untouched (#324).
        """
        match = self._find_fuller_synonym_match(species)
        if match is None:
            return species
        return self._inherit_unset_fields(species, match)

    def _find_fuller_synonym_match(self, species: Species) -> Species | None:
        """Pick the best more-populated record synonym-linked to ``species``.

        The repository AQL prefilter is re-confirmed here with the canonical
        normalization utility (``_is_synonym_linked``) so the match is never
        decided by the looser inline AQL. Only records with strictly more
        populated fields than the new one qualify (a match that is itself empty
        has nothing to give). Among those, an authoritative-origin
        (``system``/``enrichment``) record wins, then the most-populated one.
        """
        candidates = [
            c for c in self._repo.find_synonym_match_candidates(species) if self._is_synonym_linked(species, c)
        ]
        new_count = _populated_field_count(species)
        fuller = [c for c in candidates if _populated_field_count(c) > new_count]
        if not fuller:
            return None
        fuller.sort(
            key=lambda c: (c.origin in _AUTHORITATIVE_ORIGINS, _populated_field_count(c)),
            reverse=True,
        )
        return fuller[0]

    @staticmethod
    def _is_synonym_linked(new: Species, existing: Species) -> bool:
        """Whether two records are synonym-linked under canonical normalization.

        True when the records have *different* canonical names (an exact match is
        the already-handled dedup case, not a shadow) and either lists the other's
        canonical name among its normalized synonyms.
        """
        new_norm = new.scientific_name_normalized
        existing_norm = existing.scientific_name_normalized
        if new_norm == existing_norm:
            return False
        new_syn_norms = {normalize_scientific_name(s) for s in new.synonyms}
        existing_syn_norms = {normalize_scientific_name(s) for s in existing.synonyms}
        return existing_norm in new_syn_norms or new_norm in existing_syn_norms

    @staticmethod
    def _inherit_unset_fields(target: Species, source: Species) -> Species:
        """Copy every genuinely-unset field of ``target`` from ``source``.

        Only fields :func:`_is_unset` on ``target`` and *set* on ``source`` are
        copied; identity/provenance fields (:data:`_INHERIT_PROTECTED_FIELDS`) are
        never touched. A non-empty-but-default value on ``target`` (e.g.
        ``growth_habit=HERB``) is *not* corrected — see :func:`_is_unset`.
        """
        updates: dict[str, object] = {}
        for field_name in type(target).model_fields:
            if field_name in _INHERIT_PROTECTED_FIELDS:
                continue
            if not _is_unset(getattr(target, field_name)):
                continue
            source_value = getattr(source, field_name)
            if _is_unset(source_value):
                continue
            updates[field_name] = source_value
        if not updates:
            return target
        return target.model_copy(update=updates)

    def list_shadow_pairs(self) -> list[dict]:
        """List species shadow pairs, richest-first — the findable report (#975).

        A shadow pair is two records that describe the same taxon: they share a
        normalized name (a legacy exact duplicate) OR are synonym-linked. Each
        entry names the richer and the sparser record with its populated-field
        count and the link type, so the size of the shadowing problem is
        measurable. Read-only and additive: it hides nothing (#324).
        """
        species = self._repo.list_all_species()
        counts = {id(sp): _populated_field_count(sp) for sp in species}
        pairs: list[dict] = []
        for index, first in enumerate(species):
            for second in species[index + 1 :]:
                link = self._shadow_link(first, second)
                if link is None:
                    continue
                richer, sparser = (first, second) if counts[id(first)] >= counts[id(second)] else (second, first)
                pairs.append(
                    {
                        "link": link,
                        "richer": {
                            "key": richer.key,
                            "scientific_name": richer.scientific_name,
                            "populated_field_count": counts[id(richer)],
                        },
                        "sparser": {
                            "key": sparser.key,
                            "scientific_name": sparser.scientific_name,
                            "populated_field_count": counts[id(sparser)],
                        },
                    }
                )
        pairs.sort(key=lambda pair: pair["richer"]["populated_field_count"], reverse=True)
        return pairs

    @classmethod
    def _shadow_link(cls, first: Species, second: Species) -> str | None:
        """Classify how two records shadow each other, or ``None`` if they do not.

        ``"normalized_name"`` when they share the canonical dedup key (a legacy
        exact duplicate the create-time UPSERT would now collapse), otherwise
        ``"synonym"`` when synonym-linked, otherwise ``None``.
        """
        if first.scientific_name_normalized == second.scientific_name_normalized:
            return "normalized_name"
        if cls._is_synonym_linked(first, second):
            return "synonym"
        return None

    def _authorize_species_write(
        self,
        existing: Species,
        key: SpeciesKey,
        *,
        tenant_key: str | None,
        caller_role: TenantRole | None,
        is_platform_admin: bool,
        can_role_write: Callable[[TenantRole], bool],
    ) -> None:
        """Gate a species mutation on ownership, platform-admin and domain role (SEC-002, #808).

        Three-way decision, mirroring the task-template tenant checks in
        :class:`TaskService` (foreign→404, global→refuse-mutation, own→proceed):

        * ``tenant_key is None`` — the unscoped **system-context** write (a
          migration/enrichment path with no HTTP caller). No ownership/role gate,
          same as the pre-SEC-002 behaviour, so those callers keep working.
        * a *foreign* tenant's row (``existing.tenant_key`` is neither the caller's
          nor global) — :class:`NotFoundError` (404). Ownership hiding: the caller
          must not learn a foreign species exists, so this is never a 403.
        * the *global* seed catalogue (``existing.tenant_key == ""``) — only a
          platform admin may mutate it. The row is visible to everyone, so an
          under-privileged refusal is the honest 403, not a 404.
        * the caller's *own* row — the domain role gate (``can_role_write``): a
          viewer must not write (REQ-049 §2.3). A platform admin (the light-mode
          operator, REQ-027, or a ``platform`` lead) bypasses the domain rank.
        """
        if tenant_key is None:
            return
        if existing.tenant_key not in (tenant_key, ""):
            raise NotFoundError("Species", key)
        if existing.tenant_key == "":
            if not is_platform_admin:
                raise ForbiddenError("Only a platform admin may modify the global species catalogue.")
            return
        if not is_platform_admin and not (caller_role is not None and can_role_write(caller_role)):
            raise ForbiddenError("Your role may not modify species in this tenant.")

    def update_species(
        self,
        key: SpeciesKey,
        species: Species,
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> Species:
        # Unscoped load so a foreign key resolves and is answered with the
        # ownership-hiding 404 below, not a leaky "exists but forbidden".
        existing = self.get_species(key)
        self._authorize_species_write(
            existing,
            key,
            tenant_key=tenant_key,
            caller_role=caller_role,
            is_platform_admin=is_platform_admin,
            can_role_write=MembershipEngine.can_edit_resource,
        )
        # The representative reference image is owned by the acquisition
        # pipeline (REQ-029-A §4), not the edit form — preserve it on update.
        species.representative_image_url = existing.representative_image_url
        species.representative_image_attribution = existing.representative_image_attribution
        species.representative_image_license = existing.representative_image_license
        # The provenance marker is server-managed (REQ-001/REQ-011) and never
        # submitted by the edit form — preserve it so a full-replace update never
        # resets an enriched/tenant record back to the 'system' default.
        species.origin = existing.origin
        # tenant ownership (REQ-001 v4.0, #808) is server-managed and never
        # submitted by the edit form — preserve it so a full-replace update never
        # resets a tenant-owned species back to the global default (tenant_key ""),
        # which would silently move it out of its owner's catalogue into the shared
        # one. Mirrors the origin preservation above.
        species.tenant_key = existing.tenant_key
        # cultivation_flexible is master data (seed lifecycle_overrides, ADR-006 E6),
        # not an edit-form field — preserve it so a full-replace update never resets
        # the facultative-cultivation capability flag to its default.
        species.cultivation_flexible = existing.cultivation_flexible
        return self._repo.update(key, species)

    def delete_species(
        self,
        key: SpeciesKey,
        *,
        tenant_key: str | None = None,
        caller_role: TenantRole | None = None,
        is_platform_admin: bool = False,
    ) -> bool:
        existing = self.get_species(key)
        self._authorize_species_write(
            existing,
            key,
            tenant_key=tenant_key,
            caller_role=caller_role,
            is_platform_admin=is_platform_admin,
            # Delete is the irreversibility boundary (REQ-049 §2.3): only a lead.
            can_role_write=MembershipEngine.can_delete_resource,
        )
        return self._repo.delete(key)

    def search_species(
        self,
        name: str | None = None,
        family_key: FamilyKey | None = None,
        *,
        tenant_key: str | None = None,
    ) -> list[Species]:
        """Search the species catalogue, tenant-scoped when ``tenant_key`` is given (SEC-005, #808).

        No HTTP caller reaches this today, but the scoping closes the regression
        trap: ``tenant_key`` threads straight into the repository's hybrid-catalogue
        union (own rows + global seeds, never a foreign tenant's), so a future
        search endpoint cannot re-open the leak F-5 closed for the list read.
        ``None`` (the default) stays the unscoped system-context search.
        """
        return self._repo.search(name=name, family_key=family_key, tenant_key=tenant_key)

    def list_cultivars(self, species_key: SpeciesKey, *, tenant_key: str | None = None) -> list[Cultivar]:
        """List a species' cultivars, tenant-scoped when ``tenant_key`` is given (C-3, #1090).

        ``tenant_key`` mirrors :meth:`list_species` and is threaded straight into
        the repository's hybrid-catalogue union — the caller's own cultivars plus
        the global seeds, never a foreign tenant's (#324 both directions).
        ``None`` (the default) is the unscoped system-context read internal callers
        rely on (P5); the HTTP route always supplies the caller's resolved active
        tenant (``""`` for an anonymous/light-mode caller → global-only).

        The species-existence check is **co-scoped** (operator decision Q3): the same
        ``tenant_key`` is passed to :meth:`get_species`, so asking for the cultivars
        of a *foreign* tenant's species raises :class:`NotFoundError` instead of
        answering an empty list — an empty list would confirm the species key exists
        and turn this route into the cross-tenant oracle SEC-001 closed on the
        species read itself.
        """
        self.get_species(species_key, tenant_key=tenant_key)
        return self._repo.get_cultivars(species_key, tenant_key=tenant_key)

    def create_cultivar(self, cultivar: Cultivar) -> Cultivar:
        self.get_species(cultivar.species_key)
        return self._repo.create_cultivar(cultivar)

    def get_cultivar(self, key: CultivarKey, *, tenant_key: str | None = None) -> Cultivar:
        """Return one cultivar by key, tenant-scoped when ``tenant_key`` is given (C-3, #1090).

        The Cultivar pendant of :meth:`get_species`, with the same two modes:

        * ``None`` (the default) — the unscoped **system-context** load internal
          callers use (the update/delete ownership check below, the dereference
          paths, the seed loaders). Never reachable from a raw HTTP read.
        * a string (including ``""``) — the hybrid-catalogue read check: the
          caller's own cultivars plus the global catalogue (``tenant_key == ""``,
          which after migration ``v0038`` still holds every pre-#1090 row) resolve,
          but a *foreign* tenant's cultivar raises :class:`NotFoundError`.

        The check runs **after** an unscoped load, so a foreign row and an absent
        key are indistinguishable to the caller: both are a 404, never a 403 — the
        by-key endpoint must not become a cross-tenant existence oracle.
        """
        cultivar = self._repo.get_cultivar_or_raise(key)
        if tenant_key is not None and cultivar.tenant_key not in (tenant_key, ""):
            raise NotFoundError("Cultivar", key)
        return cultivar

    def update_cultivar(self, key: CultivarKey, cultivar: Cultivar) -> Cultivar:
        existing = self.get_cultivar(key)
        # Preserve the server-managed provenance marker across a full-replace
        # update (the edit form never submits it).
        cultivar.origin = existing.origin
        # tenant ownership (REQ-001 v4.0, #1090) is server-managed and never submitted
        # by the edit form — preserve it so a full-replace update never resets a
        # tenant-owned cultivar back to the global default (tenant_key ""), which would
        # silently move it out of its owner's catalogue into the shared one. Mirrors
        # the origin preservation above and ``update_species``. The repository repeats
        # this guard for the callers that bypass the service (seed upsert, #1090 P2).
        cultivar.tenant_key = existing.tenant_key
        return self._repo.update_cultivar(key, cultivar)

    def delete_cultivar(self, key: CultivarKey) -> bool:
        self.get_cultivar(key)
        return self._repo.delete_cultivar(key)

    def get_compatible_species(self, species_key: SpeciesKey) -> list[dict]:
        self.get_species(species_key)
        raw = self._graph.get_compatible_species(species_key)
        # Pass the full common_names list straight through from the graph vertex —
        # it is already loaded on the species document (no extra query). The
        # presentation layer derives the layperson-facing display name from it
        # (first entry = German common name by seed convention, REQ-567/A).
        return [
            {
                "species_key": item["species"].get("_key", ""),
                "scientific_name": item["species"].get("scientific_name"),
                "common_names": item["species"].get("common_names", []),
                "score": item.get("score", 0.0),
            }
            for item in raw
        ]

    def get_incompatible_species(self, species_key: SpeciesKey) -> list[dict]:
        self.get_species(species_key)
        raw = self._graph.get_incompatible_species(species_key)
        return [
            {
                "species_key": item["species"].get("_key", ""),
                "scientific_name": item["species"].get("scientific_name"),
                "common_names": item["species"].get("common_names", []),
                "reason": item.get("reason", ""),
            }
            for item in raw
        ]

    def get_companion_counts(self) -> dict[str, dict[str, int]]:
        # Whole-catalogue aggregate: per-species compatible/incompatible companion
        # counts computed in a single batch AQL (no N+1). Companion edges are
        # global reference data, so no tenant scoping applies.
        return self._graph.get_companion_counts()

    def get_companion_recommendations(self, species_key: SpeciesKey) -> dict:
        self.get_species(species_key)
        engine = CompanionPlantingEngine(self._graph, None, self._repo)  # type: ignore[arg-type]
        return engine.get_companion_recommendations(species_key)
