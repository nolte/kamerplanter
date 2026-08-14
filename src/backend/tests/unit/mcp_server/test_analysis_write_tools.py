"""REQ-033 §2 — the five tools the external analysis processes were blocked on.

``record_feeding_event``, ``get_plant_diagnostics``, ``create_inspection``,
``search_plant_knowledge`` and ``assign_nutrient_plan`` (issue #931).

What is pinned here is what would break quietly:

* that a dose is persisted as **numbers** rather than as the boolean the care log
  offered — undersupply and oversupply have opposite corrections;
* that the diagnostics aggregate reports a **direction** of drift and keeps tank
  and runoff EC apart, since reading one as the other inverts the conclusion;
* that an agent's finding survives into an inspection **with** its confidence and
  plant part, and comes back out through the read tool;
* that a knowledge hit stays **citable** and that an outage is reported rather
  than answered as "nothing found";
* that every one of them checks tenant ownership on the dry-run path too, so a
  preview cannot approve a call the write would refuse.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import PestPressureLevel, PlantPart, TenantRole
from app.common.exceptions import NotFoundError
from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError
from app.domain.interfaces.knowledge_service import KnowledgeChunk
from app.domain.models.feeding_event import FeedingEvent
from app.domain.models.ipm import Inspection
from app.mcp_server.base import McpToolError
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.tools.diagnostics import GetPlantDiagnostics
from app.mcp_server.tools.feeding import RecordFeedingEvent
from app.mcp_server.tools.ipm import CreateInspection, GetPlantInspections
from app.mcp_server.tools.knowledge import DEFAULT_EXCERPT_CHARS, SearchPlantKnowledge
from app.mcp_server.tools.nutrition import AssignNutrientPlan

TENANT = "home"


def _membership() -> McpTenantMembership:
    return McpTenantMembership(tenant_key=TENANT, tenant_slug=TENANT, tenant_name="Home", role=TenantRole.LEAD)


def _ctx(**services) -> ToolContext:
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, _membership(), services=services)


def _global_ctx(**services) -> ToolContext:
    """A context with **no** membership — what the dispatcher builds for a global tool."""

    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, None, services=services)


# ── Fakes ─────────────────────────────────────────────────────────────────────
class _Plant:
    def __init__(self, key="p1", *, location_key="loc-1"):
        self.key = key
        self.plant_name = "Tomate"
        self.instance_id = f"INST-{key}"
        self.species_key = "solanum-lycopersicum"
        self.cultivar_key = None
        self.location_key = location_key
        self.substrate_key = "sub-1"
        self.current_phase_key = "flowering"


class _PlantService:
    def __init__(self, plants=None):
        self._plants = {p.key: p for p in (plants or [_Plant()])}
        self.seen_tenant = None

    def get_plant(self, key, tenant_key=""):
        self.seen_tenant = tenant_key
        plant = self._plants.get(key)
        if plant is None:
            raise NotFoundError("PlantInstance", key)
        return plant


class _Fert:
    def __init__(self, key, name):
        self.key = key
        self.product_name = name


class _FertService:
    def __init__(self, ferts=()):
        self._ferts = {f.key: f for f in ferts}
        self.seen_tenant = None

    def get_fertilizer(self, key, tenant_key=""):
        self.seen_tenant = tenant_key
        fert = self._ferts.get(key)
        if fert is None:
            raise NotFoundError("Fertilizer", key)
        return fert


class _FeedingService:
    def __init__(self, events=()):
        self.created: list[FeedingEvent] = []
        self._events = list(events)
        self.seen_tenant = None
        self.seen_plant = None

    def create_event(self, event: FeedingEvent) -> FeedingEvent:
        stored = event.model_copy(update={"key": f"fe-{len(self.created) + 1}"})
        if stored.timestamp is None:
            stored.timestamp = datetime.now(UTC)
        self.created.append(stored)
        return stored

    def get_by_plant(self, plant_key, offset=0, limit=50, *, tenant_key):
        self.seen_tenant = tenant_key
        self.seen_plant = plant_key
        return list(self._events)


class _IpmService:
    def __init__(self, *, pests=(), diseases=(), inspections=(), karenz=(), harvest_ok=True):
        self._pests = set(pests)
        self._diseases = set(diseases)
        self._inspections = list(inspections)
        self._karenz = list(karenz)
        self._harvest_ok = harvest_ok
        self.created: list[Inspection] = []

    def get_pest(self, key):
        if key not in self._pests:
            raise NotFoundError("Pest", key)
        return object()

    def get_disease(self, key):
        if key not in self._diseases:
            raise NotFoundError("Disease", key)
        return object()

    def create_inspection(self, plant_key, inspection: Inspection) -> Inspection:
        inspection.plant_key = plant_key
        stored = inspection.model_copy(update={"key": f"insp-{len(self.created) + 1}"})
        if stored.inspected_at is None:
            stored.inspected_at = datetime.now(UTC)
        self.created.append(stored)
        return stored

    def get_inspections(self, plant_key, offset=0, limit=50):
        return list(self._inspections), len(self._inspections)

    def check_harvest_safety(self, plant_key, planned_date=None):
        return self._harvest_ok, list(self._karenz)


class _CareService:
    def __init__(self, entries=()):
        self._entries = list(entries)

    def get_confirmation_history(self, plant_key, reminder_type, limit=50):
        return list(self._entries)


class _Confirmation:
    def __init__(self, at, reminder_type="watering"):
        self.confirmed_at = at
        self.reminder_type = reminder_type
        self.action = "confirmed"
        self.notes = None


class _Sensor:
    def __init__(self, key, metric_type, name="Probe"):
        self.key = key
        self.name = name
        self.metric_type = metric_type
        self.unit_of_measurement = "mS/cm" if metric_type == "ec_ms" else None


class _SensorService:
    def __init__(self, sensors=()):
        self._sensors = list(sensors)
        self.seen_location = None

    def get_sensors_for_location(self, location_key):
        self.seen_location = location_key
        return list(self._sensors)


class _Reading:
    def __init__(self, value, at, source="mqtt"):
        self.value = value
        self.time = at
        self.source = source


class _ObservationService:
    def __init__(self, readings=None, *, available=True):
        self._readings = readings or {}
        self._available = available
        self.seen_tenants: list[str] = []

    def is_available(self):
        return self._available

    def get_latest_reading(self, sensor_key, tenant_key):
        self.seen_tenants.append(tenant_key)
        return self._readings.get(sensor_key)


class _Plan:
    def __init__(self, key, name, *, tenant_key=TENANT):
        self.key = key
        self.name = name
        self.description = None
        self.is_template = False
        self.tenant_key = tenant_key
        self.recommended_substrate_type = "soil"
        self.version = 1
        self.tags = ["outdoor"]


class _NutrientPlanService:
    def __init__(self, plans=(), *, current=None):
        self._plans = {p.key: p for p in plans}
        self._current = current
        self.assignments: list[tuple[str, str, str]] = []
        self.seen_tenants: list[str] = []

    def get_plan(self, key, tenant_key="", *, for_write=False):
        self.seen_tenants.append(tenant_key)
        plan = self._plans.get(key)
        if plan is None:
            raise NotFoundError("NutrientPlan", key)
        return plan

    def get_plant_plan(self, plant_key, *, tenant_key):
        self.seen_tenants.append(tenant_key)
        return self._current

    def assign_to_plant(self, plant_key, plan_key, assigned_by="", *, tenant_key):
        # `tenant_key` is required and keyword-only since #950, and this double
        # did not follow. Four tests here drove `execute` and stayed green while
        # the real call site raised `TypeError` on every non-dry-run call (#1145)
        # — the double modelled a contract the service had stopped offering.
        # `test_mcp_service_doubles_match_their_service.py` now derives that
        # agreement from the real signature instead of trusting this line.
        self.seen_tenants.append(tenant_key)
        self.assignments.append((plant_key, plan_key, assigned_by))
        self._current = self._plans[plan_key]
        return {"_key": "edge-1"}


class _KnowledgeService:
    def __init__(self, chunks=(), *, error=None):
        self._chunks = list(chunks)
        self._error = error
        self.calls: list[dict] = []

    async def search(self, query, *, top_k=5, doc_language=None):
        self.calls.append({"query": query, "top_k": top_k, "doc_language": doc_language})
        if self._error is not None:
            raise self._error
        return list(self._chunks)


def _feeding(
    key: str,
    *,
    at: datetime,
    ec_before=None,
    ec_after=None,
    ph_before=None,
    ph_after=None,
    runoff_ec=None,
    runoff_ph=None,
) -> FeedingEvent:
    return FeedingEvent(
        _key=key,
        tenant_key=TENANT,
        plant_key="p1",
        timestamp=at,
        volume_applied_liters=2.0,
        measured_ec_before=ec_before,
        measured_ec_after=ec_after,
        measured_ph_before=ph_before,
        measured_ph_after=ph_after,
        runoff_ec=runoff_ec,
        runoff_ph=runoff_ph,
    )


# ── record_feeding_event ──────────────────────────────────────────────────────
class TestRecordFeedingEvent:
    @pytest.mark.asyncio
    async def test_persists_amount_ec_ph_and_tank_reference(self):
        # The whole point of the tool: the care log's action="confirmed" is a
        # boolean, and a dosage decision needs the numbers.
        feeding = _FeedingService()
        resp = await RecordFeedingEvent().execute(
            _ctx(
                plant_instance_service=_PlantService(),
                fertilizer_service=_FertService([_Fert("f1", "Grow A")]),
                feeding_service=feeding,
            ),
            RecordFeedingEvent.Input(
                plant_key="p1",
                volume_applied_liters=2.5,
                fertilizers_used=[{"fertilizer_key": "f1", "ml_applied": 5.0}],
                measured_ec_before=1.6,
                measured_ph_before=6.1,
                runoff_ec=2.4,
                runoff_ph=5.8,
                runoff_volume_liters=0.4,
                tank_fill_event_key="tfe-9",
            ),
        )

        stored = feeding.created[0]
        assert stored.tenant_key == TENANT
        assert stored.volume_applied_liters == 2.5
        assert stored.measured_ec_before == 1.6
        assert stored.measured_ph_before == 6.1
        assert stored.runoff_ec == 2.4
        assert stored.tank_fill_event_key == "tfe-9"
        assert stored.fertilizers_used[0].ml_applied == 5.0

        assert resp.data["feeding_event_key"] == "fe-1"
        # Tank EC and runoff EC stay separate keys; conflating them inverts the
        # accumulation reading.
        assert resp.data["measured_ec_before"] == 1.6
        assert resp.data["runoff_ec"] == 2.4

    @pytest.mark.asyncio
    async def test_dry_run_checks_ownership_and_persists_nothing(self):
        plants = _PlantService()
        feeding = _FeedingService()
        resp = await RecordFeedingEvent().preview(
            _ctx(
                plant_instance_service=plants,
                fertilizer_service=_FertService([_Fert("f1", "Grow A")]),
                feeding_service=feeding,
            ),
            RecordFeedingEvent.Input(
                plant_key="p1",
                volume_applied_liters=1.0,
                fertilizers_used=[{"fertilizer_key": "f1", "ml_applied": 2.0}],
            ),
        )
        assert plants.seen_tenant == TENANT
        assert feeding.created == []
        assert resp.data["fertilizers_used"][0]["product_name"] == "Grow A"

    @pytest.mark.asyncio
    async def test_refuses_a_foreign_plant(self):
        with pytest.raises(NotFoundError):
            await RecordFeedingEvent().execute(
                _ctx(
                    plant_instance_service=_PlantService(),
                    fertilizer_service=_FertService(),
                    feeding_service=_FeedingService(),
                ),
                RecordFeedingEvent.Input(plant_key="someone-elses-plant", volume_applied_liters=1.0),
            )

    @pytest.mark.asyncio
    async def test_refuses_a_foreign_fertilizer_before_writing(self):
        # A dangling feeding_used edge to another tenant's product would survive
        # in the graph; the write must not happen at all.
        feeding = _FeedingService()
        with pytest.raises(NotFoundError):
            await RecordFeedingEvent().execute(
                _ctx(
                    plant_instance_service=_PlantService(),
                    fertilizer_service=_FertService([_Fert("f1", "Grow A")]),
                    feeding_service=feeding,
                ),
                RecordFeedingEvent.Input(
                    plant_key="p1",
                    volume_applied_liters=1.0,
                    fertilizers_used=[{"fertilizer_key": "not-mine", "ml_applied": 1.0}],
                ),
            )
        assert feeding.created == []

    @pytest.mark.asyncio
    async def test_rejects_a_non_positive_volume(self):
        # "0 litres applied" is not a feeding; the model bound is what stops it
        # entering the trend as a real data point.
        with pytest.raises(ValueError, match="volume_applied_liters"):
            RecordFeedingEvent.Input(plant_key="p1", volume_applied_liters=0)


# ── get_plant_diagnostics ─────────────────────────────────────────────────────
class TestGetPlantDiagnostics:
    @staticmethod
    def _diag_ctx(**overrides):
        now = datetime.now(UTC)
        defaults = {
            "plant_instance_service": _PlantService(),
            "feeding_service": _FeedingService(
                [
                    _feeding("fe-3", at=now - timedelta(days=1), ec_before=1.8, ph_before=6.0, runoff_ec=2.9),
                    _feeding("fe-2", at=now - timedelta(days=4), ec_before=1.6, ph_before=6.0, runoff_ec=2.2),
                    _feeding("fe-1", at=now - timedelta(days=8), ec_before=1.4, ph_before=6.0, runoff_ec=1.5),
                ]
            ),
            "ipm_service": _IpmService(),
            "care_reminder_service": _CareService(),
            "sensor_service": _SensorService(),
            "observation_service": _ObservationService(available=False),
        }
        defaults.update(overrides)
        return _ctx(**defaults)

    @pytest.mark.asyncio
    async def test_reports_the_direction_of_ec_drift_not_only_the_latest_value(self):
        # AC-5's reason for existing: a single reading cannot tell a rising salt
        # load from a stable one.
        resp = await GetPlantDiagnostics().run(
            self._diag_ctx(),
            GetPlantDiagnostics.Input(plant_key="p1", window_days=14),
        )
        ec_input = resp.data["ec_ph_trend"]["ec"]["input"]
        assert ec_input["sample_count"] == 3
        assert ec_input["first"] == 1.4
        assert ec_input["latest"] == 1.8
        assert ec_input["delta"] == pytest.approx(0.4)
        assert ec_input["direction"] == "rising"
        # Newest first, like every other list in the palette.
        assert ec_input["samples"][0]["value"] == 1.8

    @pytest.mark.asyncio
    async def test_runoff_and_tank_ec_are_separate_series(self):
        resp = await GetPlantDiagnostics().run(self._diag_ctx(), GetPlantDiagnostics.Input(plant_key="p1"))
        ec = resp.data["ec_ph_trend"]["ec"]
        assert ec["input"]["latest"] == 1.8
        assert ec["runoff"]["latest"] == 2.9
        # Runoff above input is accumulation — a recipe that read them as one
        # series would see a single, meaningless line.
        assert ec["runoff"]["latest"] > ec["input"]["latest"]
        assert "Runoff EC rising" in resp.summary

    @pytest.mark.asyncio
    async def test_a_flat_series_is_stable_not_a_manufactured_trend(self):
        # pH is identical across all three feedings; a "rising" here would be
        # noise dressed up as a finding.
        resp = await GetPlantDiagnostics().run(self._diag_ctx(), GetPlantDiagnostics.Input(plant_key="p1"))
        assert resp.data["ec_ph_trend"]["ph"]["input"]["direction"] == "stable"

    @pytest.mark.asyncio
    async def test_an_empty_series_is_unknown_and_keeps_every_key(self):
        resp = await GetPlantDiagnostics().run(
            self._diag_ctx(feeding_service=_FeedingService()),
            GetPlantDiagnostics.Input(plant_key="p1"),
        )
        after = resp.data["ec_ph_trend"]["ec"]["after"]
        assert after == {
            "sample_count": 0,
            "first": None,
            "first_at": None,
            "latest": None,
            "latest_at": None,
            "delta": None,
            "direction": "unknown",
            "samples": [],
        }
        assert "No EC measurements recorded" in resp.summary

    @pytest.mark.asyncio
    async def test_the_window_excludes_older_feedings(self):
        now = datetime.now(UTC)
        ctx = self._diag_ctx(
            feeding_service=_FeedingService(
                [
                    _feeding("recent", at=now - timedelta(days=2), ec_before=1.5),
                    _feeding("ancient", at=now - timedelta(days=90), ec_before=0.9),
                ]
            )
        )
        resp = await GetPlantDiagnostics().run(ctx, GetPlantDiagnostics.Input(plant_key="p1", window_days=7))
        assert [e["feeding_event_key"] for e in resp.data["feeding_events"]] == ["recent"]
        assert resp.data["ec_ph_trend"]["ec"]["input"]["sample_count"] == 1

    @pytest.mark.asyncio
    async def test_feeding_history_is_read_inside_the_acting_tenant(self):
        feeding = _FeedingService()
        await GetPlantDiagnostics().run(
            self._diag_ctx(feeding_service=feeding),
            GetPlantDiagnostics.Input(plant_key="p1"),
        )
        # #927: the tenant predicate is in the query, not in this call site's
        # memory — but the call site still has to pass the acting tenant.
        assert feeding.seen_tenant == TENANT

    @pytest.mark.asyncio
    async def test_karenz_is_reported_and_never_windowed_away(self):
        # A treatment applied three months ago whose Karenz still runs must still
        # block; hiding it behind window_days would make the harvest gate depend
        # on how the caller sized the window.
        ipm = _IpmService(
            harvest_ok=False,
            karenz=[
                {
                    "treatment_name": "Spruzit",
                    "active_ingredient": "pyrethrin",
                    "applied_at": "2026-05-01T00:00:00Z",
                    "safety_interval_days": 120,
                    "safe_date": "2026-08-29T00:00:00Z",
                }
            ],
        )
        resp = await GetPlantDiagnostics().run(
            self._diag_ctx(ipm_service=ipm),
            GetPlantDiagnostics.Input(plant_key="p1", window_days=1),
        )
        assert resp.data["karenz"]["harvest_allowed"] is False
        assert resp.data["karenz"]["active_periods"][0]["treatment_name"] == "Spruzit"
        # A model may read only the summary; the harvest gate belongs there.
        assert "Harvest BLOCKED" in resp.summary

    @pytest.mark.asyncio
    async def test_missing_timeseries_backend_is_not_reported_as_no_readings(self):
        resp = await GetPlantDiagnostics().run(
            self._diag_ctx(
                sensor_service=_SensorService([_Sensor("s1", "ec_ms")]),
                observation_service=_ObservationService(available=False),
            ),
            GetPlantDiagnostics.Input(plant_key="p1"),
        )
        assert resp.data["sensors"]["available"] is False
        assert resp.data["sensors"]["reason"] == "timeseries_unavailable"
        assert resp.data["sensors"]["items"] == []

    @pytest.mark.asyncio
    async def test_sensor_readings_are_read_inside_the_acting_tenant(self):
        now = datetime.now(UTC)
        observations = _ObservationService({"s1": _Reading(2.1, now)})
        sensors = _SensorService([_Sensor("s1", "ec_ms")])
        resp = await GetPlantDiagnostics().run(
            self._diag_ctx(sensor_service=sensors, observation_service=observations),
            GetPlantDiagnostics.Input(plant_key="p1"),
        )
        # Sensors carry no tenant of their own; the binding is the resolved
        # plant's location plus the tenant filter on the readings.
        assert sensors.seen_location == "loc-1"
        assert observations.seen_tenants == [TENANT]
        assert resp.data["sensors"]["items"][0]["value"] == 2.1
        assert resp.data["ec_ph_trend"]["ec"]["sensor"]["sample_count"] == 1

    @pytest.mark.asyncio
    async def test_a_plant_without_a_location_reports_why(self):
        resp = await GetPlantDiagnostics().run(
            self._diag_ctx(plant_instance_service=_PlantService([_Plant(location_key=None)])),
            GetPlantDiagnostics.Input(plant_key="p1"),
        )
        assert resp.data["sensors"]["reason"] == "plant_has_no_location"

    @pytest.mark.asyncio
    async def test_care_events_and_inspections_travel_in_the_same_answer(self):
        # AC-5: one call, not five round-trips.
        now = datetime.now(UTC)
        inspection = Inspection(
            _key="i1",
            plant_key="p1",
            inspected_at=now - timedelta(days=2),
            pressure_level=PestPressureLevel.LOW,
            symptoms_observed=["webbing"],
        )
        resp = await GetPlantDiagnostics().run(
            self._diag_ctx(
                ipm_service=_IpmService(inspections=[inspection]),
                care_reminder_service=_CareService([_Confirmation(now - timedelta(days=1))]),
            ),
            GetPlantDiagnostics.Input(plant_key="p1"),
        )
        assert resp.data["inspections"][0]["symptoms_observed"] == ["webbing"]
        assert resp.data["care_events"][0]["reminder_type"] == "watering"
        assert resp.data["feeding_events"]
        assert resp.data["karenz"]["harvest_allowed"] is True

    @pytest.mark.asyncio
    async def test_refuses_a_foreign_plant(self):
        with pytest.raises(NotFoundError):
            await GetPlantDiagnostics().run(
                self._diag_ctx(),
                GetPlantDiagnostics.Input(plant_key="someone-elses-plant"),
            )

    def test_window_is_bounded(self):
        with pytest.raises(ValueError, match="window_days"):
            GetPlantDiagnostics.Input(plant_key="p1", window_days=5000)


# ── create_inspection ─────────────────────────────────────────────────────────
class TestCreateInspection:
    @pytest.mark.asyncio
    async def test_a_finding_keeps_its_confidence_and_plant_part(self):
        # The AC in so many words: an analysis result becomes an inspection
        # without lossy remapping.
        ipm = _IpmService(pests={"tetranychus-urticae"})
        resp = await CreateInspection().execute(
            _ctx(plant_instance_service=_PlantService(), ipm_service=ipm),
            CreateInspection.Input(
                plant_key="p1",
                pressure_level=PestPressureLevel.MEDIUM,
                findings=[
                    {
                        "symptom": "Feine Gespinste an den Blattunterseiten",
                        "confidence": 0.82,
                        "affected_plant_part": "leaf",
                        "pest_key": "tetranychus-urticae",
                        "rationale": "Sprenkelung plus Gespinst.",
                    }
                ],
            ),
        )
        stored = ipm.created[0]
        assert stored.tenant_key == TENANT
        assert stored.findings[0].confidence == 0.82
        assert stored.findings[0].affected_plant_part == PlantPart.LEAF
        assert resp.data["findings"][0]["affected_plant_part"] == "leaf"

    @pytest.mark.asyncio
    async def test_findings_are_mirrored_into_the_flat_symptom_list(self):
        # symptoms_observed stays the canonical list every existing reader (the
        # UI included) uses; an agent filling only `findings` must not produce a
        # row that looks empty to them.
        ipm = _IpmService(pests={"pe1"}, diseases={"di1"})
        await CreateInspection().execute(
            _ctx(plant_instance_service=_PlantService(), ipm_service=ipm),
            CreateInspection.Input(
                plant_key="p1",
                symptoms_observed=["gelbe Blattraender"],
                findings=[
                    {"symptom": "Feine Gespinste", "pest_key": "pe1"},
                    {"symptom": "Grauschimmel", "disease_key": "di1"},
                ],
            ),
        )
        stored = ipm.created[0]
        assert stored.symptoms_observed == ["gelbe Blattraender", "Feine Gespinste", "Grauschimmel"]
        assert stored.detected_pest_keys == ["pe1"]
        assert stored.detected_disease_keys == ["di1"]

    @pytest.mark.asyncio
    async def test_duplicate_catalogue_keys_are_collapsed(self):
        ipm = _IpmService(pests={"pe1"})
        await CreateInspection().execute(
            _ctx(plant_instance_service=_PlantService(), ipm_service=ipm),
            CreateInspection.Input(
                plant_key="p1",
                detected_pest_keys=["pe1"],
                findings=[{"symptom": "Gespinste", "pest_key": "pe1"}],
            ),
        )
        assert ipm.created[0].detected_pest_keys == ["pe1"]

    @pytest.mark.asyncio
    async def test_an_unknown_pest_key_fails_before_the_write(self):
        # The repository wires a detected_pest edge without looking; an unchecked
        # key becomes a dangling edge every later traversal steps over.
        ipm = _IpmService(pests={"pe1"})
        with pytest.raises(NotFoundError):
            await CreateInspection().execute(
                _ctx(plant_instance_service=_PlantService(), ipm_service=ipm),
                CreateInspection.Input(plant_key="p1", detected_pest_keys=["invented-pest"]),
            )
        assert ipm.created == []

    @pytest.mark.asyncio
    async def test_dry_run_checks_ownership_and_persists_nothing(self):
        plants = _PlantService()
        ipm = _IpmService(pests={"pe1"})
        resp = await CreateInspection().preview(
            _ctx(plant_instance_service=plants, ipm_service=ipm),
            CreateInspection.Input(plant_key="p1", detected_pest_keys=["pe1"]),
        )
        assert plants.seen_tenant == TENANT
        assert ipm.created == []
        assert resp.data["detected_pest_keys"] == ["pe1"]

    @pytest.mark.asyncio
    async def test_a_machine_written_inspection_names_the_account(self):
        ipm = _IpmService()
        await CreateInspection().execute(
            _ctx(plant_instance_service=_PlantService(), ipm_service=ipm),
            CreateInspection.Input(plant_key="p1"),
        )
        assert ipm.created[0].inspector == "mcp:u-1"

    @pytest.mark.asyncio
    async def test_get_plant_inspections_surfaces_what_create_inspection_wrote(self):
        # The palette's addressability rule, read in the direction list_diary_entries
        # was added for: a write no read tool finds again is a defect.
        ipm = _IpmService(pests={"pe1"})
        ctx = _ctx(plant_instance_service=_PlantService(), ipm_service=ipm)
        await CreateInspection().execute(
            ctx,
            CreateInspection.Input(
                plant_key="p1",
                findings=[{"symptom": "Gespinste", "confidence": 0.7, "affected_plant_part": "leaf"}],
            ),
        )
        ipm._inspections = list(ipm.created)

        read = await GetPlantInspections().run(ctx, GetPlantInspections.Input(plant_key="p1"))
        finding = read.data["items"][0]["findings"][0]
        assert finding["symptom"] == "Gespinste"
        assert finding["confidence"] == 0.7
        assert finding["affected_plant_part"] == "leaf"
        assert read.data["items"][0]["inspection_key"] == "insp-1"

    def test_confidence_outside_zero_to_one_is_rejected(self):
        with pytest.raises(ValueError, match="confidence"):
            CreateInspection.Input(plant_key="p1", findings=[{"symptom": "x", "confidence": 1.4}])


# ── search_plant_knowledge ────────────────────────────────────────────────────
def _chunk(key, score, *, content="Raubmilben gegen Spinnmilben.", title="Spinnmilben"):
    return KnowledgeChunk(
        source_key=key,
        source_type="knowledge_guide",
        title=title,
        content=content,
        score=score,
        language="de",
        metadata={"topic": "ipm"},
    )


class TestSearchPlantKnowledge:
    @pytest.mark.asyncio
    async def test_hits_are_citable(self):
        # AC-4's actual requirement: a rationale must be able to name its source.
        service = _KnowledgeService([_chunk("rag/ipm/spinnmilben#1", 0.81)])
        resp = await SearchPlantKnowledge().run(
            _global_ctx(knowledge_service_adapter=service),
            SearchPlantKnowledge.Input(query="Spinnmilben Bekaempfung biologisch"),
        )
        hit = resp.data["results"][0]
        assert hit["source_key"] == "rag/ipm/spinnmilben#1"
        assert hit["source_type"] == "knowledge_guide"
        assert hit["title"] == "Spinnmilben"
        assert hit["score"] == 0.81
        assert hit["language"] == "de"

    @pytest.mark.asyncio
    async def test_min_score_drops_weak_hits_and_says_how_many(self):
        service = _KnowledgeService([_chunk("a", 0.81), _chunk("b", 0.62), _chunk("c", 0.31)])
        resp = await SearchPlantKnowledge().run(
            _global_ctx(knowledge_service_adapter=service),
            SearchPlantKnowledge.Input(query="Spinnmilben", min_score=0.6),
        )
        assert [h["source_key"] for h in resp.data["results"]] == ["a", "b"]
        assert resp.data["retrieved"] == 3
        assert "1 further hits were below min_score" in resp.summary

    @pytest.mark.asyncio
    async def test_an_empty_result_warns_against_an_unsourced_claim(self):
        resp = await SearchPlantKnowledge().run(
            _global_ctx(knowledge_service_adapter=_KnowledgeService([])),
            SearchPlantKnowledge.Input(query="nichts dergleichen"),
        )
        assert resp.data["results"] == []
        assert "do not state a sourced claim" in resp.summary

    @pytest.mark.asyncio
    async def test_long_chunks_are_excerpted_but_stay_traceable(self):
        service = _KnowledgeService([_chunk("long", 0.9, content="x" * (DEFAULT_EXCERPT_CHARS + 500))])
        resp = await SearchPlantKnowledge().run(
            _global_ctx(knowledge_service_adapter=service),
            SearchPlantKnowledge.Input(query="lang"),
        )
        hit = resp.data["results"][0]
        assert len(hit["content"]) == DEFAULT_EXCERPT_CHARS
        assert hit["content_truncated"] is True
        assert hit["source_key"] == "long"

        full = await SearchPlantKnowledge().run(
            _global_ctx(knowledge_service_adapter=_KnowledgeService(service._chunks)),
            SearchPlantKnowledge.Input(query="lang", full_content=True),
        )
        assert full.data["results"][0]["content_truncated"] is False

    @pytest.mark.asyncio
    async def test_an_outage_fails_loudly_instead_of_answering_nothing_found(self):
        # "No hits" and "the corpus was never consulted" are different answers,
        # and only one of them permits omitting a claim.
        service = _KnowledgeService(error=KnowledgeServiceUnavailableError("circuit open"))
        with pytest.raises(McpToolError) as excinfo:
            await SearchPlantKnowledge().run(
                _global_ctx(knowledge_service_adapter=service),
                SearchPlantKnowledge.Input(query="Spinnmilben"),
            )
        assert excinfo.value.error_code == "service.unavailable"
        assert excinfo.value.status_code == 503

    @pytest.mark.asyncio
    async def test_nothing_tenant_derived_reaches_the_knowledge_service(self):
        # The tool is tenant-agnostic and PII-free: only the query travels.
        service = _KnowledgeService([_chunk("a", 0.9)])
        await SearchPlantKnowledge().run(
            _global_ctx(knowledge_service_adapter=service),
            SearchPlantKnowledge.Input(query="Tomate Mischkultur", top_k=7, doc_language="de"),
        )
        assert service.calls == [{"query": "Tomate Mischkultur", "top_k": 7, "doc_language": "de"}]

    def test_the_tool_is_not_tenant_scoped(self):
        assert SearchPlantKnowledge.tenant_scoped is False


# ── assign_nutrient_plan ──────────────────────────────────────────────────────
class TestAssignNutrientPlan:
    @pytest.mark.asyncio
    async def test_binds_an_existing_plan_and_names_the_actor(self):
        plans = _NutrientPlanService([_Plan("np-1", "Erdbeere — Plagron Terra")])
        resp = await AssignNutrientPlan().execute(
            _ctx(plant_instance_service=_PlantService(), nutrient_plan_service=plans),
            AssignNutrientPlan.Input(plant_key="p1", plan_key="np-1"),
        )
        assert plans.assignments == [("p1", "np-1", "mcp:u-1")]
        assert resp.data["plan_key"] == "np-1"
        assert resp.data["replaced_plan_key"] is None

    @pytest.mark.asyncio
    async def test_the_dry_run_names_what_would_be_replaced(self):
        # The repository deletes the existing FOLLOWS_PLAN edge silently; naming
        # the loss is the whole reason a preview exists for this tool.
        old = _Plan("np-0", "Alter Plan")
        plans = _NutrientPlanService([_Plan("np-1", "Neuer Plan"), old], current=old)
        resp = await AssignNutrientPlan().preview(
            _ctx(plant_instance_service=_PlantService(), nutrient_plan_service=plans),
            AssignNutrientPlan.Input(plant_key="p1", plan_key="np-1"),
        )
        assert plans.assignments == []
        assert resp.data["replaces_plan_key"] == "np-0"
        assert "replacing 'Alter Plan'" in resp.summary

    @pytest.mark.asyncio
    async def test_a_global_template_may_be_assigned(self):
        # The hybrid catalogue: a globally seeded plan carries an empty tenant_key
        # and is legitimately assignable (PR #324).
        plans = _NutrientPlanService([_Plan("tpl-1", "Erdbeere (einmaltragend)", tenant_key="")])
        await AssignNutrientPlan().execute(
            _ctx(plant_instance_service=_PlantService(), nutrient_plan_service=plans),
            AssignNutrientPlan.Input(plant_key="p1", plan_key="tpl-1"),
        )
        assert plans.assignments == [("p1", "tpl-1", "mcp:u-1")]

    @pytest.mark.asyncio
    async def test_both_sides_are_resolved_against_the_acting_tenant(self):
        plants = _PlantService()
        plans = _NutrientPlanService([_Plan("np-1", "Plan")])
        await AssignNutrientPlan().execute(
            _ctx(plant_instance_service=plants, nutrient_plan_service=plans),
            AssignNutrientPlan.Input(plant_key="p1", plan_key="np-1"),
        )
        # Resolving both keys first is the SEC-001 fetch-then-use guard: the
        # lookups refuse a foreign key before any write is reached. This comment
        # used to justify that with "assign_to_plant itself takes no tenant",
        # which stopped being true at #950 and then served as the reason nobody
        # re-read the call site (#1145). The write now carries a tenant of its
        # own, and `seen_tenants` covers it because the double records it.
        assert plants.seen_tenant == TENANT
        assert set(plans.seen_tenants) == {TENANT}

    @pytest.mark.asyncio
    async def test_a_foreign_plan_is_refused_before_the_write(self):
        plans = _NutrientPlanService([_Plan("np-1", "Plan")])
        with pytest.raises(NotFoundError):
            await AssignNutrientPlan().execute(
                _ctx(plant_instance_service=_PlantService(), nutrient_plan_service=plans),
                AssignNutrientPlan.Input(plant_key="p1", plan_key="someone-elses-plan"),
            )
        assert plans.assignments == []

    @pytest.mark.asyncio
    async def test_a_foreign_plant_is_refused_before_the_write(self):
        plans = _NutrientPlanService([_Plan("np-1", "Plan")])
        with pytest.raises(NotFoundError):
            await AssignNutrientPlan().execute(
                _ctx(plant_instance_service=_PlantService(), nutrient_plan_service=plans),
                AssignNutrientPlan.Input(plant_key="someone-elses-plant", plan_key="np-1"),
            )
        assert plans.assignments == []
