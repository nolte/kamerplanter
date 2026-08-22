from typing import Any

from arango.database import StandardDatabase

from app.common.types import FertilizerKey, FertilizerStockKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.tenant_scope import tenant_union_predicate
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.models.fertilizer import Fertilizer, FertilizerStock


class ArangoFertilizerRepository(BaseArangoRepository[Fertilizer], IFertilizerRepository):
    is_tenant_scoped = True
    _model_cls = Fertilizer

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.FERTILIZERS)
        self._stocks = BaseArangoRepository[FertilizerStock](db, col.FERTILIZER_STOCKS, FertilizerStock)

    # ── Fertilizer CRUD ──────────────────────────────────────────────

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        tenant_key: str | None = None,
        *,
        all_tenants: bool = False,
    ) -> tuple[list[Fertilizer], int]:
        # Fertilizers are a hybrid catalog: global products (empty tenant_key)
        # PLUS per-tenant custom products.  When a tenant_key is supplied the
        # query below unions the tenant's own rows with the global rows; a
        # missing tenant_key must therefore be an explicit system-context opt-in
        # (all_tenants=True) rather than a silent all-tenant read (SEC-B4).
        self._enforce_tenant_scope(tenant_key, all_tenants)
        query = f"FOR doc IN {col.FERTILIZERS}"
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
                if field == "brand":
                    filter_clauses.append(f"CONTAINS(LOWER(doc.{field}), LOWER(@val{i}))")
                else:
                    filter_clauses.append(f"doc.{field} == @val{i}")
        if filter_clauses:
            query += " FILTER " + " AND ".join(filter_clauses)
        count_query = query + " COLLECT WITH COUNT INTO total RETURN total"
        count_vars = dict(bind_vars)
        bind_vars["offset"] = offset
        bind_vars["limit"] = limit
        query += " SORT doc.product_name LIMIT @offset, @limit RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [Fertilizer(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
        total = next(count_cursor, 0)
        return items, total

    def delete(self, key: FertilizerKey) -> bool:
        fert_id = f"{col.FERTILIZERS}/{key}"
        # Delete outbound edges
        for edge_col in [col.HAS_STOCK, col.HAS_COMPONENT, col.FERT_INCOMPATIBLE]:
            self.delete_edges(edge_col, fert_id)
        # Delete inbound edges
        for edge_col in [col.FERT_INCOMPATIBLE, col.FEEDING_USED, col.PLAN_USES_FERTILIZER]:
            self.delete_edges(edge_col, fert_id, direction="inbound")
        # Delete child stocks
        query = (
            f"FOR doc IN {col.FERTILIZER_STOCKS} "
            f"FILTER doc.fertilizer_key == @key REMOVE doc IN {col.FERTILIZER_STOCKS}"
        )
        self._db.aql.execute(query, bind_vars={"key": key})
        return super().delete(key)

    # ── Stock CRUD ───────────────────────────────────────────────────

    def create_stock(self, stock: FertilizerStock) -> FertilizerStock:
        created = self._stocks.create(stock)
        # Create edge
        from_id = f"{col.FERTILIZERS}/{stock.fertilizer_key}"
        to_id = f"{col.FERTILIZER_STOCKS}/{created.key}"
        self.create_edge(col.HAS_STOCK, from_id, to_id)
        return created

    def get_stock_or_raise(self, key: FertilizerStockKey) -> FertilizerStock:
        """Read one stock row, 404 when absent.

        Added in #1265. Its absence is why ``FertilizerService.update_stock``
        carried the comment "stocks don't have a dedicated get" and then wrote a
        freshly constructed model over the stored document instead of reading it.
        """
        return self._stocks.get_or_raise(key)

    def get_stocks(self, fertilizer_key: FertilizerKey) -> list[FertilizerStock]:
        return self._stocks.find_by_field("fertilizer_key", fertilizer_key, sort="purchase_date", sort_direction="DESC")

    def update_stock(self, key: FertilizerStockKey, stock: FertilizerStock) -> FertilizerStock:
        return self._stocks.update(key, stock)

    def delete_stock(self, key: FertilizerStockKey) -> bool:
        stock_id = f"{col.FERTILIZER_STOCKS}/{key}"
        self.delete_edges(col.HAS_STOCK, stock_id, direction="inbound")
        return self._stocks.delete(key)

    # ── Incompatibility ──────────────────────────────────────────────

    def add_incompatibility(
        self,
        key_a: FertilizerKey,
        key_b: FertilizerKey,
        reason: str,
        severity: str,
    ) -> dict:
        from_id = f"{col.FERTILIZERS}/{key_a}"
        to_id = f"{col.FERTILIZERS}/{key_b}"
        edge_data = {"reason": reason, "severity": severity}
        return self.create_edge(col.FERT_INCOMPATIBLE, from_id, to_id, edge_data)

    def get_incompatibilities(self, key: FertilizerKey) -> list[dict]:
        fert_id = f"{col.FERTILIZERS}/{key}"
        query = f"""
        FOR e IN {col.FERT_INCOMPATIBLE}
          FILTER e._from == @fid OR e._to == @fid
          LET other_id = e._from == @fid ? e._to : e._from
          LET other = DOCUMENT(other_id)
          RETURN {{
            fertilizer_key: PARSE_IDENTIFIER(other_id).key,
            product_name: other.product_name,
            reason: e.reason,
            severity: e.severity
          }}
        """
        cursor = self._db.aql.execute(query, bind_vars={"fid": fert_id})
        return list(cursor)

    def remove_incompatibility(self, key_a: FertilizerKey, key_b: FertilizerKey) -> bool:
        from_a = f"{col.FERTILIZERS}/{key_a}"
        from_b = f"{col.FERTILIZERS}/{key_b}"
        query = f"""
        FOR e IN {col.FERT_INCOMPATIBLE}
          FILTER (e._from == @a AND e._to == @b) OR (e._from == @b AND e._to == @a)
          REMOVE e IN {col.FERT_INCOMPATIBLE}
        """
        self._db.aql.execute(query, bind_vars={"a": from_a, "b": from_b})
        return True

    # ── Reverse lookup ─────────────────────────────────────────────────

    def get_nutrient_plan_usage(self, key: FertilizerKey) -> list[dict]:
        query = f"""
        FOR entry IN {col.NUTRIENT_PLAN_PHASE_ENTRIES}
          LET matched_channels = (
            FOR ch IN (entry.delivery_channels || [])
              LET matched = (
                FOR d IN (ch.fertilizer_dosages || [])
                  FILTER d.fertilizer_key == @fert_key
                  RETURN d
              )
              FILTER LENGTH(matched) > 0
              RETURN {{
                channel_id: ch.channel_id,
                label: ch.label,
                application_method: ch.application_method,
                ml_per_liter: matched[0].ml_per_liter
              }}
          )
          FILTER LENGTH(matched_channels) > 0
          LET plan = DOCUMENT(CONCAT("{col.NUTRIENT_PLANS}/", entry.plan_key))
          FILTER plan != null
          COLLECT plan_key = entry.plan_key,
                  plan_name = plan.name
          INTO groups
          LET phase_data = (
            FOR g IN groups
              RETURN {{
                phase_name: g.entry.phase_name,
                week_start: g.entry.week_start,
                week_end: g.entry.week_end,
                channels: g.matched_channels
              }}
          )
          RETURN {{ key: plan_key, name: plan_name, phase_entries: phase_data }}
        """
        cursor = self._db.aql.execute(query, bind_vars={"fert_key": key})
        return list(cursor)
