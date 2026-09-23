from datetime import UTC, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.exceptions import NotFoundError
from app.common.types import FertilizerKey, NutrientPlanKey, NutrientPlanPhaseEntryKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.tenant_scope import tenant_union_predicate
from app.domain.interfaces.nutrient_plan_repository import INutrientPlanRepository
from app.domain.models.nutrient_plan import NutrientPlan, NutrientPlanPhaseEntry


class ArangoNutrientPlanRepository(BaseArangoRepository[NutrientPlan], INutrientPlanRepository):
    is_tenant_scoped = True
    _model_cls = NutrientPlan

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.NUTRIENT_PLANS)
        self._phase_entries = BaseArangoRepository[NutrientPlanPhaseEntry](
            db, col.NUTRIENT_PLAN_PHASE_ENTRIES, NutrientPlanPhaseEntry
        )

    # ── Plan CRUD ────────────────────────────────────────────────────

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        tenant_key: str | None = None,
        *,
        all_tenants: bool = False,
    ) -> tuple[list[NutrientPlan], int]:
        # Nutrient plans are a hybrid catalog: globally seeded system plans
        # (empty tenant_key) PLUS per-tenant custom plans.  When a tenant_key is
        # supplied the query below unions the tenant's own rows with the global
        # rows; a missing tenant_key must therefore be an explicit system-context
        # opt-in (all_tenants=True) rather than a silent all-tenant read (SEC-B4).
        self._enforce_tenant_scope(tenant_key, all_tenants)
        query = f"FOR doc IN {col.NUTRIENT_PLANS}"
        bind_vars: dict[str, Any] = {}
        filter_clauses = []
        if tenant_key:
            # Hybrid catalog: union the tenant's own rows with the global rows
            # (shared helper, SEC-B4 / #324) — see tenant_scope.tenant_union_predicate.
            predicate, predicate_vars = tenant_union_predicate(tenant_key)
            bind_vars.update(predicate_vars)
            filter_clauses.append(predicate)
        if filters:
            for i, (field, value) in enumerate(filters.items()):
                bind_vars[f"val{i}"] = value
                filter_clauses.append(f"doc.{field} == @val{i}")
        if filter_clauses:
            query += " FILTER " + " AND ".join(filter_clauses)
        count_query = query + " COLLECT WITH COUNT INTO total RETURN total"
        count_vars = dict(bind_vars)
        bind_vars["offset"] = offset
        bind_vars["limit"] = limit
        query += " SORT doc.name LIMIT @offset, @limit RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [NutrientPlan(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
        total = next(count_cursor, 0)
        return items, total

    def get_readable_or_raise(self, key: NutrientPlanKey, *, tenant_key: str) -> NutrientPlan:
        """The one hybrid-catalog read-access predicate for a single plan (#950).

        A plan is readable from ``tenant_key`` when it is that tenant's own plan
        **or** a globally seeded system plan (empty ``tenant_key`` — there is no
        ``is_system`` flag, the empty tenant IS the global marker). Anything else
        raises :class:`NotFoundError` → HTTP 404, never 403: a 403 would confirm
        that the plan exists in someone else's tenant.

        This lives in the repository rather than in each caller because #950 is
        exactly what happens when it does not. ``NutrientPlanService.get_plan``
        made its tenant argument optional, ``assign_to_plant`` omitted it, and the
        check silently turned itself off — a member of tenant A could bind their
        own plant to tenant B's plan and then read the plan back through the
        plant-anchored predicate, which is satisfied because the *plant* is theirs.
        With the parameter required and keyword-only, an assignment that does not
        name a tenant cannot be written at all.

        The predicate is deliberately **read** access, not ownership. A strict
        ``plan.tenant_key == @tenant_key`` here would refuse every globally seeded
        system plan — the #324 regression class, which traded a leak for a
        catalogue that disappeared. Writes to the plan itself stay owner-only via
        :func:`~app.common.tenant_guard.verify_tenant_ownership`.
        """
        self._require_tenant_key(tenant_key, "get_readable_or_raise")
        plan = self.get_or_raise(key)
        if plan.tenant_key not in ("", tenant_key):
            raise NotFoundError("NutrientPlan", key)
        return plan

    def delete(self, key: NutrientPlanKey) -> bool:
        plan_id = f"{col.NUTRIENT_PLANS}/{key}"
        # Delete phase entries and their edges
        entries = self.get_phase_entries(key)
        for entry in entries:
            if entry.key:
                self.delete_phase_entry(entry.key)
        # Delete outbound edges
        for edge_col in [col.HAS_PHASE_ENTRY, col.CLONED_FROM]:
            self.delete_edges(edge_col, plan_id)
        # Delete inbound edges
        for edge_col in [col.FOLLOWS_PLAN, col.CLONED_FROM]:
            self.delete_edges(edge_col, plan_id, direction="inbound")
        return super().delete(key)

    # ── Phase entries ────────────────────────────────────────────────

    def create_phase_entry(self, entry: NutrientPlanPhaseEntry) -> NutrientPlanPhaseEntry:
        created = self._phase_entries.create(entry)
        # Create edge
        from_id = f"{col.NUTRIENT_PLANS}/{entry.plan_key}"
        to_id = f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/{created.key}"
        self.create_edge(col.HAS_PHASE_ENTRY, from_id, to_id)
        return created

    def get_phase_entries(self, plan_key: NutrientPlanKey) -> list[NutrientPlanPhaseEntry]:
        return self._phase_entries.find_by_field("plan_key", plan_key, sort="sequence_order")

    def get_phase_entry_by_key(self, key: NutrientPlanPhaseEntryKey) -> NutrientPlanPhaseEntry | None:
        return self._phase_entries.get_by_key(key)

    def get_phase_entry_or_raise(self, key: NutrientPlanPhaseEntryKey) -> NutrientPlanPhaseEntry:
        return self._phase_entries.get_or_raise(key)

    def update_phase_entry(
        self,
        key: NutrientPlanPhaseEntryKey,
        entry: NutrientPlanPhaseEntry,
    ) -> NutrientPlanPhaseEntry:
        return self._phase_entries.update(key, entry)

    def delete_phase_entry(self, key: NutrientPlanPhaseEntryKey) -> bool:
        entry_id = f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/{key}"
        # Delete fertilizer edges
        self.delete_edges(col.PLAN_USES_FERTILIZER, entry_id)
        # Delete parent edge
        self.delete_edges(col.HAS_PHASE_ENTRY, entry_id, direction="inbound")
        return self._phase_entries.delete(key)

    # ── Plant assignment ─────────────────────────────────────────────

    def assign_to_plant(self, plant_key: str, plan_key: NutrientPlanKey, assigned_by: str = "") -> dict:
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        plan_id = f"{col.NUTRIENT_PLANS}/{plan_key}"
        # Remove existing assignment
        self.delete_edges(col.FOLLOWS_PLAN, plant_id)
        # Create new
        edge_data = {"assigned_by": assigned_by, "assigned_at": datetime.now(UTC).isoformat()}
        return self.create_edge(col.FOLLOWS_PLAN, plant_id, plan_id, edge_data)

    def get_plant_plan(self, plant_key: str, *, tenant_key: str) -> NutrientPlan | None:
        """The plan assigned to a plant, readable only from the plant's tenant (#927).

        **The predicate sits on the plant, not on the plan.** Nutrient plans are a
        hybrid catalog: globally seeded system plans carry ``tenant_key == ""``
        and are legitimately assigned to plants of every tenant (PR #324). A
        strict ``plan.tenant_key == @tenant_key`` here would answer ``None`` for
        every plant on a system plan — the #324 regression class, traded for the
        leak instead of a fix.

        What must therefore not cross tenants is the *assignment* — and until
        #950 nothing enforced that. This docstring used to assert it as if it
        held: ``NutrientPlanService.assign_to_plant`` called ``get_plan`` with the
        default empty ``tenant_key``, which skips the access check entirely, so a
        member of tenant A could bind their own plant to tenant B's plan and then
        read it back right here — the plant *is* theirs, so the predicate below is
        satisfied. The guarantee now exists where it can be relied on:
        :meth:`get_readable_or_raise` is required and keyword-only on every
        assignment path. This query stays plant-anchored on purpose and depends on
        that guard for the plan side; it does not provide it.

        Listed in #927 under "one line away": every current caller resolves the
        plant against the tenant first. The filter moves that obligation into the
        query so the next caller cannot forget it.
        """
        self._require_tenant_key(tenant_key, "get_plant_plan")
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        query = f"""
        FOR e IN {col.FOLLOWS_PLAN}
          FILTER e._from == @pid
          LET plant = DOCUMENT(e._from)
          FILTER plant != null AND plant.tenant_key == @tenant_key
          LET plan = DOCUMENT(e._to)
          RETURN plan
        """
        cursor = self._db.aql.execute(query, bind_vars={"pid": plant_id, "tenant_key": tenant_key})
        docs = list(cursor)
        if not docs or docs[0] is None:
            return None
        return NutrientPlan(**self._from_doc(docs[0]))

    def remove_plant_plan(self, plant_key: str) -> bool:
        plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
        self.delete_edges(col.FOLLOWS_PLAN, plant_id)
        return True

    # ── Onboarding / favourites reads (#1638) ───────────────────────

    def list_template_plan_summaries(self, *, tenant_key: str) -> list[dict]:
        """Template plans visible to ``tenant_key``, with their fertilizers (#1561).

        Moved verbatim from ``FavoritesService.get_matching_nutrient_plans``
        (#1638). The predicate is the hybrid-catalogue union
        :func:`~app.data_access.arango.tenant_scope.tenant_union_predicate`
        builds — own ∪ global — the **same** one :meth:`get_all` applies, so the
        two reads of ``nutrient_plans`` answer one visibility question. A strict
        ``tenant_key == @tenant_key`` filter would hide the seeded catalogue and
        empty the onboarding step (#324). Deliberately not the ``…_with_grants``
        variant: ``tenant_has_access`` is declared only ``tenants -> species |
        cultivars``, so a plan cannot carry a grant.

        This is where a species filter lands once the data model carries a
        species↔plan relation (#1618).
        """
        predicate, bind_vars = tenant_union_predicate(tenant_key, doc_var="plan")

        # The body below is a plain string spliced once through `.replace`, not an
        # f-string: it holds AQL object literals (`{ plan_key: ... }`) whose braces
        # an f-string would read as fields. Only the *predicate* is spliced; the
        # tenant itself travels as a bind var and never enters the query text.
        #
        # Collect fertilizer keys from both graph edges AND embedded
        # delivery_channels[].fertilizer_dosages[] to handle plans where
        # edges may not be fully materialised (e.g. seed data).
        cursor = self._db.aql.execute(
            """
            FOR plan IN nutrient_plans
                FILTER (plan.is_template == true OR plan.origin == "system")
                    AND __TENANT_PREDICATE__
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
            """.replace("__TENANT_PREDICATE__", predicate),
            bind_vars=bind_vars,
        )
        return list(cursor)

    def list_edge_fertilizer_keys(self, plan_key: NutrientPlanKey) -> list[str]:
        """Plan → phase entries → ``plan_uses_fertilizer`` → distinct fertilizer keys."""
        cursor = self._db.aql.execute(
            """
            FOR pe IN nutrient_plan_phase_entries
                FILTER pe.plan_key == @plan_key
                FOR edge IN plan_uses_fertilizer
                    FILTER edge._from == CONCAT("nutrient_plan_phase_entries/", pe._key)
                    LET fert_key = PARSE_IDENTIFIER(edge._to).key
                    RETURN DISTINCT fert_key
            """,
            bind_vars={"plan_key": plan_key},
        )
        return list(cursor)

    # ── Channel fertilizer edges ────────────────────────────────────

    def add_fertilizer_to_channel(
        self,
        entry_key: NutrientPlanPhaseEntryKey,
        channel_id: str,
        fertilizer_key: FertilizerKey,
        ml_per_liter: float,
        optional: bool = False,
    ) -> dict:
        from_id = f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/{entry_key}"
        to_id = f"{col.FERTILIZERS}/{fertilizer_key}"
        edge_data = {
            "ml_per_liter": ml_per_liter,
            "optional": optional,
            "channel_id": channel_id,
        }
        edge = self.create_edge(col.PLAN_USES_FERTILIZER, from_id, to_id, edge_data)

        # Update embedded delivery_channels[].fertilizer_dosages[]
        dosage = {
            "fertilizer_key": fertilizer_key,
            "ml_per_liter": ml_per_liter,
            "optional": optional,
        }
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
          UPDATE doc WITH {
            delivery_channels: (
              FOR ch IN (doc.delivery_channels || [])
                RETURN ch.channel_id == @cid
                  ? MERGE(ch, {fertilizer_dosages: APPEND(ch.fertilizer_dosages || [], [@dosage])})
                  : ch
            ),
            updated_at: @now
          } IN @@collection
        """
        self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.NUTRIENT_PLAN_PHASE_ENTRIES,
                "key": entry_key,
                "cid": channel_id,
                "dosage": dosage,
                "now": datetime.now(UTC).isoformat(),
            },
        )
        return edge

    def remove_fertilizer_from_channel(
        self,
        entry_key: NutrientPlanPhaseEntryKey,
        channel_id: str,
        fertilizer_key: FertilizerKey,
    ) -> bool:
        # Delete edge filtered by channel_id
        from_id = f"{col.NUTRIENT_PLAN_PHASE_ENTRIES}/{entry_key}"
        to_id = f"{col.FERTILIZERS}/{fertilizer_key}"
        query = f"""
        FOR e IN {col.PLAN_USES_FERTILIZER}
          FILTER e._from == @from_id AND e._to == @to_id AND e.channel_id == @cid
          REMOVE e IN {col.PLAN_USES_FERTILIZER}
        """
        self._db.aql.execute(
            query,
            bind_vars={
                "from_id": from_id,
                "to_id": to_id,
                "cid": channel_id,
            },
        )

        # Update embedded delivery_channels[].fertilizer_dosages[]
        query = """
        FOR doc IN @@collection
          FILTER doc._key == @key
          UPDATE doc WITH {
            delivery_channels: (
              FOR ch IN (doc.delivery_channels || [])
                RETURN ch.channel_id == @cid
                  ? MERGE(ch, {
                      fertilizer_dosages: (
                        FOR d IN (ch.fertilizer_dosages || [])
                          FILTER d.fertilizer_key != @fk
                          RETURN d
                      )
                    })
                  : ch
            ),
            updated_at: @now
          } IN @@collection
        """
        self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.NUTRIENT_PLAN_PHASE_ENTRIES,
                "key": entry_key,
                "cid": channel_id,
                "fk": fertilizer_key,
                "now": datetime.now(UTC).isoformat(),
            },
        )
        return True

    # ── Clone ────────────────────────────────────────────────────────

    def clone(self, source_key: NutrientPlanKey, new_name: str, author: str = "", tenant_key: str = "") -> NutrientPlan:
        source = self.get_by_key(source_key)
        if source is None:
            raise ValueError(f"Source plan '{source_key}' not found")

        # Create new plan owned by the cloning tenant (never the source's tenant).
        new_plan = NutrientPlan(
            name=new_name,
            tenant_key=tenant_key,
            description=source.description,
            recommended_substrate_type=source.recommended_substrate_type,
            author=author,
            is_template=False,
            version="1.0",
            tags=list(source.tags),
            cloned_from_key=source_key,
        )
        created_plan = self.create(new_plan)

        # Create CLONED_FROM edge
        from_id = f"{col.NUTRIENT_PLANS}/{created_plan.key}"
        to_id = f"{col.NUTRIENT_PLANS}/{source_key}"
        self.create_edge(col.CLONED_FROM, from_id, to_id)

        # Clone phase entries
        entries = self.get_phase_entries(source_key)
        for entry in entries:
            new_entry = NutrientPlanPhaseEntry(
                plan_key=created_plan.key or "",
                phase_name=entry.phase_name,
                sequence_order=entry.sequence_order,
                week_start=entry.week_start,
                week_end=entry.week_end,
                npk_ratio=entry.npk_ratio,
                calcium_ppm=entry.calcium_ppm,
                magnesium_ppm=entry.magnesium_ppm,
                notes=entry.notes,
                delivery_channels=[ch.model_copy(deep=True) for ch in entry.delivery_channels],
            )
            self.create_phase_entry(new_entry)

        return created_plan
