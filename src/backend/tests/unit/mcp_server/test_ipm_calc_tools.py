"""REQ-033 §2.1 — IPM catalogue tools and the fertiliser calculator.

Pins what would break quietly: that the Karenz reaches the caller, that a pest's
natural enemies come along with its treatments, that the inspection history
checks plant ownership, and that the calculator refuses a foreign fertiliser and
flags estimated EC contributions instead of presenting them as exact.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from app.common.enums import TenantRole
from app.common.exceptions import NotFoundError
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.ipm import (
    GetDisease,
    GetPest,
    GetPlantInspections,
    GetTreatment,
    ListDiseases,
    ListPests,
)
from app.mcp_server.tools.nutrient_calc import CalculateMixingProtocol, ListFertilizers


def _membership() -> McpTenantMembership:
    return McpTenantMembership(tenant_key="home", tenant_slug="home", tenant_name="Home", role=TenantRole.LEAD)


def _ctx(**services) -> ToolContext:
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, _membership(), services=services)


# ── Fakes ─────────────────────────────────────────────────────────────────────
class _Pest:
    def __init__(self, key, sci, common, de=None, symptoms="feine Gespinste"):
        self.key = key
        self.scientific_name = sci
        self.common_name = common
        self.common_name_de = de
        self.pest_type = "insect"
        self.lifecycle_days = 14
        self.optimal_temp_min = 20.0
        self.optimal_temp_max = 30.0
        self.description = "desc"
        self.description_de = None
        self.damage_symptoms = symptoms
        self.damage_symptoms_de = None
        self.detection_slug = "tetranychus"


class _Treatment:
    def __init__(self, key, name, *, karenz=0):
        self.key = key
        self.name = name
        self.name_de = None
        self.treatment_type = "biological"
        self.active_ingredient = None
        self.application_method = "spray"
        self.safety_interval_days = karenz
        self.dosage_per_liter = 2.0
        self.protective_equipment = ["gloves"]
        self.description = None
        self.description_de = None
        self.how_to_apply = None
        self.how_to_apply_de = None
        self.mode_of_action = None
        self.mode_of_action_de = None
        self.precautions = None
        self.precautions_de = None


class _Beneficial:
    def __init__(self, common, sci, preys_on=("tetranychus",)):
        self.common_name = common
        self.scientific_name = sci
        self.preys_on = list(preys_on)
        self.description = None


class _Disease:
    def __init__(self, key, sci, common):
        self.key = key
        self.scientific_name = sci
        self.common_name = common
        self.pathogen_type = "fungus"
        self.incubation_period_days = 7
        self.environmental_triggers = ["high_humidity"]
        self.affected_plant_parts = ["leaf"]
        self.description = None
        self.description_de = None


class _IpmService:
    def __init__(self, pests=None, diseases=None, detail=None, inspections=None):
        self._pests = pests or []
        self._diseases = diseases or []
        self._detail = detail
        self._inspections = inspections or []

    def list_pests(self, offset=0, limit=50):
        return self._pests, len(self._pests)

    def list_diseases(self, offset=0, limit=50):
        return self._diseases, len(self._diseases)

    def get_pest_detail(self, key):
        return self._detail

    def get_disease(self, key):
        for d in self._diseases:
            if d.key == key:
                return d
        raise NotFoundError("Disease", key)

    def get_treatment(self, key):
        return _Treatment(key, "Neem oil", karenz=3)

    def get_inspections(self, plant_key, offset=0, limit=50):
        return self._inspections, len(self._inspections)


class _Plant:
    def __init__(self, key, name):
        self.key = key
        self.plant_name = name
        self.instance_id = f"INST-{key}"


class _PlantService:
    def __init__(self, plants):
        self._plants = plants
        self.seen_tenant = None

    def get_plant(self, key, tenant_key=""):
        self.seen_tenant = tenant_key
        for p in self._plants:
            if p.key == key:
                return p
        raise NotFoundError("PlantInstance", key)


# ── IPM catalogue ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_list_pests_filters_on_damage_symptoms_too():
    # A user describes what they see, not the species name — the symptom text has
    # to be part of the haystack for that to resolve.
    svc = _IpmService(
        pests=[
            _Pest("pe1", "Tetranychus urticae", "Two-spotted spider mite", symptoms="feine Gespinste"),
            _Pest("pe2", "Aphis fabae", "Black bean aphid", symptoms="klebrige Blätter"),
        ]
    )
    resp = await ListPests().run(_ctx(ipm_service=svc), ListPests.Input(query="gespinste"))
    assert [i["pest_key"] for i in resp.data["items"]] == ["pe1"]


@pytest.mark.asyncio
async def test_get_pest_returns_treatments_and_natural_enemies():
    pest = _Pest("pe1", "Tetranychus urticae", "Two-spotted spider mite", de="Spinnmilbe")
    detail = {
        "pest": pest,
        "treatments": [_Treatment("t1", "Predatory mites"), _Treatment("t2", "Neem oil", karenz=3)],
        "beneficials": [_Beneficial("Predatory mite", "Phytoseiulus persimilis")],
        "detection_symptom_hint": "Feine Gespinste an Blattunterseiten",
    }
    resp = await GetPest().run(_ctx(ipm_service=_IpmService(detail=detail)), GetPest.Input(pest_key="pe1"))

    assert len(resp.data["treatments"]) == 2
    assert resp.data["beneficials"][0]["scientific_name"] == "Phytoseiulus persimilis"
    assert resp.data["detection_symptom_hint"]
    # The Karenz has to travel with the treatment — advice without it is unsafe.
    assert resp.data["treatments"][1]["safety_interval_days"] == 3


# ── The specialist has to lead the list (#1007) ───────────────────────────────
#
# Nothing in the stored order is factually wrong — every one of these does prey
# on spider mites. But a consumer that reads top-down, or truncates to the first
# entry, would release ladybirds against a spider-mite infestation: the wrong
# advice out of a record that holds the right answer.


def _spider_mite_detail(pest):
    """The seeded order from #1007: the two generalists ahead of the specialist."""

    return {
        "pest": pest,
        "treatments": [],
        "beneficials": [
            _Beneficial("Ladybird", "Coccinellidae", ["aphid", "spider_mite", "mealybug"]),
            _Beneficial("Green lacewing", "Chrysopidae", ["aphid", "spider_mite", "thrips_frankliniella"]),
            _Beneficial("Predatory mite", "Phytoseiidae", ["spider_mite", "thrips_frankliniella"]),
        ],
        "detection_symptom_hint": None,
    }


@pytest.mark.asyncio
async def test_beneficials_lead_with_the_specialist_not_the_generalist():
    pest = _Pest("8974", "Tetranychus urticae", "Two-spotted spider mite", de="Spinnmilbe")
    resp = await GetPest().run(
        _ctx(ipm_service=_IpmService(detail=_spider_mite_detail(pest))),
        GetPest.Input(pest_key="8974"),
    )

    assert [b["scientific_name"] for b in resp.data["beneficials"]] == [
        "Phytoseiidae",
        "Chrysopidae",
        "Coccinellidae",
    ]


@pytest.mark.asyncio
async def test_equally_specific_beneficials_keep_a_stable_order():
    # Ties are broken by scientific_name, so two identically specific enemies do
    # not swap places between two reads of the same record.
    pest = _Pest("8974", "Tetranychus urticae", "Two-spotted spider mite")
    detail = {
        "pest": pest,
        "treatments": [],
        "beneficials": [
            _Beneficial("Predatory midge", "Feltiella acarisuga", ["spider_mite"]),
            _Beneficial("Predatory mite", "Amblyseius andersoni", ["spider_mite"]),
        ],
        "detection_symptom_hint": None,
    }

    resp = await GetPest().run(_ctx(ipm_service=_IpmService(detail=detail)), GetPest.Input(pest_key="8974"))

    assert [b["scientific_name"] for b in resp.data["beneficials"]] == [
        "Amblyseius andersoni",
        "Feltiella acarisuga",
    ]


@pytest.mark.asyncio
async def test_get_treatment_states_the_karenz_in_the_summary():
    resp = await GetTreatment().run(_ctx(ipm_service=_IpmService()), GetTreatment.Input(treatment_key="t2"))
    assert resp.data["safety_interval_days"] == 3
    # A model may only read the summary, so the harvest gate belongs there too.
    assert "Karenz: 3 days" in resp.summary


@pytest.mark.asyncio
async def test_disease_lookup_round_trip():
    svc = _IpmService(diseases=[_Disease("di1", "Botrytis cinerea", "Grey mould")])
    listing = await ListDiseases().run(_ctx(ipm_service=svc), ListDiseases.Input(query="botrytis"))
    assert [i["disease_key"] for i in listing.data["items"]] == ["di1"]

    detail = await GetDisease().run(_ctx(ipm_service=svc), GetDisease.Input(disease_key="di1"))
    assert detail.data["pathogen_type"] == "fungus"
    assert detail.data["environmental_triggers"] == ["high_humidity"]


@pytest.mark.asyncio
async def test_plant_inspections_verify_ownership_first():
    class _Inspection:
        key = "i1"
        inspected_at = datetime(2026, 7, 1, 8, 0)
        pressure_level = "low"
        detected_pest_keys = ["pe1"]
        detected_disease_keys = []
        symptoms_observed = ["webbing"]
        # Legacy shape: an inspection written before ``findings`` existed carries
        # the attribute at all only because the model defaults it. The tool reads
        # it defensively, so a row from a raw dict must still pass.
        findings: list = []
        notes = None

    plants = _PlantService([_Plant("p1", "Tomate")])
    resp = await GetPlantInspections().run(
        _ctx(plant_instance_service=plants, ipm_service=_IpmService(inspections=[_Inspection()])),
        GetPlantInspections.Input(plant_key="p1"),
    )
    assert plants.seen_tenant == "home"
    assert resp.data["count"] == 1


# ── Fertiliser calculator ─────────────────────────────────────────────────────
class _Fert:
    def __init__(self, key, name, *, uncertain=False, tenant="home"):
        self.key = key
        self.product_name = name
        self.brand = "ACME"
        self.fertilizer_type = "base"
        self.is_organic = False
        self.tenant_key = tenant
        self.npk_ratio = (5.0, 2.0, 3.0)
        self.ec_contribution_per_ml = 0.2
        self.ec_contribution_uncertain = uncertain
        self.max_dose_ml_per_liter = 4.0


class _FertService:
    def __init__(self, ferts):
        self._ferts = {f.key: f for f in ferts}
        self.seen_tenant = None

    def list_fertilizers(self, offset=0, limit=50, filters=None, tenant_key=""):
        self.seen_tenant = tenant_key
        items = list(self._ferts.values())
        return items, len(items)

    def get_fertilizer(self, key, tenant_key=""):
        self.seen_tenant = tenant_key
        fert = self._ferts.get(key)
        if fert is None:
            raise NotFoundError("Fertilizer", key)
        return fert


@pytest.mark.asyncio
async def test_list_fertilizers_is_tenant_scoped_and_flags_uncertain_ec():
    svc = _FertService([_Fert("f1", "Grow A"), _Fert("f2", "Bloom B", uncertain=True)])
    resp = await ListFertilizers().run(_ctx(fertilizer_service=svc), ListFertilizers.Input())
    assert svc.seen_tenant == "home"
    flags = {i["product_name"]: i["ec_contribution_uncertain"] for i in resp.data["items"]}
    assert flags == {"Grow A": False, "Bloom B": True}


@pytest.mark.asyncio
async def test_mixing_protocol_computes_doses_and_reports_ec_net():
    svc = _FertService([_Fert("f1", "Grow A")])
    resp = await CalculateMixingProtocol().run(
        _ctx(fertilizer_service=svc),
        CalculateMixingProtocol.Input(
            fertilizer_keys=["f1"],
            target_volume_liters=10,
            target_ec_ms=1.6,
            base_water_ec=0.4,
        ),
    )
    # EC-net is the budget the fertilisers actually have to fill: 1.6 - 0.4.
    assert resp.data["ec_net"] == pytest.approx(1.2, abs=0.01)
    assert resp.data["dosages"]
    assert "instructions" in resp.data


@pytest.mark.asyncio
async def test_mixing_protocol_marks_the_result_as_an_estimate_for_uncertain_products():
    # An estimated EC contribution makes every derived dose an estimate. Saying so
    # in the summary matters: a model that only reads the summary would otherwise
    # present a guess as a precise figure.
    svc = _FertService([_Fert("f1", "Mystery Mix", uncertain=True)])
    resp = await CalculateMixingProtocol().run(
        _ctx(fertilizer_service=svc),
        CalculateMixingProtocol.Input(fertilizer_keys=["f1"], target_volume_liters=10, target_ec_ms=1.5),
    )
    assert resp.data["estimated_ec_products"] == ["Mystery Mix"]
    assert "estimate" in resp.summary.lower()


@pytest.mark.asyncio
async def test_mixing_protocol_refuses_a_foreign_fertilizer():
    svc = _FertService([_Fert("f1", "Grow A")])
    with pytest.raises(NotFoundError):
        await CalculateMixingProtocol().run(
            _ctx(fertilizer_service=svc),
            CalculateMixingProtocol.Input(
                fertilizer_keys=["f1", "someone-elses-product"],
                target_volume_liters=10,
                target_ec_ms=1.5,
            ),
        )
