from datetime import UTC, datetime

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col
from app.domain.interfaces.favorites_repository import IFavoritesRepository
from app.domain.interfaces.nutrient_plan_repository import INutrientPlanRepository

#: Collections a favourite may target, in resolution order. A key is looked up
#: in each until one holds a row **visible to the caller**.
_FAVOURITABLE_COLLECTIONS = (
    col.SPECIES,
    col.NUTRIENT_PLANS,
    col.FERTILIZERS,
    col.ACTIVITIES,
    col.BOTANICAL_FAMILIES,
    col.SUBSTRATES,
)

# Catalogue collections whose rows carry a ``tenant_key`` ownership marker: some
# rows are global (``tenant_key == ""`` or absent, e.g. seeded system
# catalogues), others are owned by a single tenant. Favouriting one of these must
# respect tenant isolation (#965 item 2).
#
# ``activities`` is included beyond the two catalogues named in the #965 report:
# ``Activity.tenant_key`` (app/domain/models/activity.py) is a real ownership
# marker (system rows carry ``is_system == true``, tenant rows an owning
# ``tenant_key``), so the same cross-tenant leak applied to it and is closed the
# same way.
#
# ``species`` joined the set in #1538. The comment that stood here claimed
# species were "purely global" and carried no ``tenant_key``; that was true when
# #965 was written and stopped being true with #808 (REQ-001 v4.0), which added
# ``Species.tenant_key`` and the hybrid-catalogue read predicate that consumes
# it. Until #1538 a *foreign* tenant's private species was therefore genuinely
# favouritable — measured, not inferred. ``botanical_families`` is the only
# member of :data:`_FAVOURITABLE_COLLECTIONS` that still carries no ownership
# field at all, so it alone stays unguarded. **Adding a collection to
# :data:`_FAVOURITABLE_COLLECTIONS` means checking its model for a
# ``tenant_key`` and adding it here too.**
_TENANT_OWNED_CATALOG_COLLECTIONS = frozenset(
    {
        col.SPECIES,
        col.NUTRIENT_PLANS,
        col.FERTILIZERS,
        col.ACTIVITIES,
        col.SUBSTRATES,
    }
)


def _grantable_collections() -> frozenset[str]:
    """Favouritable collections whose rows an owner can share across tenants (#1092).

    **Derived, not listed.** The authority is the ``tenant_has_access`` edge
    definition in
    :data:`~app.data_access.arango.collections.GRAPH_EDGE_DEFINITIONS`, whose own
    comment calls widening ``to_vertex_collections`` "a deliberate widening of
    what may be granted, not a formality" — so this set follows it automatically,
    intersected with what is favouritable at all (cultivars are grantable but not
    a favourite target).

    Writing the members out by hand would have rebuilt exactly the defect this
    change repairs, only mirrored: ``_TENANT_OWNED_CATALOG_COLLECTIONS`` drifted
    away from the models and *leaked*; a hand-listed grant set drifting away from
    the graph would make a shared row readable via ``GET /species/{key}`` yet
    unfavouritable — the #324 over-strictness class (review finding SCR-002).
    """
    granted: frozenset[str] = frozenset()
    for definition in col.GRAPH_EDGE_DEFINITIONS:
        if definition["edge_collection"] == col.TENANT_HAS_ACCESS:
            granted = frozenset(definition["to_vertex_collections"])
            break
    return granted & frozenset(_FAVOURITABLE_COLLECTIONS)


#: A grant is the **third** way a row becomes visible, after own-tenant and global.
_GRANTABLE_COLLECTIONS = _grantable_collections()

#: Favouriting one of these cascades to the fertilizers it uses (REQ-020 §1).
#: A frozenset rather than an ``==`` so the rule reads as a property of the
#: target type; today it holds exactly one member.
_CASCADING_COLLECTIONS = frozenset({col.NUTRIENT_PLANS})


class FavoritesService:
    """Favourite a catalogue entry, with cascade and tenant visibility (REQ-020).

    Reaches its data only through repositories (#1638): the favourite edges and
    the by-key target probes through :class:`IFavoritesRepository`, the plan
    reads through :class:`INutrientPlanRepository`, which owns
    ``nutrient_plans``.
    """

    def __init__(self, favorites_repo: IFavoritesRepository, plan_repo: INutrientPlanRepository) -> None:
        self._repo = favorites_repo
        self._plan_repo = plan_repo

    def _add_one(
        self,
        user_key: str,
        target_key: str,
        *,
        tenant_key: str,
        source: str = "manual",
        cascade_from_key: str | None = None,
    ) -> dict:
        """Create or upsert exactly ONE edge. Never cascades.

        The cascade lives in :meth:`add_favorite` and this method is what it
        calls, so a cascade can never re-enter one. That is structural rather
        than a property of the data: today ``cascade_fertilizers`` only ever
        adds fertilizers, which are not a cascading target — but nothing in the
        code said so, and the next cascading target would have made recursion a
        live question. It is not one.

        Upserts — upgrades cascade→manual.

        Favourites are personal and span tenants (product decision, #965): a user
        may favourite a **global** catalogue entry (``tenant_key == ""``) or one
        owned by their **own** tenant, but never a **foreign** tenant's entry.

        ``tenant_key`` is anchored on the caller's **active** tenant
        (``ctx.tenant_key`` of the request), not the full set of the user's
        memberships. Resolving every membership tenant on each write would be
        heavyweight and there is no cheap membership lookup on this path; every
        other tenant-scoped route already anchors on the active tenant, so this
        stays consistent. The practical effect: favouriting an own-tenant
        catalogue entry works while acting *inside that tenant* — which is the
        only context the tenant-scoped router (``/t/{slug}/favorites``) runs in.
        It is keyword-only so a route that forgets to thread it fails loudly
        (#948) rather than silently defaulting to a global-only view.

        The tenant predicate is enforced only for tenant-owned catalogues
        (:data:`_TENANT_OWNED_CATALOG_COLLECTIONS`); ``botanical_families``
        carries no ownership field and is unaffected. Since #1538 the predicate
        is part of :meth:`_resolve_collection` rather than a second check run
        after it, so there is exactly **one** decision point and the router
        surface cannot drift from it. A foreign-tenant target therefore takes the
        same unresolved arm an unknown key takes and raises the same
        :class:`NotFoundError` (404, never 403 — ownership hiding, matching
        ``verify_tenant_read_access``).
        """
        target_collection = self._resolve_collection(target_key, tenant_key=tenant_key)
        if not target_collection:
            # SEC-002 / #1538: unknown, unresolvable and foreign are one answer
            # and now also one code path. A ValueError here used to route through
            # the unhandled-error handler, making an unresolvable key (500)
            # distinguishable from a foreign-but-real one (404) — a cross-tenant
            # existence oracle on catalogue keys.
            raise NotFoundError("favorite target", target_key)

        from_id = f"{col.USERS}/{user_key}"
        to_id = f"{target_collection}/{target_key}"

        edge = self._repo.find_edge(from_id, to_id)

        if edge is not None:
            # The resolved collection is authoritative, not the stored field: an
            # edge written before `target_type` existed carries none, and the
            # caller decides whether to cascade from this value. `to_id` was
            # built from `target_collection`, so the two can never disagree.
            edge["target_type"] = target_collection
            # Upgrade cascade→manual if user explicitly favorites
            if source == "manual" and edge.get("source") == "cascade":
                self._repo.promote_to_manual(edge["_key"])
                edge["source"] = "manual"
                edge["cascade_from_key"] = None
            return edge

        now = datetime.now(UTC).isoformat()
        edge_data = {
            "_from": from_id,
            "_to": to_id,
            "source": source,
            "cascade_from_key": cascade_from_key,
            "target_type": target_collection,
            "favorited_at": now,
        }
        # A concurrent insert of the same pair returns the winner's edge; the
        # resolved collection stays authoritative for it, as on the upsert arm.
        stored = self._repo.insert_edge(edge_data)
        stored["target_type"] = target_collection
        return stored

    def add_favorite(
        self,
        user_key: str,
        target_key: str,
        *,
        tenant_key: str,
        source: str = "manual",
        cascade_from_key: str | None = None,
    ) -> dict:
        """Favourite one entity, cascading where the target type says to (#1233).

        Creation and removal now agree. Removal has honoured ``cascade_cleanup``
        since REQ-020 v1.5 (:meth:`remove_favorite` -> :meth:`_cleanup_cascade`),
        while creation cascaded only inside the onboarding wizard, which called
        :meth:`cascade_fertilizers` by hand. Everywhere else ``POST /favorites``
        with a nutrient-plan key produced no fertilizer favourites at all — so
        removal cleaned up something creation could no longer create, and
        REQ-020 §1's promise that favourites can be managed "jederzeit in den
        jeweiligen Detailansichten" held for species only.

        The cascade fires on an already-existing edge too. That is deliberate:
        re-favouriting is how a plan favourited before this change backfills the
        fertilizers it never cascaded, and :meth:`_add_one` is an upsert, so
        doing it twice costs nothing.
        """
        edge = self._add_one(
            user_key,
            target_key,
            tenant_key=tenant_key,
            source=source,
            cascade_from_key=cascade_from_key,
        )
        if edge.get("target_type") in _CASCADING_COLLECTIONS:
            self.cascade_fertilizers(user_key, target_key, tenant_key=tenant_key)
        return edge

    def remove_favorite(
        self,
        user_key: str,
        target_key: str,
        cascade_cleanup: bool = True,
    ) -> bool:
        """Remove a favorite edge. Optionally clean up cascade edges.

        No tenant predicate is applied on removal: the edge is anchored on the
        caller's ``user_key`` and only their **own** edges are ever removed, so
        removal cannot leak across tenants. Enforcing the add-path predicate here
        would instead *trap* any edge that leaked before the #965 fix, blocking
        the user from cleaning it up. Removal therefore stays permissive.

        **Removal does not resolve the key at all** (#1538, review finding
        SCR-001). It used to, and once :meth:`_resolve_collection` became
        tenant-aware the two sides began answering *different* questions about
        the same key: the add path deliberately walks past a row the caller
        cannot see and lands on the next visible one, while a tenant-blind
        removal stops at the first catalogue that merely *holds* the key. With
        the same key in ``species`` (foreign) and ``substrates`` (global), the
        add wrote ``substrates/K`` and the removal addressed ``species/K`` —
        the user could not delete the favourite they had just created, and
        ``cascade_cleanup`` fired on the wrong condition. Before this PR both
        sides were equally blind and therefore agreed; the asymmetry was
        introduced here, so it is closed here.

        The stored edge is the authoritative record of which catalogue a
        favourite points at — ``_to`` was built from the collection the add path
        resolved. Reading it back is both strictly permissive (no predicate can
        trap an edge) and symmetric with the add by construction, without
        importing the add-path predicate.

        :meth:`_cleanup_cascade` now runs unconditionally when ``cascade_cleanup``
        is set, rather than behind a nutrient-plan check. It only ever matches
        edges whose ``source == "cascade"`` **and** ``cascade_from_key ==
        target_key``, which nothing but a plan favourite can produce — so the
        collection check it used to hide behind bought nothing and cost the
        resolution. It also preserves the pre-existing ability to clean up
        cascade edges orphaned by an already-removed plan edge.
        """
        from_id = f"{col.USERS}/{user_key}"

        if cascade_cleanup:
            self._cleanup_cascade(user_key, target_key)

        return self._repo.remove_edges_to_key(from_id, target_key) > 0

    def list_favorites(
        self,
        user_key: str,
        entity_type: str | None = None,
    ) -> list[dict]:
        """List all favorites for a user, optionally filtered by entity type."""
        return self._repo.list_edges(f"{col.USERS}/{user_key}", entity_type)

    def get_matching_nutrient_plans(
        self,
        species_keys: list[str],
        *,
        tenant_key: str,
    ) -> list[dict]:
        """Template nutrient plans linked to any of ``species_keys`` that the tenant may see (#1561, #1618).

        **What this returns, stated once so the next reader does not have to
        infer it from three disagreeing sources.** It returns *template* plans,
        only those visible to ``tenant_key``, and only those whose
        ``species_keys`` relation contains at least one requested species. A plan
        with an empty relation matches no species (operator decision
        2026-09-23, #1618); each row names the species it matched in
        ``matched_species``.

        ``tenant_key`` reached nothing before this change: the AQL ran **without**
        ``bind_vars`` and its only filter was ``is_template == true OR
        origin == "system"``. Every row any tenant flagged as a template was
        served to any authenticated caller of any tenant, together with the
        product name and brand of every fertilizer it uses — a cross-tenant
        read, not an existence oracle. The parameter existed and read like a
        filter at the call site, which is why nothing looked wrong; the router
        did not pass it either.

        The predicate is the hybrid-catalogue union
        :func:`~app.data_access.arango.tenant_scope.tenant_union_predicate`
        builds — own ∪ global — the **same** one
        :class:`~app.data_access.arango.nutrient_plan_repository.ArangoNutrientPlanRepository.list_all`
        applies to this collection, so the two reads of ``nutrient_plans`` answer
        one visibility question instead of two. A strict
        ``tenant_key == @tenant_key`` filter would hide the seeded catalogue and
        empty the onboarding step — the #324 regression.

        Deliberately **not** the ``…_with_grants`` variant: ``tenant_has_access``
        is declared only ``tenants -> species | cultivars``
        (``col.GRAPH_EDGE_DEFINITIONS``), so a plan cannot carry a grant. The
        grant arm would be a correlated subquery per candidate row that can
        never match.

        ``tenant_key`` is keyword-only and has no default (#948, the drift class
        this endpoint is an instance of): an omitted predicate must not be
        spellable at a call site. An empty string is the anonymous / light-mode
        context and collapses the union to global-only, exactly as
        :meth:`_is_visible` does.

        **``species_keys`` is a filter since #1618.** Until then it was accepted
        and ignored, because no species↔plan relation existed; the relation is
        now ``NutrientPlan.species_keys``, maintained on the seeded template plans
        from their source documents and editable on tenant plans. The filter runs
        in the repository query, next to the visibility predicate, so a caller
        cannot receive a row that failed either.
        """
        if not species_keys:
            return []

        return self._plan_repo.list_template_plan_summaries(tenant_key=tenant_key, species_keys=species_keys)

    def cascade_fertilizers(self, user_key: str, nutrient_plan_key: str, *, tenant_key: str) -> list[dict]:
        """Traverse plan → entries → fertilizers and create cascade favorite edges.

        ``tenant_key`` is keyword-only (#948) and threaded into each cascaded
        :meth:`add_favorite`, so cascaded fertilizer favourites obey the same
        tenant predicate as an explicit favourite.
        """
        fertilizer_keys = self._plan_repo.list_edge_fertilizer_keys(nutrient_plan_key)

        created = []
        for fert_key in fertilizer_keys:
            # `_add_one`, not `add_favorite`: fertilizers are not a cascading
            # target today, so this could not recurse anyway — but calling the
            # non-cascading primitive is what makes that true by construction.
            edge = self._add_one(
                user_key,
                fert_key,
                tenant_key=tenant_key,
                source="cascade",
                cascade_from_key=nutrient_plan_key,
            )
            created.append(edge)
        return created

    def _cleanup_cascade(self, user_key: str, nutrient_plan_key: str) -> int:
        """Remove cascade-only fertilizer favorites originating from a specific plan."""
        return self._repo.remove_cascade_edges(f"{col.USERS}/{user_key}", nutrient_plan_key)

    def _resolve_collection(self, key: str, *, tenant_key: str | None) -> str | None:
        """Resolve which catalogue holds a key **that the caller may see**.

        The tenant predicate lives *here*, in the resolution, rather than in a
        second check downstream (#1538). Before, this asked
        ``collection(name).has(key)`` — a question about the collection, not
        about the caller — so a foreign tenant's row resolved and was refused one
        step later. Two code paths with equal output are not one path: anything
        that later distinguishes them (a log line, an added detail field) reopens
        the cross-tenant existence oracle SEC-002 closed in the *message* only. A
        row the caller may not see now resolves to nothing, so "foreign" and
        "unknown" are the same answer by construction.

        **This does not make the two arms indistinguishable in *time*, and the
        same change that collapses the code paths introduces the difference**
        (review finding SCR-007): an existing foreign species costs the transfer
        of a full document plus the grant probe, while an unknown key costs six
        empty gets. Measured in round-trips that is noise, and no attempt is made
        to equalise it — said here so the next reader measures rather than trusts
        a comment that claimed the difference away.

        Visibility is the hybrid-catalogue union — own ∪ global ∪ granted — the
        same three arms
        :func:`~app.data_access.arango.tenant_scope.tenant_union_with_grants_predicate`
        builds for list reads and :meth:`SpeciesService.get_species` asks for a
        single row. **Global rows must stay favouritable**: an ownership-only
        filter would blank the seeded catalogue, which is the #324 regression.
        A missing ``tenant_key`` field and a null one both mean global, exactly
        as the AQL union's ``== "" OR == null`` arms do.

        ``tenant_key`` is keyword-only and has no default (#948): a caller must
        decide, and ``None`` is that decision spelled out — *no predicate*, the
        system context. :meth:`remove_favorite` passes it deliberately; see its
        docstring for why removal stays permissive.

        A foreign hit does not end the walk. Keys are unique per collection, not
        across them, so a visible row further down the list must still resolve —
        otherwise a shadowing foreign row would make it unfavouritable, which is
        over-strictness by control flow instead of by predicate.

        A key containing ``/`` is refused up front (review finding SCR-005). It
        is not a document key but a document *handle*, and python-arango accepts
        one whose prefix happens to match the collection it is asked
        (``_prep_from_doc`` -> ``_validate_id``, `arango/collection.py`): measured
        against a live ArangoDB, ``collection("species").get("species/tomato")``
        returns the real row, ``_add_one`` then builds
        ``_to = "species/species/tomato"``, and the edge insert fails with
        ``[HTTP 400][ERR 1233] expecting both `_from` and `_to` … to have the
        format <collectionName>/<vertexKey>`` — a 500 for what is a malformed
        client input. Pre-existing (``has()`` behaved the same way), refused here
        because this is the one place both verbs pass through.

        Datastore errors are no longer swallowed. Only an absent catalogue (a
        deployment defect, logged by
        :meth:`IFavoritesRepository.get_catalogue_row`) means "not this
        collection"; a connection
        loss, an auth failure or a server error propagates and becomes a 5xx,
        because a 404 that means "the database is down" is a lie to the client.
        """
        if "/" in key:
            return None

        for collection_name in _FAVOURITABLE_COLLECTIONS:
            doc = self._repo.get_catalogue_row(collection_name, key)
            if doc is None:
                continue
            if self._is_visible(collection_name, doc, key, tenant_key):
                return collection_name
        return None

    def _is_visible(
        self,
        collection_name: str,
        doc: dict,
        key: str,
        tenant_key: str | None,
    ) -> bool:
        """Own ∪ global ∪ granted — the hybrid-catalogue read predicate, by key.

        The sibling of
        :func:`~app.data_access.arango.tenant_ownership.verify_entity_ownership`,
        not a copy of it: that one guards a *known* collection on a write path and
        **raises**, while resolution has to answer "not here" and keep walking,
        and it has to admit a grant (#1092), which the ownership guard's
        collections cannot carry. Same two ownership arms, different contract.

        An empty ``tenant_key`` (anonymous / light-mode / no personal tenant)
        collapses the predicate to global-only, exactly as
        :meth:`SpeciesService.get_species` does: there is no tenant to own a row
        and no tenant to hold a grant.
        """
        if tenant_key is None or collection_name not in _TENANT_OWNED_CATALOG_COLLECTIONS:
            return True
        row_tenant = doc.get("tenant_key") or ""
        if row_tenant in ("", tenant_key):
            return True
        return (
            bool(tenant_key)
            and collection_name in _GRANTABLE_COLLECTIONS
            and self._is_granted(collection_name, key, tenant_key)
        )

    def _is_granted(self, collection_name: str, key: str, tenant_key: str) -> bool:
        """Does an explicit ``tenant_has_access`` grant admit this tenant (#1092)?

        The by-key twin of the grant arm in
        :func:`~app.data_access.arango.tenant_scope.tenant_union_with_grants_predicate`,
        asked the same way
        :meth:`ArangoSpeciesRepository.is_granted_to` asks it. Consulted only
        after ownership and global have both failed, so the common favourite
        costs no extra query.
        """
        return self._repo.is_granted(collection_name, key, tenant_key)
