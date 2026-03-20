from datetime import UTC, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.types import FertilizerKey, FertilizerStockKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.fertilizer_repository import IFertilizerRepository
from app.domain.models.fertilizer import Fertilizer, FertilizerStock


class ArangoFertilizerRepository(IFertilizerRepository, BaseArangoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        BaseArangoRepository.__init__(self, db, col.FERTILIZERS)

    # ── Fertilizer CRUD ──────────────────────────────────────────────

    def get_all(
        self,
        offset: int = 0,
        limit: int = 50,
        filters: dict | None = None,
        tenant_key: str | None = None,
    ) -> tuple[list[Fertilizer], int]:
        query = f"FOR doc IN {col.FERTILIZERS}"
        bind_vars: dict[str, Any] = {}
        filter_clauses = []
        if tenant_key:
            bind_vars["tenant_key"] = tenant_key
            filter_clauses.append(
                '(doc.tenant_key == @tenant_key OR doc.tenant_key == "" OR doc.tenant_key == null)'
            )
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
        query += f" SORT doc.product_name LIMIT {offset}, {limit} RETURN doc"
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [Fertilizer(**self._from_doc(doc)) for doc in cursor]
        count_cursor = self._db.aql.execute(count_query, bind_vars=bind_vars)
        total = next(count_cursor, 0)
        return items, total

    def get_by_key(self, key: FertilizerKey) -> Fertilizer | None:
        doc = BaseArangoRepository.get_by_key(self, key)
        return Fertilizer(**doc) if doc else None

    def create(self, fertilizer: Fertilizer) -> Fertilizer:
        doc = BaseArangoRepository.create(self, fertilizer)
        return Fertilizer(**doc)

    def update(self, key: FertilizerKey, fertilizer: Fertilizer) -> Fertilizer:
        doc = BaseArangoRepository.update(self, key, fertilizer)
        return Fertilizer(**doc)

    def delete(self, key: FertilizerKey) -> bool:
        fert_id = f"{col.FERTILIZERS}/{key}"
        # Delete outbound edges
        for edge_col in [col.HAS_STOCK, col.HAS_COMPONENT, col.FERT_INCOMPATIBLE]:
            self.delete_edges(edge_col, fert_id)
        # Delete inbound edges
        for edge_col in [col.FERT_INCOMPATIBLE, col.FEEDING_USED, col.PLAN_USES_FERTILIZER]:
            query = f"FOR e IN {edge_col} FILTER e._to == @fid REMOVE e IN {edge_col}"
            self._db.aql.execute(query, bind_vars={"fid": fert_id})
        # Delete child stocks
        query = (
            f"FOR doc IN {col.FERTILIZER_STOCKS} "
            f"FILTER doc.fertilizer_key == @key REMOVE doc IN {col.FERTILIZER_STOCKS}"
        )
        self._db.aql.execute(query, bind_vars={"key": key})
        return BaseArangoRepository.delete(self, key)

    # ── Stock CRUD ───────────────────────────────────────────────────

    def create_stock(self, stock: FertilizerStock) -> FertilizerStock:
        data = stock.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        now = datetime.now(UTC).isoformat()
        data["created_at"] = now
        data["updated_at"] = now
        result = self._db.collection(col.FERTILIZER_STOCKS).insert(data, return_new=True)
        doc = self._from_doc(result["new"])
        created = FertilizerStock(**doc)
        # Create edge
        from_id = f"{col.FERTILIZERS}/{stock.fertilizer_key}"
        to_id = f"{col.FERTILIZER_STOCKS}/{doc['_key']}"
        self.create_edge(col.HAS_STOCK, from_id, to_id)
        return created

    def get_stocks(self, fertilizer_key: FertilizerKey) -> list[FertilizerStock]:
        query = """
        FOR doc IN @@collection
          FILTER doc.fertilizer_key == @fert_key
          SORT doc.purchase_date DESC
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": col.FERTILIZER_STOCKS,
                "fert_key": fertilizer_key,
            },
        )
        return [FertilizerStock(**self._from_doc(doc)) for doc in cursor]

    def update_stock(self, key: FertilizerStockKey, stock: FertilizerStock) -> FertilizerStock:
        data = stock.model_dump(by_alias=True, exclude_none=True, mode="json")
        data.pop("_key", None)
        data["updated_at"] = datetime.now(UTC).isoformat()
        result = self._db.collection(col.FERTILIZER_STOCKS).update(
            {"_key": key, **data},
            return_new=True,
        )
        return FertilizerStock(**self._from_doc(result["new"]))

    def delete_stock(self, key: FertilizerStockKey) -> bool:
        stock_id = f"{col.FERTILIZER_STOCKS}/{key}"
        query = f"FOR e IN {col.HAS_STOCK} FILTER e._to == @sid REMOVE e IN {col.HAS_STOCK}"
        self._db.aql.execute(query, bind_vars={"sid": stock_id})
        try:
            self._db.collection(col.FERTILIZER_STOCKS).delete(key)
            return True
        except Exception:
            return False

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
