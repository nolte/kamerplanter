from datetime import UTC, date, datetime

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.watering_log_repository import IWateringLogRepository
from app.domain.models.watering_log import WateringLog


class ArangoWateringLogRepository(BaseArangoRepository[WateringLog], IWateringLogRepository):
    is_tenant_scoped = True
    _model_cls = WateringLog

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.WATERING_LOGS)

    # ── Mapping helper ──────────────────────────────────────────────────

    def _to_model(self, doc: dict) -> WateringLog:
        return WateringLog(**self._from_doc(doc))

    # ── Create ──────────────────────────────────────────────────────────

    def create(self, log: WateringLog) -> WateringLog:
        created = super().create(log, default_now_fields=("logged_at",))

        log_id = f"{col.WATERING_LOGS}/{created.key}"

        # Create LOG_SLOT edges (WateringLog -> Slot)
        for slot_key in log.slot_keys:
            slot_id = f"{col.SLOTS}/{slot_key}"
            self.create_edge(col.LOG_SLOT, log_id, slot_id)

        # Create LOG_PLANT edges (WateringLog -> PlantInstance)
        for plant_key in log.plant_keys:
            plant_id = f"{col.PLANT_INSTANCES}/{plant_key}"
            self.create_edge(col.LOG_PLANT, log_id, plant_id)

        # Create LOG_FERTILIZER edges (WateringLog -> Fertilizer)
        for fert in log.fertilizers_used:
            fert_id = f"{col.FERTILIZERS}/{fert.fertilizer_key}"
            self.create_edge(
                col.LOG_FERTILIZER,
                log_id,
                fert_id,
                {"ml_per_liter": fert.ml_per_liter},
            )

        return created

    def resolve_plant_names(self, plant_keys: list[str]) -> dict[str, str]:
        """Batch-resolve plant keys to display names."""
        if not plant_keys:
            return {}
        query = """
        FOR pk IN @plant_keys
          LET pi = DOCUMENT(CONCAT(@col, "/", pk))
          FILTER pi != null
          RETURN { key: pk, name: pi.plant_name || pi.instance_id || pk }
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "plant_keys": plant_keys,
                "col": col.PLANT_INSTANCES,
            },
        )
        return {r["key"]: r["name"] for r in cursor}

    def resolve_fertilizer_names(self, fert_keys: list[str]) -> dict[str, str]:
        """Batch-resolve fertilizer keys to display names."""
        if not fert_keys:
            return {}
        query = """
        FOR fk IN @fert_keys
          LET f = DOCUMENT(CONCAT(@col, "/", fk))
          FILTER f != null
          RETURN { key: fk, name: CONCAT(f.product_name, " (", f.brand, ")") }
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "fert_keys": fert_keys,
                "col": col.FERTILIZERS,
            },
        )
        return {r["key"]: r["name"] for r in cursor}

    # ── Update ──────────────────────────────────────────────────────────

    def update_fields(self, key: str, fields: dict) -> WateringLog:
        fields["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.WATERING_LOGS).update(
            {"_key": key, **fields},
            return_new=True,
        )
        return WateringLog(**self._from_doc(result["new"]))

    # ── Delete ──────────────────────────────────────────────────────────

    def delete(self, key: str) -> bool:
        log_id = f"{col.WATERING_LOGS}/{key}"
        # Delete outbound edges
        self.delete_edges(col.LOG_SLOT, log_id)
        self.delete_edges(col.LOG_PLANT, log_id)
        self.delete_edges(col.LOG_FERTILIZER, log_id)
        return super().delete(key)

    # ── Queries ─────────────────────────────────────────────────────────

    def get_by_slot(
        self,
        slot_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[WateringLog]:
        """A slot's watering logs **inside one tenant** (#927).

        Issue #927 lists this under "one line away — current callers do check".
        They do not: ``GET /t/{slug}/slots/{slot_key}/watering-logs`` passes the
        URL key straight through without resolving the slot against the caller's
        tenant, so this was exploitable exactly like the five named endpoints.
        The tenant predicate is therefore applied here, keyword-only and required,
        rather than as a caller-side check.
        """
        self._require_tenant_key(tenant_key, "get_by_slot")
        query = """
        FOR e IN @@edge_col
          FILTER e._to == @slot_id
          LET doc = DOCUMENT(e._from)
          FILTER doc != null AND doc.tenant_key == @tenant_key
          SORT doc.logged_at DESC
          LIMIT @offset, @limit
          RETURN doc
        """
        slot_id = f"{col.SLOTS}/{slot_key}"
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@edge_col": col.LOG_SLOT,
                "slot_id": slot_id,
                "tenant_key": tenant_key,
                "offset": offset,
                "limit": limit,
            },
        )
        return [self._to_model(doc) for doc in cursor]

    def get_by_location(
        self,
        location_key: str,
        offset: int = 0,
        limit: int = 50,
        *,
        tenant_key: str,
    ) -> list[WateringLog]:
        """A location's watering logs **inside one tenant** (#927).

        Same correction as :meth:`get_by_slot`:
        ``GET /t/{slug}/locations/{location_key}/watering-logs`` forwarded the URL
        key unverified, so this too was live rather than merely latent.
        """
        self._require_tenant_key(tenant_key, "get_by_location")
        query = """
        FOR slot_edge IN @@has_slot
          FILTER slot_edge._from == @location_id
          FOR log_edge IN @@log_slot
            FILTER log_edge._to == slot_edge._to
            LET doc = DOCUMENT(log_edge._from)
            FILTER doc != null AND doc.tenant_key == @tenant_key
            SORT doc.logged_at DESC
            LIMIT @offset, @limit
            RETURN DISTINCT doc
        """
        location_id = f"{col.LOCATIONS}/{location_key}"
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@has_slot": col.HAS_SLOT,
                "@log_slot": col.LOG_SLOT,
                "location_id": location_id,
                "tenant_key": tenant_key,
                "offset": offset,
                "limit": limit,
            },
        )
        return [self._to_model(doc) for doc in cursor]

    def get_stats_by_location(self, location_key: str, *, tenant_key: str) -> dict:
        """A location's watering-log statistics, **inside one tenant** (#927).

        The aggregate is nothing but counts and sums, so leaving it unfiltered
        would disclose exactly the numbers the list query no longer returns.
        """
        self._require_tenant_key(tenant_key, "get_stats_by_location")
        query = """
        LET logs = (
          FOR slot_edge IN @@has_slot
            FILTER slot_edge._from == @location_id
            FOR log_edge IN @@log_slot
              FILTER log_edge._to == slot_edge._to
              LET doc = DOCUMENT(log_edge._from)
              FILTER doc != null AND doc.tenant_key == @tenant_key
              RETURN DISTINCT doc
        )
        LET by_method = (
          FOR l IN logs
            COLLECT method = l.application_method
            AGGREGATE cnt = COUNT(l), vol = SUM(l.volume_liters)
            RETURN { method, count: cnt, total_volume: vol }
        )
        RETURN {
          total_events: LENGTH(logs),
          total_volume: SUM(logs[*].volume_liters),
          by_method: by_method
        }
        """
        location_id = f"{col.LOCATIONS}/{location_key}"
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@has_slot": col.HAS_SLOT,
                "@log_slot": col.LOG_SLOT,
                "location_id": location_id,
                "tenant_key": tenant_key,
            },
        )
        result = next(cursor, None)
        return result or {"total_events": 0, "total_volume": 0.0, "by_method": []}

    def get_last_watering_date_for_run(self, run_key: str, *, tenant_key: str) -> date | None:
        """Newest watering-log date for a run's slots, **inside one tenant** (#927).

        Structural twin of ``ArangoWateringRepository.get_last_watering_date_for_run``
        and closed for the same reason: the query selects logs by a slot-key
        intersection and named no tenant.
        """
        self._require_tenant_key(tenant_key, "get_last_watering_date_for_run")
        query = """
        LET slot_keys = (
          FOR rc IN @@run_contains
            FILTER rc._from == @run_id
            FILTER rc.detached_at == null
            FOR pi IN @@placed_in
              FILTER pi._from == rc._to
              RETURN PARSE_IDENTIFIER(pi._to).key
        )
        FOR wl IN @@watering_logs
          FILTER wl.tenant_key == @tenant_key
          FILTER LENGTH(INTERSECTION(wl.slot_keys, slot_keys)) > 0
          SORT wl.logged_at DESC
          LIMIT 1
          RETURN wl.logged_at
        """
        run_id = f"{col.PLANTING_RUNS}/{run_key}"
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@run_contains": col.RUN_CONTAINS,
                "@placed_in": col.PLACED_IN,
                "@watering_logs": col.WATERING_LOGS,
                "run_id": run_id,
                "tenant_key": tenant_key,
            },
        )
        result = next(cursor, None)
        if result is None:
            return None
        if isinstance(result, str):
            return datetime.fromisoformat(result).date()
        if isinstance(result, datetime):
            return result.date()
        return None

    # Two static AQL variants keep the tenant filter injection-safe (no f-strings,
    # NFR-006): the tenant-scoped variant is used for every request-context call,
    # the unscoped variant only for an explicit ``all_tenants=True`` system query.
    _BY_PLANT_QUERY = """
    FOR doc IN @@collection
      FILTER @plant_key IN doc.plant_keys
      SORT doc.logged_at DESC
      LIMIT @offset, @limit
      RETURN doc
    """

    _BY_PLANT_TENANT_QUERY = """
    FOR doc IN @@collection
      FILTER @plant_key IN doc.plant_keys
        AND doc.tenant_key == @tenant_key
      SORT doc.logged_at DESC
      LIMIT @offset, @limit
      RETURN doc
    """

    _RECENT_RUNOFF_QUERY = """
    FOR doc IN @@collection
      FILTER @plant_key IN doc.plant_keys
        AND doc.runoff_ec != null
      SORT doc.logged_at DESC
      LIMIT @limit
      RETURN doc
    """

    _RECENT_RUNOFF_TENANT_QUERY = """
    FOR doc IN @@collection
      FILTER @plant_key IN doc.plant_keys
        AND doc.tenant_key == @tenant_key
        AND doc.runoff_ec != null
      SORT doc.logged_at DESC
      LIMIT @limit
      RETURN doc
    """

    def get_by_plant(
        self,
        plant_key: str,
        offset: int = 0,
        limit: int = 50,
        tenant_key: str = "",
        *,
        all_tenants: bool = False,
    ) -> list[WateringLog]:
        """Return a plant's watering logs, tenant-scoped by default (SEC-B4).

        The per-plant Gießprotokoll view must not read another tenant's — nor an
        orphaned empty-tenant — log (#580). ``tenant_key`` therefore filters the
        query and is required in a request context: an unscoped read is only
        allowed for an explicit ``all_tenants=True`` system-context call, mirroring
        :meth:`BaseArangoRepository._list_docs`.
        """
        self._enforce_tenant_scope(tenant_key, all_tenants)
        bind_vars: dict[str, object] = {
            "@collection": col.WATERING_LOGS,
            "plant_key": plant_key,
            "offset": offset,
            "limit": limit,
        }
        if tenant_key:
            bind_vars["tenant_key"] = tenant_key
            query = self._BY_PLANT_TENANT_QUERY
        else:
            query = self._BY_PLANT_QUERY
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._to_model(doc) for doc in cursor]

    def get_latest_by_plant(
        self,
        plant_key: str,
        tenant_key: str = "",
        *,
        all_tenants: bool = False,
    ) -> WateringLog | None:
        results = self.get_by_plant(plant_key, offset=0, limit=1, tenant_key=tenant_key, all_tenants=all_tenants)
        return results[0] if results else None

    def get_recent_runoff_logs(
        self,
        plant_key: str,
        limit: int = 5,
        tenant_key: str = "",
        *,
        all_tenants: bool = False,
    ) -> list[WateringLog]:
        self._enforce_tenant_scope(tenant_key, all_tenants)
        bind_vars: dict[str, object] = {
            "@collection": col.WATERING_LOGS,
            "plant_key": plant_key,
            "limit": limit,
        }
        if tenant_key:
            bind_vars["tenant_key"] = tenant_key
            query = self._RECENT_RUNOFF_TENANT_QUERY
        else:
            query = self._RECENT_RUNOFF_QUERY
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [self._to_model(doc) for doc in cursor]
