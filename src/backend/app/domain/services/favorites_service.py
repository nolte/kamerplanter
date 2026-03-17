from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.data_access.arango import collections as col


class FavoritesService:
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    def add_favorite(
        self,
        user_key: str,
        target_key: str,
        source: str = "manual",
        cascade_from_key: str | None = None,
    ) -> dict:
        """Add a favorite edge from user to target entity. Upserts — upgrades cascade→manual."""
        target_collection = self._resolve_collection(target_key)
        if not target_collection:
            raise ValueError(f"Cannot resolve collection for key: {target_key}")

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
        result = self._db.collection(col.USER_FAVORITES).insert(edge_data, return_new=True)
        return result.get("new", edge_data)

    def remove_favorite(
        self,
        user_key: str,
        target_key: str,
        cascade_cleanup: bool = True,
    ) -> bool:
        """Remove a favorite edge. Optionally clean up cascade edges."""
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

    def cascade_fertilizers(self, user_key: str, nutrient_plan_key: str) -> list[dict]:
        """Traverse plan → entries → fertilizers and create cascade favorite edges."""
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
            edge = self.add_favorite(user_key, fert_key, source="cascade", cascade_from_key=nutrient_plan_key)
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

    def _resolve_collection(self, key: str) -> str | None:
        """Resolve which document collection a key belongs to."""
        for collection_name in [col.SPECIES, col.NUTRIENT_PLANS, col.FERTILIZERS]:
            try:
                if self._db.collection(collection_name).has(key):
                    return collection_name
            except Exception:
                continue
        return None
