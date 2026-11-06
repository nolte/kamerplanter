"""WP 8.10 (#2653) — what the nutrient-hint service reads for a bed, and that the bed summary carries it.

The engine decides (``test_nutrient_hint_engine.py``); this file pins the inputs it gets: the species' own stored
``nutrient_demand`` (no family value in its place, no foreign species), the preceding crop's ``nitrogen_fixing``,
the newest nutrient input (``feeding`` or an amendment with a nutrient material), bark mulch and the lab classes -
each read scoped by the tenant and bounded. And that production wires the service into the bed summary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

from app.common import dependencies
from app.common.enums import GrowingMediumKind, NutrientDemand
from app.domain.engines.crop_rotation_validator import HistoryEntry
from app.domain.engines.nutrient_hint_engine import DEFAULT_CONFIG, NutrientHintConfig, SourcedThreshold
from app.domain.interfaces.care_event_repository import CareEventFilter, CareEventRow
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.care_event import CareEvent
from app.domain.models.site import Location, SoilProfile
from app.domain.models.species import Species
from app.domain.services.nutrient_hint_service import READ_WINDOW_DAYS, NutrientHintService

TENANT = "t_own"
NOW = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
SOURCE = "test threshold, not agronomy"


def _species(key: str, *, demand: NutrientDemand | None, tenant: str = "", family: str = "fam", **kw: Any) -> Species:
    return Species(
        _key=key, scientific_name=f"Genus {key}", tenant_key=tenant, family_key=family, nutrient_demand=demand, **kw
    )


class FakeSpecies:
    def __init__(self, *species: Species) -> None:
        self.by_key = {each.key: each for each in species}

    def get_by_key(self, key: str) -> Species | None:
        return self.by_key.get(key)

    def is_granted_to(self, key: str, tenant_key: str) -> bool:
        return False


@dataclass
class FakeEvents:
    events: list[CareEvent] = field(default_factory=list)
    calls: list[tuple[CareEventFilter, str, int]] = field(default_factory=list)

    def list_events(self, criteria: CareEventFilter, *, tenant_key: str, offset: int, limit: int) -> list[CareEventRow]:
        self.calls += [(criteria, tenant_key, limit)]
        rows = [
            e
            for e in self.events
            if e.tenant_key == tenant_key
            and e.location_key == criteria.location_key
            and e.category == criteria.category
            and (criteria.performed_from is None or e.performed_at >= criteria.performed_from)
            and (not criteria.exclude_voided or e.voided_at is None)
        ]
        rows.sort(key=lambda e: e.performed_at, reverse=True)
        return [CareEventRow(event=e) for e in rows[offset : offset + limit]]


class FakeResolver:
    def __init__(self, species: FakeSpecies, families: dict[str, BotanicalFamily]) -> None:
        self._species = species
        self._families = families

    def species(self, key: str | None) -> Species | None:
        return self._species.get_by_key(key) if key else None

    def family(self, key: str | None) -> BotanicalFamily | None:
        return self._families.get(key) if key else None


class FakeValidator:
    def __init__(self, entries: list[HistoryEntry], resolver: FakeResolver) -> None:
        self.entries = entries
        self.resolver = resolver
        self.tenants: list[str] = []

    def bed_rotation_entries(self, location: Location, *, tenant_key: str) -> tuple[list[HistoryEntry], None]:
        self.tenants += [tenant_key]
        return self.entries, None

    def timeline_resolver(self, tenant_key: str) -> FakeResolver:
        return self.resolver


def _event(category: str, days_ago: float, **kw: Any) -> CareEvent:
    return CareEvent(
        tenant_key=kw.pop("tenant_key", TENANT),
        site_key="site",
        location_key="bed",
        category=category,
        summary="x",
        performed_at=NOW - timedelta(days=days_ago),
        **kw,
    )


BED = Location(
    _key="bed",
    name="Bed",
    site_key="site",
    area_m2=2.0,
    location_type_key="bed",
    soil_profile=SoilProfile(growing_medium_kind=GrowingMediumKind.NATIVE_SOIL),
)
ACTIVE = NutrientHintConfig(
    check_after_days={
        d: SourcedThreshold(30 if d is NutrientDemand.HEAVY_FEEDER else None, SOURCE) for d in NutrientDemand
    },
    likely_deficit_after_days={
        d: SourcedThreshold(60 if d is NutrientDemand.HEAVY_FEEDER else None, SOURCE) for d in NutrientDemand
    },
)


def _service(
    *, events: list[CareEvent] | None = None, entries: list[HistoryEntry] | None = None, config=ACTIVE, extra=()
) -> tuple[NutrientHintService, FakeEvents, FakeValidator]:
    species = FakeSpecies(
        _species("tomato", demand=NutrientDemand.HEAVY_FEEDER),
        _species("unknown", demand=None, family="heavy_family"),
        _species("foreign", demand=NutrientDemand.LIGHT_FEEDER, tenant="t_other"),
        _species("bean", demand=NutrientDemand.LIGHT_FEEDER, family="fabaceae", nitrogen_fixing=True),
        _species("pea_unflagged", demand=NutrientDemand.LIGHT_FEEDER, family="fabaceae", nitrogen_fixing=None),
        _species("carrot_not_fixing", demand=NutrientDemand.LIGHT_FEEDER, family="fabaceae", nitrogen_fixing=False),
        *extra,
    )
    families = {
        "fabaceae": BotanicalFamily(_key="fabaceae", name="Fabaceae", nitrogen_fixing=True),
        "heavy_family": BotanicalFamily(
            _key="heavy_family", name="Solanaceae", typical_nutrient_demand=NutrientDemand.HEAVY_FEEDER
        ),
    }
    fake_events = FakeEvents(list(events or []))
    validator = FakeValidator(list(entries or []), FakeResolver(species, families))
    return NutrientHintService(species, fake_events, validator, config), fake_events, validator  # type: ignore[arg-type]


def _entry(
    year: int, species_key: str | None, family_key: str | None = "fabaceae", role: str = "main_crop"
) -> HistoryEntry:
    return HistoryEntry(year, family_key, species_key, role, None, "plant")


class TestDemand:
    def test_a_species_without_its_own_demand_gets_none_not_the_family_value(self) -> None:
        service, _, _ = _service()
        hint = service.assess(BED, ["unknown"], tenant_key=TENANT, now=NOW)
        assert (hint.state, hint.reasons[0]) == ("insufficient_data", "demand_unknown")

    def test_a_foreign_species_is_not_read(self) -> None:
        service, _, _ = _service()
        hint = service.assess(BED, ["foreign"], tenant_key=TENANT, now=NOW)
        assert hint.reasons[0] == "demand_unknown"

    def test_the_stored_demand_reaches_the_engine(self) -> None:
        service, _, _ = _service(events=[_event("feeding", 90)])
        assert service.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW).state == "likely_deficit"


class TestNutrientInputs:
    def test_the_newest_feeding_or_nutrient_amendment_counts(self) -> None:
        service, _, _ = _service(
            events=[
                _event("feeding", 90),
                _event("soil_amendment", 10, material="horn_shavings"),
                _event("soil_amendment", 1, material="sand"),
            ]
        )
        assert service.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW).state == "ok"

    def test_an_amendment_without_a_nutrient_material_does_not_count(self) -> None:
        service, _, _ = _service(events=[_event("feeding", 90), _event("soil_amendment", 1, material="sand")])
        assert service.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW).state == "likely_deficit"

    def test_a_voided_feeding_and_another_tenant_s_feeding_do_not_count(self) -> None:
        service, _, _ = _service(
            events=[
                _event("feeding", 1, voided_at=NOW),
                _event("feeding", 1, tenant_key="t_other"),
            ]
        )
        hint = service.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW)
        assert hint.reasons[0] == "no_feeding_recorded"

    def test_bark_mulch_after_the_feeding_is_flagged(self) -> None:
        service, _, _ = _service(events=[_event("feeding", 10), _event("mulching", 2, material="bark_mulch")])
        hint = service.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW)
        assert hint.state == "check" and "bark_mulch_n_binding" in hint.reasons

    def test_the_reads_are_scoped_bounded_and_windowed(self) -> None:
        service, events, validator = _service()
        service.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW)
        assert {tenant for _c, tenant, _l in events.calls} == {TENANT} and validator.tenants == [TENANT]
        assert all(limit <= 50 for _c, _t, limit in events.calls)
        windows = {c.category: c.performed_from for c, _t, _l in events.calls}
        assert windows["feeding"] == NOW - timedelta(days=READ_WINDOW_DAYS)
        assert windows["soil_analysis"] is None  # a lab analysis is repeated every few years


class TestLabClasses:
    def test_an_old_lab_class_d_withholds_compost_and_p(self) -> None:
        analysis = _event(
            "soil_analysis",
            800,
            measurements=[{"parameter": "p", "value": 30, "unit": "mg", "source": "lab", "content_class": "D"}],
        )
        service, _, _ = _service(events=[analysis])
        hint = service.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW)
        assert hint.compost_and_p_withheld is True


class TestPrecedingCrop:
    def test_a_legume_of_the_previous_year_is_flagged(self) -> None:
        service, _, _ = _service(entries=[_entry(NOW.year - 1, "bean")])
        hint = service.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW)
        assert "preceding_nitrogen_fixer" in hint.reasons

    def test_the_species_flag_wins_over_the_family_and_the_family_fills_a_gap(self) -> None:
        not_fixing, _, _ = _service(entries=[_entry(NOW.year - 1, "carrot_not_fixing")])
        assert "preceding_nitrogen_fixer" not in not_fixing.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW).reasons
        unflagged, _, _ = _service(entries=[_entry(NOW.year - 1, "pea_unflagged")])
        assert "preceding_nitrogen_fixer" in unflagged.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW).reasons

    def test_an_older_year_or_a_fallow_year_is_no_preceding_crop(self) -> None:
        older, _, _ = _service(entries=[_entry(NOW.year - 2, "bean")])
        assert "preceding_nitrogen_fixer" not in older.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW).reasons
        fallow, _, _ = _service(entries=[_entry(NOW.year - 1, None, role="fallow")])
        assert "preceding_nitrogen_fixer" not in fallow.assess(BED, ["tomato"], tenant_key=TENANT, now=NOW).reasons


def test_production_wires_the_hint_into_the_bed_summary_with_the_null_configuration(monkeypatch) -> None:
    """The bed summary asks the production provider, and that provider ships no sourced threshold (E-10)."""
    for name in ("get_site_repo", "get_garden_plan_repo", "get_db", "get_species_repo", "get_care_event_repo"):
        monkeypatch.setattr(dependencies, name, MagicMock)

    assert dependencies.get_garden_resource_service()._nutrient_hint is dependencies.get_nutrient_hint_service
    shipped = dependencies.get_nutrient_hint_service()
    assert shipped._config is DEFAULT_CONFIG and shipped._config.active_rules() == ()
