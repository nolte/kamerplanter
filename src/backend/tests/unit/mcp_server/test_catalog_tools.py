"""REQ-033 §2.1 — seeded-catalogue read tools.

These exist so the seeded reference data can be inspected through MCP. The tests
pin what would make that useless: a species view that drops the very fields the
seeds carry, an empty-value filter that swallows meaningful ``False``/``0``, and
the tenant scoping on the two catalogues that have it.
"""

from __future__ import annotations

import pytest

from app.common.enums import TenantRole, ToxicitySeverity
from app.domain.models.species import Species, Toxicity
from app.domain.models.substrate import Substrate
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.catalogs import (
    ListHardinessZones,
    ListOverwinteringProfiles,
    ListPhaseDefinitions,
    ListStarterKits,
    ListSubstrates,
    SearchGlossary,
)
from app.mcp_server.tools.species import GetCultivar, GetSpeciesInfo, ListCultivars


def _membership() -> McpTenantMembership:
    return McpTenantMembership(tenant_key="home", tenant_slug="home", tenant_name="Home", role=TenantRole.LEAD)


def _ctx(**services) -> ToolContext:
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, _membership(), services=services)


class _Species:
    def __init__(self):
        self.key = "sp-tomato"
        self.scientific_name = "Solanum lycopersicum"
        self.common_names = ["Tomate"]
        self.synonyms = []
        self.genus = "Solanum"
        self.family_key = "fam-solanaceae"
        self.growth_habit = "herb"
        self.root_type = "fibrous"
        self.plant_category = "vegetable"
        self.description = "Nachtschattengewächs"
        self.native_habitat = ""
        self.direct_sow_months = [4, 5]
        self.harvest_months = [7, 8, 9]
        self.bloom_months = [6, 7]
        self.pruning_months = []
        self.sowing_indoor_weeks_before_last_frost = 6
        self.sowing_outdoor_after_last_frost_days = 14
        self.harvest_from_year = None
        self.bloom_from_year = None
        self.hardiness_zones = ["9a"]
        self.frost_sensitivity = "sensitive"
        self.base_temp = 10.0
        self.nutrient_demand_level = "high"
        self.green_manure_suitable = False
        # The real shape: ``Species.toxicity`` is a ``Toxicity`` object, while
        # ``toxicity_severity`` is the flat legacy passthrough on a *different*
        # scale. A string here would be a shape the model cannot hold, and the
        # assertions built on it would certify nothing.
        self.toxicity = Toxicity(is_toxic_cats=True, toxic_compounds=["solanine"], severity=ToxicitySeverity.MODERATE)
        self.toxicity_severity = "low"
        self.allergen_info = None
        self.allows_harvest = True
        self.harvest_pattern = "repeat"
        self.traits = ["determinate"]
        self.growing_periods = []
        self.seed_profile = None


class _Cultivar:
    def __init__(self, key="cv-1", name="San Marzano"):
        self.key = key
        self.name = name
        self.species_key = "sp-tomato"
        self.breeder = "Heirloom"
        self.breeding_year = 1926
        self.traits = ["plum"]
        self.seed_type = "open_pollinated"
        self.days_to_maturity = 80
        self.dtm_reference = "transplant"


class _SpeciesService:
    def __init__(self, cultivars=None, companions=None):
        self._cultivars = cultivars or []
        self._companions = companions or []

    def get_species(self, key):
        return _Species()

    def get_compatible_species(self, key):
        return self._companions

    def list_cultivars(self, species_key):
        return self._cultivars

    def get_cultivar(self, key):
        return _Cultivar(key=key)


# ── Stage 1: species detail and cultivars ─────────────────────────────────────
@pytest.mark.asyncio
async def test_species_info_returns_the_seeded_detail_not_just_a_name():
    # The whole point: before this, the tool returned five fields and the seeded
    # timing/hardiness/toxicity content was invisible through MCP.
    svc = _SpeciesService(companions=[{"species_key": "sp-basil"}])
    resp = await GetSpeciesInfo().run(_ctx(species_service=svc), GetSpeciesInfo.Input(species_key="sp-tomato"))

    for field in (
        "direct_sow_months",
        "harvest_months",
        "sowing_indoor_weeks_before_last_frost",
        "hardiness_zones",
        "frost_sensitivity",
        "nutrient_demand_level",
        "toxicity",
        "harvest_pattern",
    ):
        assert field in resp.data, f"{field} missing from species detail"
    assert resp.data["compatible_companions"]


@pytest.mark.asyncio
async def test_species_info_keeps_meaningful_false_and_zero():
    # green_manure_suitable=False is an answer, not a missing value — a naive
    # truthiness filter would delete exactly the fields a verifier cares about.
    resp = await GetSpeciesInfo().run(
        _ctx(species_service=_SpeciesService()), GetSpeciesInfo.Input(species_key="sp-tomato")
    )
    assert resp.data["green_manure_suitable"] is False
    assert resp.data["allows_harvest"] is True


@pytest.mark.asyncio
async def test_species_info_embeds_cultivars_and_can_omit_them():
    svc = _SpeciesService(cultivars=[_Cultivar()])
    with_cv = await GetSpeciesInfo().run(_ctx(species_service=svc), GetSpeciesInfo.Input(species_key="sp-tomato"))
    assert with_cv.data["cultivars"][0]["name"] == "San Marzano"

    without = await GetSpeciesInfo().run(
        _ctx(species_service=svc), GetSpeciesInfo.Input(species_key="sp-tomato", include_cultivars=False)
    )
    assert "cultivars" not in without.data


@pytest.mark.asyncio
async def test_species_info_survives_a_missing_companion_graph():
    class _Broken(_SpeciesService):
        def get_compatible_species(self, key):
            raise RuntimeError("graph unavailable")

    resp = await GetSpeciesInfo().run(_ctx(species_service=_Broken()), GetSpeciesInfo.Input(species_key="sp-tomato"))
    assert resp.data["scientific_name"] == "Solanum lycopersicum"


@pytest.mark.asyncio
async def test_cultivar_tools_round_trip():
    svc = _SpeciesService(cultivars=[_Cultivar()])
    listing = await ListCultivars().run(_ctx(species_service=svc), ListCultivars.Input(species_key="sp-tomato"))
    assert listing.data["count"] == 1

    detail = await GetCultivar().run(_ctx(species_service=svc), GetCultivar.Input(cultivar_key="cv-1"))
    assert detail.data["days_to_maturity"] == 80
    assert detail.data["seed_type"] == "open_pollinated"


# ── An omitted safety field must not read as a clearance (#1005) ──────────────
#
# ``_drop_empty`` makes a sparse record read as sparse, which is the right answer
# for almost every field. For toxicity it is the wrong one: a consumer cannot
# tell "no toxicity data" from "not toxic", so the absence reads as a safety
# clearance nobody gave. The tests below pin the carve-out *and* the philosophy
# it is carved out of.


class _UnresearchedSpeciesService:
    """Serves the record shape #1005 was filed against: identified, unresearched.

    Built from the real :class:`Species` model rather than a hand-rolled stub, so
    the assertions cannot pass against a field shape the model does not have.
    """

    def get_species(self, key):
        return Species(_key="11441306", scientific_name="Dracaena reflexa", genus="Dracaena")

    def get_compatible_species(self, key):
        return []

    def list_cultivars(self, species_key):
        return []


@pytest.mark.asyncio
async def test_an_unresearched_toxicity_is_reported_as_null_rather_than_omitted():
    resp = await GetSpeciesInfo().run(
        _ctx(species_service=_UnresearchedSpeciesService()),
        GetSpeciesInfo.Input(species_key="11441306"),
    )

    for field in ("toxicity", "toxicity_severity", "allergen_info", "allows_harvest"):
        assert field in resp.data, f"{field} was omitted — its absence would read as a negative answer"
    assert resp.data["toxicity"] is None
    assert resp.data["toxicity_severity"] is None
    assert resp.data["allergen_info"] is None


@pytest.mark.asyncio
async def test_the_safety_carve_out_leaves_the_rest_of_the_record_sparse():
    # The #949 property: a sparse record reads as sparse, and that is itself the
    # answer to "is this record complete?". Turning every field into an explicit
    # null would destroy it, so the carve-out must stay a carve-out.
    resp = await GetSpeciesInfo().run(
        _ctx(species_service=_UnresearchedSpeciesService()),
        GetSpeciesInfo.Input(species_key="11441306"),
    )

    for field in ("plant_category", "bloom_months", "harvest_months", "hardiness_zones", "frost_sensitivity"):
        assert field not in resp.data, f"{field} is not safety-critical and must stay omitted when unpopulated"


@pytest.mark.asyncio
async def test_the_populated_field_count_does_not_count_the_safety_nulls():
    # The summary is the part an LLM may read alone. Counting the explicit nulls
    # as "populated" would make the response claim more than the record says —
    # the same failure class the carve-out is meant to end.
    resp = await GetSpeciesInfo().run(
        _ctx(species_service=_UnresearchedSpeciesService()),
        GetSpeciesInfo.Input(species_key="11441306"),
    )

    populated = sum(1 for value in resp.data.values() if value is not None)
    assert f"{populated} populated fields" in resp.summary
    assert populated < len(resp.data), "the safety nulls are present but must not be counted"


# ── Stage 2: the remaining catalogues ─────────────────────────────────────────
class _Named:
    """Minimal stand-in for a seeded entity with a name."""

    def __init__(self, name):
        self.name = name

    def model_dump(self):
        return {"name": self.name}


@pytest.mark.asyncio
async def test_list_substrates_filters_by_name():
    # Real ``Substrate`` records, not name-carrying stubs: the model has
    # ``name_de``/``name_en`` and no ``name`` at all, so a filter written against
    # ``name`` matches nothing while a stub with a ``name`` attribute would let
    # that pass (#1006, same root cause as the get_plant join).
    class _Svc:
        def list_substrates(self, offset=0, limit=50):
            return [
                Substrate(_key="s1", name_de="Kokos", name_en="Coco coir"),
                Substrate(_key="s2", name_de="Perlite", name_en="Perlite"),
            ], 2

    resp = await ListSubstrates().run(_ctx(substrate_service=_Svc()), ListSubstrates.Input(query="koko"))
    assert [i["name_de"] for i in resp.data["items"]] == ["Kokos"]

    # The English name is part of the haystack too — the palette answers in both.
    english = await ListSubstrates().run(_ctx(substrate_service=_Svc()), ListSubstrates.Input(query="coco"))
    assert [i["name_de"] for i in english.data["items"]] == ["Kokos"]


@pytest.mark.asyncio
async def test_overwintering_profiles_are_tenant_scoped():
    class _Svc:
        def __init__(self):
            self.seen = None

        def list_profiles(self, tenant_key, offset=0, limit=50):
            self.seen = tenant_key
            return [_Named("Kübel frostfrei")], 1

    svc = _Svc()
    resp = await ListOverwinteringProfiles().run(
        _ctx(overwintering_profile_service=svc), ListOverwinteringProfiles.Input()
    )
    assert svc.seen == "home"
    assert resp.data["count"] == 1


@pytest.mark.asyncio
async def test_starter_kits_are_tenant_scoped_and_filterable():
    class _Svc:
        def __init__(self):
            self.seen = None

        def list_kits_for_tenant(self, tenant_key, difficulty=None):
            self.seen = (tenant_key, difficulty)
            return [_Named("Indoor-Tomate")]

    svc = _Svc()
    await ListStarterKits().run(_ctx(starter_kit_service=svc), ListStarterKits.Input(difficulty="beginner"))
    assert svc.seen == ("home", "beginner")


@pytest.mark.asyncio
async def test_phase_definitions_and_hardiness_zones_are_global():
    class _Phase:
        def list_definitions(self, offset=0, limit=50, name_filter=None):
            return [_Named("Standard Gemüse")], 1

    class _Zones:
        def list_zones(self):
            return [_Named("8a"), _Named("9a")]

    phases = await ListPhaseDefinitions().run(_ctx(phase_sequence_service=_Phase()), ListPhaseDefinitions.Input())
    assert phases.data["count"] == 1
    # No tenant argument on these — they are global reference data.
    assert not ListPhaseDefinitions().tenant_scoped
    assert not ListHardinessZones().tenant_scoped

    zones = await ListHardinessZones().run(_ctx(hardiness_zone_service=_Zones()), ListHardinessZones.Input())
    assert zones.data["count"] == 2


@pytest.mark.asyncio
async def test_glossary_search_filters_and_passes_the_language_through():
    class _Term:
        def __init__(self, slug, label):
            self.slug = slug
            self.label = label
            self.category = "domain"

    class _Svc:
        def __init__(self):
            self.seen = None

        def list_terms(self, *, category=None, language="de"):
            self.seen = (category, language)
            return [_Term("vpd", "Dampfdruckdefizit"), _Term("ec", "Leitfähigkeit")]

    svc = _Svc()
    resp = await SearchGlossary().run(_ctx(glossary_service=svc), SearchGlossary.Input(query="vpd", language="en"))
    assert svc.seen == (None, "en")
    assert [i["slug"] for i in resp.data["items"]] == ["vpd"]
