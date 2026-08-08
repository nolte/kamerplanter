"""REQ-033 §2.1 — plant read tools.

These tools exist to close the addressing gap: every write tool takes a
``plant_key``, and before them only plants with a pending care task ever exposed
one. The tests below pin the two properties that matter — the tenant-scoped
delegation, and the filtering that makes a plant findable by name.

Fake services throughout, so no ArangoDB is involved.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from app.common.enums import ReminderType, SubstrateType, TenantRole
from app.common.exceptions import ValidationError
from app.domain.models.phase import PhaseHistory
from app.domain.models.substrate import Substrate
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.phases import (
    PHASE_STATE_BETWEEN_CYCLES,
    PHASE_STATE_NEVER_INITIALISED,
)
from app.mcp_server.tools.plant_reads import (
    PHASE_STATE_UNKNOWN,
    GetPlant,
    GetPlantCareLog,
    ListPlants,
    ListPlantsAtLocation,
)


class _Plant:
    def __init__(
        self,
        key,
        name=None,
        *,
        species="sp-tomato",
        location=None,
        slot=None,
        site=None,
        removed=None,
        substrate_key=None,
        substrate_type_override=None,
        current_phase_key="vegetative",
    ):
        self.key = key
        self.instance_id = f"INST-{key}"
        self.plant_name = name
        self.species_key = species
        self.cultivar_key = None
        self.site_key = site
        self.location_key = location
        self.slot_key = slot
        self.substrate_key = substrate_key
        self.substrate_batch_key = None
        self.substrate_type_override = substrate_type_override
        self.planted_on = date(2026, 4, 1)
        self.removed_on = removed
        self.current_phase_key = current_phase_key


def _membership() -> McpTenantMembership:
    return McpTenantMembership(tenant_key="home", tenant_slug="home", tenant_name="Home", role=TenantRole.LEAD)


def _ctx(**services) -> ToolContext:
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, _membership(), services=services)


class _PlantService:
    """Records the tenant it was asked for, so isolation is assertable."""

    def __init__(self, plants):
        self._plants = plants
        self.seen_tenant = None

    def list_plants(self, offset=0, limit=50, tenant_key=""):
        self.seen_tenant = tenant_key
        page = self._plants[offset : offset + limit]
        return page, len(self._plants)

    def get_plant(self, key, tenant_key=""):
        self.seen_tenant = tenant_key
        for p in self._plants:
            if p.key == key:
                return p
        from app.common.exceptions import NotFoundError

        raise NotFoundError("PlantInstance", key)


@pytest.mark.asyncio
async def test_list_plants_is_tenant_scoped():
    svc = _PlantService([_Plant("p1", "Tomate"), _Plant("p2", "Basilikum")])
    tool = ListPlants()
    resp = await tool.run(_ctx(plant_instance_service=svc), tool.Input())
    assert svc.seen_tenant == "home"
    assert resp.data["count"] == 2
    assert {i["plant_key"] for i in resp.data["items"]} == {"p1", "p2"}


@pytest.mark.asyncio
async def test_list_plants_filters_by_name_so_a_plant_becomes_addressable():
    # The point of the query filter: turn "my tomato" into a plant_key the write
    # tools can consume.
    svc = _PlantService([_Plant("p1", "Tomate Nord"), _Plant("p2", "Basilikum")])
    tool = ListPlants()
    resp = await tool.run(_ctx(plant_instance_service=svc), tool.Input(query="tomate"))
    assert [i["plant_key"] for i in resp.data["items"]] == ["p1"]


@pytest.mark.asyncio
async def test_list_plants_hides_archived_unless_asked():
    svc = _PlantService([_Plant("p1", "Alt", removed=date(2026, 5, 1)), _Plant("p2", "Neu")])
    tool = ListPlants()

    default = await tool.run(_ctx(plant_instance_service=svc), tool.Input())
    assert [i["plant_key"] for i in default.data["items"]] == ["p2"]

    with_archived = await tool.run(_ctx(plant_instance_service=svc), tool.Input(include_archived=True))
    assert {i["plant_key"] for i in with_archived.data["items"]} == {"p1", "p2"}


@pytest.mark.asyncio
async def test_get_plant_returns_master_data_and_resolves_the_species_name():
    svc = _PlantService([_Plant("p1", "Tomate")])
    species = type("S", (), {"scientific_name": "Solanum lycopersicum", "common_names": ["Tomate"]})()
    ctx = _ctx(plant_instance_service=svc, species_service=type("X", (), {"get_species": lambda self, k: species})())
    tool = GetPlant()

    resp = await tool.run(ctx, tool.Input(plant_key="p1"))
    assert svc.seen_tenant == "home"
    assert resp.data["species_name"] == "Solanum lycopersicum"
    assert resp.data["plant_key"] == "p1"


@pytest.mark.asyncio
async def test_get_plant_survives_a_missing_catalogue_entry():
    # A dangling species reference must not turn a plant read into an error.
    svc = _PlantService([_Plant("p1", "Tomate")])

    class _Broken:
        def get_species(self, key):
            raise RuntimeError("catalogue unavailable")

    resp = await GetPlant().run(
        _ctx(plant_instance_service=svc, species_service=_Broken()),
        GetPlant.Input(plant_key="p1"),
    )
    assert resp.data["species_name"] is None
    assert resp.data["plant_key"] == "p1"


# ══ The medium a plant stands in ═════════════════════════════════════════════
#
# ``list_substrates`` publishes ph_base, ec_base_ms, buffer_capacity and
# cec_meq_per_100g — the properties that decide whether a given feeding level is
# excessive. Without a substrate reference on the plant, that catalogue is
# unreachable from an instance: an agent would have to guess which medium it is
# looking at, and the same weekly dose is harmless in one and an overdose in
# another.


class _SpeciesStub:
    def get_species(self, key):
        return type("S", (), {"scientific_name": "Solanum lycopersicum", "common_names": []})()


class _SubstrateService:
    """Records its calls, so "resolved once" and "not called at all" are both assertable."""

    def __init__(self, substrate=None, *, broken=False):
        self._substrate = substrate
        self._broken = broken
        self.calls: list[str] = []

    def get_substrate(self, key):
        self.calls.append(key)
        if self._broken:
            raise RuntimeError("catalogue unavailable")
        return self._substrate


def _substrate(name="Coco 70/30", type_=SubstrateType.COCO):
    """A real ``Substrate``, not a stub carrying whatever attribute the tool reads.

    The catalogue model has ``name_de``/``name_en`` and **no** ``name`` field. A
    stub that invents one lets a reader of ``substrate.name`` pass here while
    returning ``substrate_name: null`` against the real catalogue — which is
    exactly what #1006 observed in production.
    """

    return Substrate(_key="sub-coco", name_de=name, name_en=name, type=type_)


@pytest.mark.asyncio
async def test_get_plant_resolves_the_substrate_so_the_catalogue_becomes_reachable():
    svc = _PlantService([_Plant("p1", "Tomate", substrate_key="sub-coco")])
    substrates = _SubstrateService(_substrate())
    ctx = _ctx(plant_instance_service=svc, species_service=_SpeciesStub(), substrate_service=substrates)

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert resp.data["substrate_key"] == "sub-coco", "the key is what list_substrates is keyed by"
    assert resp.data["substrate_type"] == "coco"
    assert resp.data["substrate_name"] == "Coco 70/30"
    assert substrates.calls == ["sub-coco"], "resolved once, like the species name"
    # A plain str, not the enum member. StrEnum makes the two compare equal, so
    # `== "coco"` above would pass either way; this is the assertion that would
    # actually notice if the enum stopped deriving from str.
    assert type(resp.data["substrate_type"]) is str


@pytest.mark.asyncio
async def test_the_substrate_name_falls_back_to_the_english_one():
    """#1006: the join resolved, the *name* did not — the tool read a field that
    does not exist on the model. A record carrying only the English name must
    still produce a name rather than a null next to a populated key."""

    svc = _PlantService([_Plant("p1", "Tomate", substrate_key="sub-perlite")])
    substrate = Substrate(_key="sub-perlite", name_en="Perlite", type=SubstrateType.PERLITE)
    ctx = _ctx(
        plant_instance_service=svc,
        species_service=_SpeciesStub(),
        substrate_service=_SubstrateService(substrate),
    )

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert resp.data["substrate_name"] == "Perlite"


@pytest.mark.asyncio
async def test_a_nameless_substrate_record_still_reports_its_key_and_type():
    """The only remaining null: the catalogue record itself carries no name.

    Then ``substrate_name: null`` is the honest answer — the gap is in the
    catalogue, not in the join — and the key plus the type still travel.
    """

    svc = _PlantService([_Plant("p1", "Tomate", substrate_key="sub-anon")])
    ctx = _ctx(
        plant_instance_service=svc,
        species_service=_SpeciesStub(),
        substrate_service=_SubstrateService(Substrate(_key="sub-anon", type=SubstrateType.SOIL)),
    )

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert resp.data["substrate_name"] is None
    assert resp.data["substrate_key"] == "sub-anon"
    assert resp.data["substrate_type"] == "soil"


@pytest.mark.asyncio
async def test_an_explicit_substrate_override_wins_over_the_referenced_record():
    """The cascade PlantInstance declares and WateringService applies.

    Reversing it would report the medium the grower explicitly said it is *not*.
    """

    svc = _PlantService([_Plant("p1", "Tomate", substrate_key="sub-coco", substrate_type_override=SubstrateType.SOIL)])
    ctx = _ctx(
        plant_instance_service=svc,
        species_service=_SpeciesStub(),
        substrate_service=_SubstrateService(_substrate(type_=SubstrateType.COCO)),
    )

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert resp.data["substrate_type"] == "soil"
    assert resp.data["substrate_type_override"] == "soil", "the raw field stays visible next to the resolution"
    assert type(resp.data["substrate_type_override"]) is str, "the list projection emits a str too"


@pytest.mark.asyncio
async def test_a_plant_without_a_substrate_reference_is_not_looked_up():
    svc = _PlantService([_Plant("p1", "Tomate")])
    substrates = _SubstrateService(_substrate())
    ctx = _ctx(plant_instance_service=svc, species_service=_SpeciesStub(), substrate_service=substrates)

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert resp.data["substrate_type"] is None
    assert resp.data["substrate_name"] is None
    assert substrates.calls == [], "no key, no lookup"


@pytest.mark.asyncio
async def test_get_plant_survives_a_missing_substrate_record():
    """Same rule as the species catalogue: a dangling reference is not a read error."""

    svc = _PlantService([_Plant("p1", "Tomate", substrate_key="gone")])
    ctx = _ctx(
        plant_instance_service=svc,
        species_service=_SpeciesStub(),
        substrate_service=_SubstrateService(broken=True),
    )

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert resp.data["substrate_name"] is None
    assert resp.data["substrate_key"] == "gone", "the dangling key is still reported, not swallowed"


@pytest.mark.asyncio
async def test_the_list_projection_carries_the_raw_substrate_keys_without_resolving_them():
    """A page must not turn into an N+1 across the substrate catalogue."""

    svc = _PlantService([_Plant("p1", "Tomate", substrate_key="sub-coco")])
    substrates = _SubstrateService(_substrate())

    resp = await ListPlants().run(
        _ctx(plant_instance_service=svc, substrate_service=substrates),
        ListPlants.Input(),
    )

    assert resp.data["items"][0]["substrate_key"] == "sub-coco"
    assert substrates.calls == [], "the list tools resolve nothing — get_plant does"


# ══ The phase state behind a null current_phase_key ══════════════════════════
#
# ``current_phase_key: null`` on ``get_plant`` conflates "never enrolled in the
# lifecycle", "resting between cycles" and "dangling phase record" — three states
# that each call for a different action (#1006, #949). The distinction already
# exists on ``get_plant_phase_status`` as ``phase_state``; ``get_plant`` surfaces
# the very same value (via the shared ``_classify_phase_state``) when, and only
# when, the key is null — so the detail view is self-explaining without a second
# tool call, and the healthy path pays for no extra service calls.


def _completed_history_row() -> PhaseHistory:
    """A real phase-history row that has been exited — ``_classify_phase_state``
    reads ``exited_at`` off it, so a bare mock whose value never becomes the shape
    the classifier reads would certify nothing (#996)."""

    entered = datetime(2026, 4, 1, 8, 0)
    return PhaseHistory(
        _key="ph-1",
        plant_instance_key="p1",
        phase_key="e-3",
        phase_name="dormancy",
        entered_at=entered,
        exited_at=datetime(2026, 6, 1, 8, 0),
        cycle_number=1,
        transition_reason="completed",
    )


class _PhaseService:
    """Records its call count, so "resolved on null" and "not touched on a healthy
    plant" are both assertable. Returns realistic ``get_current_phase`` dicts and
    real ``PhaseHistory`` rows — not a mock whose return never becomes the shape
    ``_classify_phase_state`` reads (the #996 trap)."""

    def __init__(self, current=None, history=None, *, broken=False):
        self._current = current if current is not None else {"phase_key": "", "phase": ""}
        self._history = history if history is not None else []
        self._broken = broken
        self.calls = 0

    def get_current_phase(self, plant_key):
        self.calls += 1
        if self._broken:
            raise RuntimeError("phase engine unavailable")
        return self._current

    def get_phase_history(self, plant_key):
        if self._broken:
            raise RuntimeError("phase engine unavailable")
        return self._history


@pytest.mark.asyncio
async def test_get_plant_surfaces_phase_state_when_the_current_phase_key_is_null():
    # RED against the pre-fix code: no ``phase_state`` key exists in the response
    # at all, so a consumer reading get_plant alone cannot tell why the phase is
    # null. GREEN once get_plant reuses _classify_phase_state: a plant with a null
    # key and no history reads as never_initialised.
    svc = _PlantService([_Plant("p1", "Tomate", current_phase_key=None)])
    phases = _PhaseService()  # empty current, no history
    ctx = _ctx(plant_instance_service=svc, species_service=_SpeciesStub(), phase_service=phases)

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert resp.data["phase_state"] == PHASE_STATE_NEVER_INITIALISED
    assert resp.data["current_phase_key"] is None


@pytest.mark.asyncio
async def test_get_plant_classifies_a_completed_cycle_as_between_cycles():
    # A null key with an all-exited history is a perennial resting between cycles,
    # not an uninitialised plant — the classifier reads exited_at off the row.
    svc = _PlantService([_Plant("p1", "Yucca", current_phase_key=None)])
    phases = _PhaseService(history=[_completed_history_row()])
    ctx = _ctx(plant_instance_service=svc, species_service=_SpeciesStub(), phase_service=phases)

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert resp.data["phase_state"] == PHASE_STATE_BETWEEN_CYCLES


@pytest.mark.asyncio
async def test_get_plant_omits_phase_state_when_the_plant_is_in_a_phase():
    # only-on-null decision: a truthy current_phase_key already names a real phase,
    # so phase_state would be a redundant in_phase — and computing it would cost two
    # phase-service calls on the common healthy path for no new information.
    svc = _PlantService([_Plant("p1", "Tomate", current_phase_key="vegetative")])
    phases = _PhaseService()
    ctx = _ctx(plant_instance_service=svc, species_service=_SpeciesStub(), phase_service=phases)

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert "phase_state" not in resp.data
    assert resp.data["current_phase_key"] == "vegetative"
    assert phases.calls == 0, "the healthy path resolves no phase state"


@pytest.mark.asyncio
async def test_get_plant_survives_a_raising_phase_service():
    # Same rule as the species/substrate lookups: a failing phase read must not turn
    # a plant read into a 500. It degrades to an explicit "unknown" — never a null
    # phase_state, which would reintroduce the very opacity the field exists to remove.
    svc = _PlantService([_Plant("p1", "Tomate", current_phase_key=None)])
    phases = _PhaseService(broken=True)
    ctx = _ctx(plant_instance_service=svc, species_service=_SpeciesStub(), phase_service=phases)

    resp = await GetPlant().run(ctx, GetPlant.Input(plant_key="p1"))

    assert resp.data["phase_state"] == PHASE_STATE_UNKNOWN
    assert resp.data["plant_key"] == "p1"


@pytest.mark.asyncio
async def test_list_plants_at_location_filters_on_the_given_level():
    svc = _PlantService(
        [
            _Plant("p1", "Beet-2-A", location="loc-beet-2"),
            _Plant("p2", "Beet-3-A", location="loc-beet-3"),
        ]
    )
    tool = ListPlantsAtLocation()
    resp = await tool.run(_ctx(plant_instance_service=svc), tool.Input(location_key="loc-beet-2"))
    assert [i["plant_key"] for i in resp.data["items"]] == ["p1"]


@pytest.mark.asyncio
async def test_list_plants_at_location_requires_a_filter():
    # Without one it would silently degrade into "list everything", which is what
    # list_plants is for — refuse instead of answering a different question.
    svc = _PlantService([_Plant("p1", "X")])
    with pytest.raises(ValidationError):
        await ListPlantsAtLocation().run(_ctx(plant_instance_service=svc), ListPlantsAtLocation.Input())


@pytest.mark.asyncio
async def test_care_log_checks_plant_ownership_before_reading_history():
    # get_confirmation_history takes no tenant, so the ownership check has to
    # happen on the plant first — otherwise a foreign key would leak its history.
    svc = _PlantService([_Plant("p1", "Tomate")])
    calls = {}

    class _Care:
        def get_confirmation_history(self, plant_key, reminder_type=None, limit=50):
            calls["args"] = (plant_key, reminder_type, limit)
            return [
                type(
                    "C",
                    (),
                    {
                        "confirmed_at": datetime(2026, 8, 1, 9, 0),
                        "reminder_type": ReminderType.WATERING,
                        "action": "done",
                        "notes": None,
                        "interval_at_time": 5,
                    },
                )()
            ]

    tool = GetPlantCareLog()
    resp = await tool.run(
        _ctx(plant_instance_service=svc, care_reminder_service=_Care()),
        tool.Input(plant_key="p1", reminder_type=ReminderType.WATERING),
    )

    assert svc.seen_tenant == "home"  # ownership verified against the acting tenant
    assert calls["args"] == ("p1", ReminderType.WATERING, 50)
    assert resp.data["count"] == 1


@pytest.mark.asyncio
async def test_care_log_says_so_when_nothing_was_recorded():
    svc = _PlantService([_Plant("p1", "Tomate")])

    class _Empty:
        def get_confirmation_history(self, plant_key, reminder_type=None, limit=50):
            return []

    resp = await GetPlantCareLog().run(
        _ctx(plant_instance_service=svc, care_reminder_service=_Empty()),
        GetPlantCareLog.Input(plant_key="p1"),
    )
    assert resp.data["count"] == 0
    assert "No care recorded yet" in resp.summary


# ── Filtering must span the whole set, not one page ───────────────────────────
@pytest.mark.asyncio
async def test_list_plants_finds_a_match_beyond_the_first_page():
    # The regression: the tool used to read `limit` records and filter those, so a
    # plant past the first page reported "0 match" — a wrong answer, not a short
    # one, from the very tool a model uses to resolve a name into a plant_key.
    plants = [_Plant(f"p{i}", f"Basilikum {i}") for i in range(120)]
    plants.append(_Plant("p-tomato", "Tomate Nord"))
    svc = _PlantService(plants)

    tool = ListPlants()
    resp = await tool.run(_ctx(plant_instance_service=svc), tool.Input(query="tomate", limit=50))

    assert [i["plant_key"] for i in resp.data["items"]] == ["p-tomato"]
    assert resp.data["matched"] == 1
    assert resp.data["truncated"] is False


@pytest.mark.asyncio
async def test_list_plants_paginates_the_filtered_set():
    plants = [_Plant(f"p{i}", f"Tomate {i}") for i in range(60)]
    svc = _PlantService(plants)
    tool = ListPlants()

    first = await tool.run(_ctx(plant_instance_service=svc), tool.Input(query="tomate", limit=25))
    second = await tool.run(_ctx(plant_instance_service=svc), tool.Input(query="tomate", limit=25, offset=25))

    assert len(first.data["items"]) == 25
    assert len(second.data["items"]) == 25
    # Both pages report the full match count, and the pages do not overlap.
    assert first.data["matched"] == second.data["matched"] == 60
    assert not {i["plant_key"] for i in first.data["items"]} & {i["plant_key"] for i in second.data["items"]}


@pytest.mark.asyncio
async def test_list_plants_at_location_scans_beyond_the_page_limit():
    plants = [_Plant(f"p{i}", f"Anderswo {i}", location="loc-other") for i in range(120)]
    plants.append(_Plant("p-bed2", "Beet-2-Pflanze", location="loc-beet-2"))
    svc = _PlantService(plants)

    tool = ListPlantsAtLocation()
    resp = await tool.run(_ctx(plant_instance_service=svc), tool.Input(location_key="loc-beet-2"))
    assert [i["plant_key"] for i in resp.data["items"]] == ["p-bed2"]
