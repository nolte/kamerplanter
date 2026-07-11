"""REQ-026 Aquaponics ArangoDB repository.

Persists aquaponic systems, fish stocks, immutable water tests / feeding /
supplementation events (all tenant-scoped) and the global fish-species catalog.
Graph edges wire systems to stocks, tanks and grow-bed slots, and fish species to
compatible/incompatible plant species.

All AQL is parameterised via ``bind_vars`` (never f-string interpolation of
values) and every tenant-scoped list query filters on ``tenant_key`` (SEC-B4).
"""

from __future__ import annotations

from typing import Any

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.aquaponik import (
    AquaponicSystem,
    FishFeedingEvent,
    FishSpecies,
    FishStock,
    SupplementationEvent,
    WaterTest,
)


class ArangoAquaponikRepository(BaseArangoRepository[AquaponicSystem]):
    """Repository for the aquaponics domain (systems + child collections)."""

    is_tenant_scoped = True
    _model_cls = AquaponicSystem
    _entity_name = "AquaponicSystem"

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.AQUAPONIC_SYSTEMS)
        self._species = BaseArangoRepository[FishSpecies](db, col.FISH_SPECIES, FishSpecies)
        self._stocks = BaseArangoRepository[FishStock](db, col.FISH_STOCKS, FishStock)
        self._water_tests = BaseArangoRepository[WaterTest](db, col.WATER_TESTS, WaterTest)
        self._feedings = BaseArangoRepository[FishFeedingEvent](db, col.FISH_FEEDING_EVENTS, FishFeedingEvent)
        self._supplements = BaseArangoRepository[SupplementationEvent](
            db, col.SUPPLEMENTATION_EVENTS, SupplementationEvent
        )

    # ── FishSpecies (global catalog) ────────────────────────────────────

    def list_species(
        self,
        temperature_zone: str | None = None,
        feed_type: str | None = None,
    ) -> list[FishSpecies]:
        extra: list[tuple[str, str, Any]] = []
        if temperature_zone:
            extra.append(("temperature_zone", "==", temperature_zone))
        if feed_type:
            extra.append(("feed_type", "==", feed_type))
        if not extra:
            items, _ = self._species.get_all(offset=0, limit=500, all_tenants=True)
            return items
        first_field, first_op, first_value = extra[0]
        return self._species.find_by_field(first_field, first_value, extra_filters=extra[1:], sort="scientific_name")

    def get_species(self, key: str) -> FishSpecies | None:
        return self._species.get_by_key(key)

    def get_species_or_raise(self, key: str) -> FishSpecies:
        return self._species.get_or_raise(key)

    def create_species(self, species: FishSpecies) -> FishSpecies:
        return self._species.create(species)

    def get_compatible_plants(self, species_key: str, compatible: bool = True) -> list[dict[str, Any]]:
        """Graph-traverse compatible/incompatible plant species for a fish species."""
        edge_col = col.COMPATIBLE_FISH_PLANT if compatible else col.INCOMPATIBLE_FISH_PLANT
        query = """
        FOR v, e IN 1..1 OUTBOUND @start @@edge
          RETURN {
            species_key: v._key,
            common_name: v.common_name,
            scientific_name: v.scientific_name,
            temperature_match: e.temperature_match,
            nutrient_match: e.nutrient_match,
            reason: e.reason,
            notes: e.notes
          }
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"start": f"{col.FISH_SPECIES}/{species_key}", "@edge": edge_col},
        )
        return list(cursor)

    def link_compatible_plant(
        self, species_key: str, plant_species_key: str, data: dict[str, Any], compatible: bool = True
    ) -> None:
        edge_col = col.COMPATIBLE_FISH_PLANT if compatible else col.INCOMPATIBLE_FISH_PLANT
        self.create_edge(
            edge_col,
            f"{col.FISH_SPECIES}/{species_key}",
            f"{col.SPECIES}/{plant_species_key}",
            data,
        )

    # ── AquaponicSystem CRUD ────────────────────────────────────────────

    def list_systems(self, tenant_key: str) -> list[AquaponicSystem]:
        self._require_tenant_key(tenant_key, "list_systems")
        return self.find_by_field("tenant_key", tenant_key, sort="name")

    def create_system(self, system: AquaponicSystem) -> AquaponicSystem:
        return self.create(system)

    def delete_system(self, key: str) -> bool:
        system_id = f"{col.AQUAPONIC_SYSTEMS}/{key}"
        self.delete_edges(col.HAS_FISH_STOCK, system_id)
        self.delete_edges(col.SYSTEM_HAS_TANK, system_id)
        self.delete_edges(col.SYSTEM_HAS_GROWBED, system_id)
        self.delete_edges(col.WATER_TEST_FOR, system_id, direction="inbound")
        self.delete_edges(col.SUPPLEMENTATION_FOR, system_id, direction="inbound")
        for child_col in (col.WATER_TESTS, col.SUPPLEMENTATION_EVENTS, col.FISH_FEEDING_EVENTS):
            query = f"FOR doc IN {child_col} FILTER doc.system_key == @key REMOVE doc IN {child_col}"
            self._db.aql.execute(query, bind_vars={"key": key})
        query = f"FOR doc IN {col.FISH_STOCKS} FILTER doc.system_key == @key REMOVE doc IN {col.FISH_STOCKS}"
        self._db.aql.execute(query, bind_vars={"key": key})
        return self.delete(key)

    def link_tank(self, system_key: str, tank_key: str, tank_role: str) -> None:
        self.create_edge(
            col.SYSTEM_HAS_TANK,
            f"{col.AQUAPONIC_SYSTEMS}/{system_key}",
            f"{col.TANKS}/{tank_key}",
            {"tank_role": tank_role},
        )

    def link_growbed(self, system_key: str, slot_key: str) -> None:
        self.create_edge(
            col.SYSTEM_HAS_GROWBED,
            f"{col.AQUAPONIC_SYSTEMS}/{system_key}",
            f"{col.SLOTS}/{slot_key}",
        )

    # ── FishStock ───────────────────────────────────────────────────────

    def create_stock(self, stock: FishStock) -> FishStock:
        created = self._stocks.create(stock)
        if stock.system_key and created.key:
            self.create_edge(
                col.HAS_FISH_STOCK,
                f"{col.AQUAPONIC_SYSTEMS}/{stock.system_key}",
                f"{col.FISH_STOCKS}/{created.key}",
            )
        if stock.species_key and created.key:
            self.create_edge(
                col.STOCK_OF_SPECIES,
                f"{col.FISH_STOCKS}/{created.key}",
                f"{col.FISH_SPECIES}/{stock.species_key}",
            )
        return created

    def list_stocks(self, system_key: str, tenant_key: str) -> list[FishStock]:
        return self._stocks.find_by_field(
            "system_key",
            system_key,
            sort="name",
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    def get_stock(self, key: str) -> FishStock | None:
        return self._stocks.get_by_key(key)

    def get_stock_or_raise(self, key: str) -> FishStock:
        return self._stocks.get_or_raise(key)

    def update_stock(self, key: str, stock: FishStock) -> FishStock:
        return self._stocks.update(key, stock)

    def delete_stock(self, key: str) -> bool:
        stock_id = f"{col.FISH_STOCKS}/{key}"
        self.delete_edges(col.HAS_FISH_STOCK, stock_id, direction="inbound")
        self.delete_edges(col.STOCK_OF_SPECIES, stock_id)
        self.delete_edges(col.FEEDING_FOR_STOCK, stock_id, direction="inbound")
        return self._stocks.delete(key)

    # ── WaterTest (immutable) ───────────────────────────────────────────

    def create_water_test(self, water_test: WaterTest) -> WaterTest:
        created = self._water_tests.create(water_test, default_now_fields=("tested_at",))
        if water_test.system_key and created.key:
            self.create_edge(
                col.WATER_TEST_FOR,
                f"{col.WATER_TESTS}/{created.key}",
                f"{col.AQUAPONIC_SYSTEMS}/{water_test.system_key}",
            )
        return created

    def list_water_tests(self, system_key: str, tenant_key: str, offset: int = 0, limit: int = 50) -> list[WaterTest]:
        return self._water_tests.find_by_field(
            "system_key",
            system_key,
            sort="tested_at",
            sort_direction="DESC",
            offset=offset,
            limit=limit,
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    def get_latest_water_test(self, system_key: str) -> WaterTest | None:
        results = self._water_tests.find_by_field(
            "system_key", system_key, sort="tested_at", sort_direction="DESC", offset=0, limit=1
        )
        return results[0] if results else None

    # ── FishFeedingEvent (immutable) ────────────────────────────────────

    def create_feeding(self, feeding: FishFeedingEvent) -> FishFeedingEvent:
        created = self._feedings.create(feeding, default_now_fields=("fed_at",))
        if feeding.stock_key and created.key:
            self.create_edge(
                col.FEEDING_FOR_STOCK,
                f"{col.FISH_FEEDING_EVENTS}/{created.key}",
                f"{col.FISH_STOCKS}/{feeding.stock_key}",
            )
        return created

    def list_feedings(
        self, system_key: str, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> list[FishFeedingEvent]:
        return self._feedings.find_by_field(
            "system_key",
            system_key,
            sort="fed_at",
            sort_direction="DESC",
            offset=offset,
            limit=limit,
            extra_filters=[("tenant_key", "==", tenant_key)],
        )

    # ── SupplementationEvent (immutable) ────────────────────────────────

    def create_supplementation(self, event: SupplementationEvent) -> SupplementationEvent:
        created = self._supplements.create(event, default_now_fields=("applied_at",))
        if event.system_key and created.key:
            self.create_edge(
                col.SUPPLEMENTATION_FOR,
                f"{col.SUPPLEMENTATION_EVENTS}/{created.key}",
                f"{col.AQUAPONIC_SYSTEMS}/{event.system_key}",
            )
        return created

    def list_supplementations(
        self, system_key: str, tenant_key: str, offset: int = 0, limit: int = 50
    ) -> list[SupplementationEvent]:
        return self._supplements.find_by_field(
            "system_key",
            system_key,
            sort="applied_at",
            sort_direction="DESC",
            offset=offset,
            limit=limit,
            extra_filters=[("tenant_key", "==", tenant_key)],
        )
