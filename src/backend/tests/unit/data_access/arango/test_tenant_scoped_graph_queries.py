"""The remaining "one line away" queries of #927, closed at the repository layer.

#927 lists these as unfiltered but not exploitable today, because their current
callers happen to check the anchor first. "Happens to check" is the property the
fix removes: the tenant predicate now lives in the query, so a new caller that
skips the anchor check cannot reintroduce the leak.

The database double replays whichever predicates the query actually spells out
(:mod:`tests.support.tenant_replay`), so removing the ``tenant_key`` filter from
any of these repositories turns the matching "…not visible…" test red — the same
red-first property as the API tests in
``tests/api/test_cross_tenant_reads_router.py``.

Both directions are asserted throughout: a foreign anchor must yield nothing,
*and* the caller's own data must still come back. A filter that also hides
legitimate rows is the #324 regression class, not a fix.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.data_access.arango import collections as col
from app.data_access.arango.nutrient_plan_repository import ArangoNutrientPlanRepository
from app.data_access.arango.plant_instance_repository import ArangoPlantInstanceRepository
from app.data_access.arango.site_repository import ArangoSiteRepository
from tests.support.tenant_replay import ReplayingAql, ReplayingDatabase, apply_predicates

TENANT_KEY = "tenant-a"
FOREIGN_TENANT_KEY = "tenant-b"

OWN_PLANT = "plant-a1"
FOREIGN_PLANT = "plant-b1"
OWN_SLOT = "slot-a1"
FOREIGN_SLOT = "slot-b1"
OWN_SITE = "site-a1"
FOREIGN_SITE = "site-b1"


def _plants() -> dict[str, dict[str, Any]]:
    return {
        OWN_PLANT: {
            "_key": OWN_PLANT,
            "_id": f"{col.PLANT_INSTANCES}/{OWN_PLANT}",
            "tenant_key": TENANT_KEY,
            "instance_id": "P-A1",
            "species_key": "solanum_lycopersicum",
            "slot_key": OWN_SLOT,
            "planted_on": "2026-04-01",
            "removed_on": None,
        },
        FOREIGN_PLANT: {
            "_key": FOREIGN_PLANT,
            "_id": f"{col.PLANT_INSTANCES}/{FOREIGN_PLANT}",
            "tenant_key": FOREIGN_TENANT_KEY,
            "instance_id": "P-B1",
            "species_key": "cucumis_sativus",
            "slot_key": FOREIGN_SLOT,
            "planted_on": "2026-04-02",
            "removed_on": None,
        },
    }


# ── nutrient_plan_repository.get_plant_plan ──────────────────────────────────


class TestPlantNutrientPlanAssignment:
    """The *assignment* must not cross tenants — the plan itself may be global.

    Nutrient plans are a hybrid catalog: a system plan carries ``tenant_key == ""``
    and is legitimately assigned to plants of every tenant (PR #324). The
    predicate therefore sits on the **plant**, not on the plan; a strict filter on
    the plan would answer ``None`` for every plant on a system plan, trading the
    leak for the #324 regression instead of fixing it.
    """

    def _repo(self) -> ArangoNutrientPlanRepository:
        plants = _plants()
        # ``own`` follows a tenant-owned plan, ``foreign`` a globally seeded one —
        # so the global plan is reachable from both and the test can tell a
        # plant-anchored predicate apart from a plan-anchored one.
        assignments = [
            {
                "_from": f"{col.PLANT_INSTANCES}/{OWN_PLANT}",
                "plan": {"_key": "np-own", "tenant_key": TENANT_KEY, "name": "Tomate Bio"},
            },
            {
                "_from": f"{col.PLANT_INSTANCES}/{FOREIGN_PLANT}",
                "plan": {"_key": "np-global", "tenant_key": "", "name": "Standard"},
            },
        ]

        def follows_plan(query: str, bind_vars: dict[str, Any]) -> Any:
            rows = [a for a in assignments if a["_from"] == bind_vars["pid"]]
            rows = apply_predicates(
                rows,
                query,
                bind_vars,
                resolvers={"plant": lambda row: plants.get(row["_from"].split("/")[-1])},
            )
            return [a["plan"] for a in rows]

        aql = ReplayingAql().route(col.FOLLOWS_PLAN, follows_plan)
        return ArangoNutrientPlanRepository(ReplayingDatabase(aql))

    def test_a_foreign_plants_assignment_is_not_visible(self):
        assert self._repo().get_plant_plan(FOREIGN_PLANT, tenant_key=TENANT_KEY) is None

    def test_the_callers_own_plant_still_resolves_its_plan(self):
        plan = self._repo().get_plant_plan(OWN_PLANT, tenant_key=TENANT_KEY)

        assert plan is not None
        assert plan.key == "np-own"

    def test_a_globally_seeded_plan_stays_readable_for_its_own_tenant(self):
        """#324 guard: the predicate must not be on the plan's ``tenant_key``.

        Read from the tenant that owns ``FOREIGN_PLANT``, the globally seeded plan
        (``tenant_key == ""``) has to come back — a plan-anchored filter would
        answer ``None`` here and silently unassign every system plan.
        """
        plan = self._repo().get_plant_plan(FOREIGN_PLANT, tenant_key=FOREIGN_TENANT_KEY)

        assert plan is not None
        assert plan.key == "np-global"

    def test_an_empty_tenant_key_is_rejected(self):
        with pytest.raises(ValueError, match="tenant"):
            self._repo().get_plant_plan(OWN_PLANT, tenant_key="")


# ── site_repository.get_location_tree / get_slot_for_plant ───────────────────


class TestSiteGraphQueries:
    """Locations and slots are tenant-resolved through their parent, not by themselves.

    The fixtures below deliberately give every location and slot
    ``tenant_key == ""``, because **that is the only shape the application ever
    writes**: neither ``LocationCreate``/``SlotCreate`` nor the routers behind
    them carry the field, and their full-replace ``PUT`` wipes anything the
    one-off ``v0004_backfill_tenant_key`` migration had put there. The design is
    stated in ``PlantInstanceService`` ("Location documents are persisted with an
    empty tenant_key and are tenant-verified through their parent site").

    An earlier revision of this file stamped ``tenant_key: TENANT_KEY`` onto both
    — a shape production cannot produce. That made
    ``test_the_callers_own_site_still_returns_its_locations`` pass against a
    predicate (``v.tenant_key == @tenant_key``) which in production matched *no*
    row at all, so the positive direction certified a query that silently
    returned an empty hierarchy. A fixture that cannot occur proves nothing; this
    is the #324 regression class arriving through the test data instead of
    through the query.
    """

    def _repo(self) -> ArangoSiteRepository:
        # Sites ARE reliably stamped — every write path (both site routers, the
        # onboarding service, the MCP CreateSite tool) passes an explicit
        # ``tenant_key`` — which is what makes the site a usable anchor.
        sites = {
            OWN_SITE: {
                "_key": OWN_SITE,
                "_id": f"{col.SITES}/{OWN_SITE}",
                "tenant_key": TENANT_KEY,
                "name": "Garten A",
            },
            FOREIGN_SITE: {
                "_key": FOREIGN_SITE,
                "_id": f"{col.SITES}/{FOREIGN_SITE}",
                "tenant_key": FOREIGN_TENANT_KEY,
                "name": "Garten B",
            },
        }
        locations = [
            {
                "_key": "loc-a1",
                "_id": f"{col.LOCATIONS}/loc-a1",
                "tenant_key": "",  # production shape — see the class docstring
                "site_key": OWN_SITE,
                "name": "Beet A",
                "area_m2": 4.0,
            },
            {
                "_key": "loc-b1",
                "_id": f"{col.LOCATIONS}/loc-b1",
                "tenant_key": "",
                "site_key": FOREIGN_SITE,
                "name": "Beet B",
                "area_m2": 5.0,
            },
        ]
        # ``placed_in`` edges, modelled the way the nutrient-plan fixture models
        # ``follows_plan``: the row is the edge, so the fake can resolve the
        # *plant* the query anchors on rather than being handed the answer.
        placements = [
            {
                "_from": f"{col.PLANT_INSTANCES}/{OWN_PLANT}",
                "slot": {
                    "_key": OWN_SLOT,
                    "_id": f"{col.SLOTS}/{OWN_SLOT}",
                    "tenant_key": "",  # production shape — see the class docstring
                    "slot_id": "BEETA_A1",
                    "location_key": "loc-a1",
                },
            },
            {
                "_from": f"{col.PLANT_INSTANCES}/{FOREIGN_PLANT}",
                "slot": {
                    "_key": FOREIGN_SLOT,
                    "_id": f"{col.SLOTS}/{FOREIGN_SLOT}",
                    "tenant_key": "",
                    "slot_id": "BEETB_A1",
                    "location_key": "loc-b1",
                },
            },
        ]
        plants = _plants()

        def location_tree(query: str, bind_vars: dict[str, Any]) -> Any:
            site_key = str(bind_vars["start_id"]).split("/")[-1]
            rows = [loc for loc in locations if loc["site_key"] == site_key]
            return apply_predicates(
                rows,
                query,
                bind_vars,
                # ``site`` is ``DOCUMENT(@start_id)`` — the traversal's start
                # vertex, not the row's own idea of its site.
                resolvers={"v": lambda row: row, "site": lambda _row: sites.get(site_key)},
            )

        def slot_for_plant(query: str, bind_vars: dict[str, Any]) -> Any:
            plant_id = str(bind_vars["plant_id"])
            rows = [p for p in placements if p["_from"] == plant_id]
            rows = apply_predicates(
                rows,
                query,
                bind_vars,
                resolvers={
                    "slot": lambda row: row["slot"],
                    "plant": lambda row: plants.get(row["_from"].split("/")[-1]),
                },
            )
            return [p["slot"] for p in rows]

        aql = ReplayingAql()
        aql.route("@contains_col", location_tree)
        aql.route("@@placed_in", slot_for_plant)
        return ArangoSiteRepository(ReplayingDatabase(aql))

    def test_a_foreign_sites_location_tree_is_not_walkable(self):
        assert self._repo().get_location_tree(FOREIGN_SITE, tenant_key=TENANT_KEY) == []

    def test_the_callers_own_site_still_returns_its_locations(self):
        """Red against a ``v.tenant_key`` predicate — which is the whole point.

        The location comes back *and* carries an empty ``tenant_key``: asserting
        both together is what keeps a later "simplification" of the query from
        passing. A predicate on the location itself returns ``[]`` here, i.e. the
        site's hierarchy silently disappears from ``GET …/location-tree``.
        """
        tree = self._repo().get_location_tree(OWN_SITE, tenant_key=TENANT_KEY)

        assert [loc.key for loc in tree] == ["loc-a1"]
        assert tree[0].tenant_key == ""

    def test_a_foreign_plants_slot_is_not_resolvable(self):
        assert self._repo().get_slot_for_plant(FOREIGN_PLANT, tenant_key=TENANT_KEY) is None

    def test_the_callers_own_plant_still_resolves_its_slot(self):
        """Red against a ``slot.tenant_key`` predicate: every slot resolves to ``None``.

        Both callers treat ``None`` as "plant is not placed", so the loss is
        silent — no irrigation warnings, no REQ-005 soil-moisture override.
        """
        slot = self._repo().get_slot_for_plant(OWN_PLANT, tenant_key=TENANT_KEY)

        assert slot is not None
        assert slot.key == OWN_SLOT
        assert slot.tenant_key == ""

    @pytest.mark.parametrize(("method", "anchor"), [("get_location_tree", OWN_SITE), ("get_slot_for_plant", OWN_PLANT)])
    def test_an_empty_tenant_key_is_rejected(self, method, anchor):
        with pytest.raises(ValueError, match="tenant"):
            getattr(self._repo(), method)(anchor, tenant_key="")


# ── plant_instance_repository.get_active_by_slot / get_history_by_slot ───────


class TestSlotOccupancyAndHistory:
    """What grows in a bed, and what grew there before, is tenant-private.

    Both feed engines whose *output is prose*: the companion-planting warning
    names the neighbouring species, the rotation verdict the botanical family
    previously grown there. An unscoped read would put another tenant's crop into
    this tenant's message.
    """

    def _repo(self) -> ArangoPlantInstanceRepository:
        plants = _plants()

        def by_slot(query: str, bind_vars: dict[str, Any]) -> Any:
            slot_key = str(bind_vars["slot_id"]).split("/")[-1]
            rows = [p for p in plants.values() if p["slot_key"] == slot_key]
            return apply_predicates(rows, query, bind_vars, resolvers={"v": lambda row: row})

        aql = ReplayingAql().route("INBOUND @slot_id", by_slot)
        return ArangoPlantInstanceRepository(ReplayingDatabase(aql))

    def test_a_foreign_slot_shows_no_occupants(self):
        assert self._repo().get_active_by_slot(FOREIGN_SLOT, tenant_key=TENANT_KEY) == []

    def test_the_callers_own_slot_still_shows_its_occupants(self):
        occupants = self._repo().get_active_by_slot(OWN_SLOT, tenant_key=TENANT_KEY)

        assert [p.key for p in occupants] == [OWN_PLANT]

    def test_a_foreign_slot_has_no_readable_history(self):
        assert self._repo().get_history_by_slot(FOREIGN_SLOT, tenant_key=TENANT_KEY) == []

    def test_the_callers_own_slot_still_has_its_history(self):
        history = self._repo().get_history_by_slot(OWN_SLOT, tenant_key=TENANT_KEY)

        assert [p.key for p in history] == [OWN_PLANT]

    @pytest.mark.parametrize("method", ["get_active_by_slot", "get_history_by_slot"])
    def test_an_empty_tenant_key_is_rejected(self, method):
        with pytest.raises(ValueError, match="tenant"):
            getattr(self._repo(), method)(OWN_SLOT, tenant_key="")

    @pytest.mark.parametrize("method", ["get_active_by_slot", "get_history_by_slot"])
    def test_omitting_the_tenant_entirely_is_a_type_error(self, method):
        with pytest.raises(TypeError):
            getattr(self._repo(), method)(OWN_SLOT)
