from datetime import UTC, datetime

from arango.database import StandardDatabase
from arango.exceptions import DocumentInsertError

from app.common.exceptions import NotFoundError
from app.data_access.arango import collections as col

# Catalogue collections whose rows carry a ``tenant_key`` ownership marker: some
# rows are global (``tenant_key == ""``, e.g. seeded system catalogues), others
# are owned by a single tenant. Favouriting one of these must respect tenant
# isolation (#965 item 2). ``species`` and ``botanical_families`` carry no
# ``tenant_key`` and are purely global, so they are intentionally absent here.
#
# ``activities`` is included beyond the two catalogues named in the #965 report:
# ``Activity.tenant_key`` (app/domain/models/activity.py) is a real ownership
# marker (system rows carry ``is_system == true``, tenant rows an owning
# ``tenant_key``), so the same cross-tenant leak applied to it and is closed the
# same way.
_TENANT_OWNED_CATALOG_COLLECTIONS = frozenset(
    {
        col.NUTRIENT_PLANS,
        col.FERTILIZERS,
        col.ACTIVITIES,
    }
)


class FavoritesService:
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def add_favorite(
        self,
        user_key: str,
        target_key: str,
        *,
        tenant_key: str,
        source: str = "manual",
        cascade_from_key: str | None = None,
    ) -> dict:
        """Add a favorite edge from user to target entity. Upserts — upgrades cascade→manual.

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
        (:data:`_TENANT_OWNED_CATALOG_COLLECTIONS`). Purely global targets
        (species, botanical families) carry no ``tenant_key`` and are unaffected.
        A foreign-tenant target raises :class:`NotFoundError` (404) — matching
        ``verify_tenant_read_access`` — to avoid a cross-tenant existence oracle.
        """
        target_collection = self._resolve_collection(target_key)
        if not target_collection:
            raise ValueError(f"Cannot resolve collection for key: {target_key}")

        self._verify_target_tenant_access(
            target_collection=target_collection,
            target_key=target_key,
            tenant_key=tenant_key,
        )

        from_id = f"{col.USERS}/{user_key}"
        to_id = f"{target_collection}/{target_key}"

        # Check if edge already exists
        cursor = self._db.aql.execute(
            """
            FOR e IN user_favorites
                FILTER e._from == @from_id AND e._to == @to_id
                RETURN e
            """,
            bind_vars={"from_id": from_id, "to_id": to_id},
        )
        existing = list(cursor)

        if existing:
            edge = existing[0]
            # Upgrade cascade→manual if user explicitly favorites
            if source == "manual" and edge.get("source") == "cascade":
                self._db.collection(col.USER_FAVORITES).update(
                    {"_key": edge["_key"], "source": "manual", "cascade_from_key": None}
                )
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
        try:
            result = self._db.collection(col.USER_FAVORITES).insert(edge_data, return_new=True)
            return result.get("new", edge_data)
        except DocumentInsertError as exc:
            if exc.http_code == 409:
                # Concurrent insert race — edge was created between check and insert
                cursor = self._db.aql.execute(
                    "FOR e IN user_favorites FILTER e._from == @f AND e._to == @t RETURN e",
                    bind_vars={"f": from_id, "t": to_id},
                )
                rows = list(cursor)
                if rows:
                    return rows[0]
            raise

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
        """
        target_collection = self._resolve_collection(target_key)
        if not target_collection:
            return False

        from_id = f"{col.USERS}/{user_key}"
        to_id = f"{target_collection}/{target_key}"

        # If removing a nutrient plan, clean up cascaded fertilizer favorites
        if cascade_cleanup and target_collection == col.NUTRIENT_PLANS:
            self._cleanup_cascade(user_key, target_key)

        cursor = self._db.aql.execute(
            """
            FOR e IN user_favorites
                FILTER e._from == @from_id AND e._to == @to_id
                REMOVE e IN user_favorites
                RETURN OLD
            """,
            bind_vars={"from_id": from_id, "to_id": to_id},
        )
        return len(list(cursor)) > 0

    def list_favorites(
        self,
        user_key: str,
        entity_type: str | None = None,
    ) -> list[dict]:
        """List all favorites for a user, optionally filtered by entity type."""
        from_id = f"{col.USERS}/{user_key}"

        if entity_type:
            cursor = self._db.aql.execute(
                """
                FOR e IN user_favorites
                    FILTER e._from == @from_id AND e.target_type == @entity_type
                    RETURN e
                """,
                bind_vars={"from_id": from_id, "entity_type": entity_type},
            )
        else:
            cursor = self._db.aql.execute(
                """
                FOR e IN user_favorites
                    FILTER e._from == @from_id
                    RETURN e
                """,
                bind_vars={"from_id": from_id},
            )
        return list(cursor)

    def get_matching_nutrient_plans(
        self,
        species_keys: list[str],
        tenant_key: str | None = None,
    ) -> list[dict]:
        """Find template nutrient plans matching the given species."""
        if not species_keys:
            return []

        # Find plans that reference any of the given species via phase entries.
        # Collect fertilizer keys from both graph edges AND embedded
        # delivery_channels[].fertilizer_dosages[] to handle plans where
        # edges may not be fully materialised (e.g. seed data).
        cursor = self._db.aql.execute(
            """
            FOR plan IN nutrient_plans
                FILTER plan.is_template == true OR plan.origin == "system"
                LET phase_entries = (
                    FOR pe IN nutrient_plan_phase_entries
                        FILTER pe.plan_key == plan._key
                        RETURN pe
                )
                LET edge_fert_keys = (
                    FOR pe IN phase_entries
                        FOR edge IN plan_uses_fertilizer
                            FILTER edge._from == CONCAT("nutrient_plan_phase_entries/", pe._key)
                            RETURN PARSE_IDENTIFIER(edge._to).key
                )
                LET embedded_fert_keys = (
                    FOR pe IN phase_entries
                        FOR ch IN (pe.delivery_channels || [])
                            FOR fd IN (ch.fertilizer_dosages || [])
                                RETURN fd.fertilizer_key
                )
                LET fertilizer_keys = UNIQUE(APPEND(edge_fert_keys, embedded_fert_keys))
                LET fertilizers = (
                    FOR fk IN fertilizer_keys
                        FOR f IN fertilizers
                            FILTER f._key == fk
                            RETURN { key: f._key, product_name: f.product_name, brand: f.brand }
                )
                RETURN {
                    plan_key: plan._key,
                    name: plan.name,
                    description: plan.description,
                    substrate_type: plan.substrate_type,
                    fertilizer_count: LENGTH(fertilizer_keys),
                    fertilizers: fertilizers
                }
            """,
        )
        return list(cursor)

    def cascade_fertilizers(self, user_key: str, nutrient_plan_key: str, *, tenant_key: str) -> list[dict]:
        """Traverse plan → entries → fertilizers and create cascade favorite edges.

        ``tenant_key`` is keyword-only (#948) and threaded into each cascaded
        :meth:`add_favorite`, so cascaded fertilizer favourites obey the same
        tenant predicate as an explicit favourite.
        """
        cursor = self._db.aql.execute(
            """
            FOR pe IN nutrient_plan_phase_entries
                FILTER pe.plan_key == @plan_key
                FOR edge IN plan_uses_fertilizer
                    FILTER edge._from == CONCAT("nutrient_plan_phase_entries/", pe._key)
                    LET fert_key = PARSE_IDENTIFIER(edge._to).key
                    RETURN DISTINCT fert_key
            """,
            bind_vars={"plan_key": nutrient_plan_key},
        )
        fertilizer_keys = list(cursor)

        created = []
        for fert_key in fertilizer_keys:
            edge = self.add_favorite(
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
        from_id = f"{col.USERS}/{user_key}"
        cursor = self._db.aql.execute(
            """
            FOR e IN user_favorites
                FILTER e._from == @from_id
                    AND e.source == "cascade"
                    AND e.cascade_from_key == @plan_key
                REMOVE e IN user_favorites
                RETURN OLD
            """,
            bind_vars={"from_id": from_id, "plan_key": nutrient_plan_key},
        )
        return len(list(cursor))

    def _verify_target_tenant_access(
        self,
        *,
        target_collection: str,
        target_key: str,
        tenant_key: str,
    ) -> None:
        """Enforce the personal-favourite tenant predicate for tenant-owned catalogues.

        Allows a **global** row (``tenant_key == ""``) or one owned by the
        caller's **active** tenant; refuses a **foreign** tenant's row with
        :class:`NotFoundError` (404, not 403) so cross-tenant existence cannot be
        probed — mirroring ``app/common/tenant_guard.py:verify_tenant_read_access``.
        Purely global catalogues (species, botanical families) carry no
        ``tenant_key`` and are skipped entirely, so this never hides them (#324).
        """
        if target_collection not in _TENANT_OWNED_CATALOG_COLLECTIONS:
            return

        doc = self._db.collection(target_collection).get(target_key)
        if doc is None:
            raise NotFoundError(target_collection, target_key)

        row_tenant = doc.get("tenant_key") or ""
        if row_tenant not in ("", tenant_key):
            raise NotFoundError(target_collection, target_key)

    def _resolve_collection(self, key: str) -> str | None:
        """Resolve which document collection a key belongs to."""
        for collection_name in [
            col.SPECIES,
            col.NUTRIENT_PLANS,
            col.FERTILIZERS,
            col.ACTIVITIES,
            col.BOTANICAL_FAMILIES,
        ]:
            try:
                if self._db.collection(collection_name).has(key):
                    return collection_name
            except Exception:
                continue
        return None
