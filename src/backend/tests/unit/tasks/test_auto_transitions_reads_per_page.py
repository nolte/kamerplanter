"""MT-032 (#2128): ``check_auto_transitions`` pays no store read per plant.

The scan walked the active tenants' plants a page at a time but then asked the store
three to ten times **per plant**: ``PhaseService.get_current_phase`` (the plant again,
its phase history, the outgoing rules, the target phase, the phase resolution, the
species' sequence with every entry and definition), the species' lifecycle, the
phase's transition rules, the sequence's next entry and the plant's location and site.
With a few thousand plants the beat sent tens of thousands of queries, and it grew
with every plant an installation added.

These tests drive the **real task** over the **real** :class:`PhaseService` and count
every repository call. Plants that share a species, a phase and a location must cost
nothing extra: the reads for forty plants equal the reads for three. Against the
per-plant scan the forty-plant run reads more, so the comparison fails there.

The memo behind it is scoped to one page — a page of a different size re-reads the
catalogue per page — so the worker's memory is bounded by the page, not the
installation.
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.enums import LightType, PhotoperiodType, TransitionTriggerType
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.phase import PhaseHistory, PhaseTransitionRule
from app.domain.models.phase_sequence import PhaseDefinition, PhaseSequence, PhaseSequenceEntry
from app.domain.models.site import Location, Site
from app.domain.services.phase_service import PhaseService
from tests.support.tenant_walk import TenantRows, active

_NOW = datetime.now(UTC)
_FIVE_DAYS_AGO = _NOW - timedelta(days=5)


class _Reads:
    """Every repository call, by method name."""

    def __init__(self) -> None:
        self.calls: Counter[str] = Counter()

    def __call__(self, name: str) -> None:
        self.calls[name] += 1

    def total(self) -> int:
        return sum(self.calls.values())


class _PhaseRepo:
    """The legacy GrowthPhase store: one species, one phase, a time and a photoperiod rule."""

    def __init__(self, log: _Reads, histories: dict[str, PhaseHistory]) -> None:
        self._log = log
        self._histories = histories
        self._lifecycle = LifecycleConfig(
            _key="lc-legacy",
            species_key="sp-legacy",
            photoperiod_type=PhotoperiodType.SHORT_DAY,
            critical_day_length_hours=10.0,  # the tent runs 12 h: no induction, nothing fires
        )
        self._phase = GrowthPhase(
            _key="gp-veg", name="vegetative", lifecycle_key="lc-legacy", typical_duration_days=30, sequence_order=1
        )
        self._flower = GrowthPhase(
            _key="gp-flower", name="flowering", lifecycle_key="lc-legacy", typical_duration_days=60, sequence_order=2
        )
        self._rules = [
            PhaseTransitionRule(
                from_phase_key="gp-veg",
                to_phase_key="gp-flower",
                trigger_type=TransitionTriggerType.TIME_BASED,
                auto_transition_after_days=60,
            ),
            PhaseTransitionRule(
                from_phase_key="gp-veg",
                to_phase_key="gp-flower",
                trigger_type=TransitionTriggerType.PHOTOPERIOD_BASED,
            ),
        ]

    def get_lifecycle_by_species(self, species_key):  # noqa: ANN001, ANN201
        self._log("get_lifecycle_by_species")
        return self._lifecycle if species_key == "sp-legacy" else None

    def get_lifecycle_by_key(self, key):  # noqa: ANN001, ANN201
        self._log("get_lifecycle_by_key")
        return self._lifecycle if key == "lc-legacy" else None

    def get_phases_by_lifecycle(self, key):  # noqa: ANN001, ANN201
        self._log("get_phases_by_lifecycle")
        return [self._phase, self._flower] if key == "lc-legacy" else []

    def get_phase_by_key(self, key):  # noqa: ANN001, ANN201
        self._log("get_phase_by_key")
        return {"gp-veg": self._phase, "gp-flower": self._flower}.get(key)

    def get_transition_rules(self, key):  # noqa: ANN001, ANN201
        self._log("get_transition_rules")
        return list(self._rules) if key == "gp-veg" else []

    def get_phase_history(self, plant_key):  # noqa: ANN001, ANN201
        self._log("get_phase_history")
        history = self._histories.get(plant_key)
        return [history] if history else []

    def get_active_phase_histories(self, plant_keys):  # noqa: ANN001, ANN201
        self._log("get_active_phase_histories")
        return {key: self._histories[key] for key in plant_keys if key in self._histories}


class _SequenceRepo:
    """The PhaseSequence store: one species on a two-entry sequence."""

    def __init__(self, log: _Reads) -> None:
        self._log = log
        self._sequence = PhaseSequence(_key="seq-1", name="seq", species_key="sp-seq")
        self._entries = [
            PhaseSequenceEntry(
                _key="e-veg", phase_sequence_key="seq-1", phase_definition_key="d-veg", sequence_order=1
            ),
            PhaseSequenceEntry(
                _key="e-flower", phase_sequence_key="seq-1", phase_definition_key="d-flower", sequence_order=2
            ),
        ]
        self._definitions = {
            "d-veg": PhaseDefinition(_key="d-veg", name="vegetative", typical_duration_days=30),
            "d-flower": PhaseDefinition(_key="d-flower", name="flowering", typical_duration_days=60),
        }

    def get_entry_by_key(self, key):  # noqa: ANN001, ANN201
        self._log("get_entry_by_key")
        return next((e for e in self._entries if e.key == key), None)

    def get_definition_by_key(self, key):  # noqa: ANN001, ANN201
        self._log("get_definition_by_key")
        return self._definitions.get(key)

    def get_sequence_by_species(self, species_key):  # noqa: ANN001, ANN201
        self._log("get_sequence_by_species")
        return self._sequence if species_key == "sp-seq" else None

    def get_entries_for_sequence(self, key):  # noqa: ANN001, ANN201
        self._log("get_entries_for_sequence")
        return list(self._entries) if key == "seq-1" else []


class _SiteRepo:
    """One tenant site holding one grow tent with a 12 h light schedule."""

    def __init__(self, log: _Reads) -> None:
        self._log = log
        self._site = Site(_key="site-1", tenant_key="t1", name="Home", type="indoor")
        self._location = Location(
            _key="loc-1",
            name="Tent",
            area_m2=1.0,
            site_key="site-1",
            light_type=LightType.LED,
            lights_on="06:00",
            lights_off="18:00",
            use_dynamic_sunrise=False,
        )

    def get_site_by_key(self, key):  # noqa: ANN001, ANN201
        self._log("get_site_by_key")
        return self._site if key == "site-1" else None

    def get_location_by_key(self, key):  # noqa: ANN001, ANN201
        self._log("get_location_by_key")
        return self._location if key == "loc-1" else None

    def get_slot_by_key(self, key):  # noqa: ANN001, ANN201
        self._log("get_slot_by_key")
        return None


class _PlantLookups:
    """The plant repository the service holds (the walk is the ``TenantRows`` double)."""

    def __init__(self, log: _Reads, plants: list[SimpleNamespace]) -> None:
        self._log = log
        self._plants = {p.key: p for p in plants}

    def get_or_raise(self, key):  # noqa: ANN001, ANN201
        self._log("get_or_raise")
        return self._plants[key]

    def get_by_key(self, key):  # noqa: ANN001, ANN201
        self._log("get_by_key")
        return self._plants.get(key)


def _plants(count: int) -> list[SimpleNamespace]:
    """``count`` plants alternating between the legacy and the sequence species, all in the tent."""
    plants = []
    for i in range(count):
        legacy = i % 2 == 0
        plants.append(
            SimpleNamespace(
                key=f"p{i:04d}",
                tenant_key="t1",
                removed_on=None,
                current_phase_key="gp-veg" if legacy else "e-veg",
                current_phase_started_at=_FIVE_DAYS_AGO,
                species_key="sp-legacy" if legacy else "sp-seq",
                site_key="site-1",
                location_key="loc-1",
                chill_days_accumulated=0,
                cultivation_cycle_type=None,
            )
        )
    return plants


def _histories(plants: list[SimpleNamespace]) -> dict[str, PhaseHistory]:
    """Every third plant carries an open history entry; the rest fall back to their own fields."""
    return {
        p.key: PhaseHistory(plant_instance_key=p.key, phase_key=p.current_phase_key, entered_at=_FIVE_DAYS_AGO)
        for i, p in enumerate(plants)
        if i % 3 == 0
    }


@pytest.fixture
def scan(monkeypatch):
    """Run the real task over ``count`` plants; returns ``(result, reads)``."""
    # The task binds its getters at import; a stand-in module lets it import without a store.
    stand_in = ModuleType("app.common.dependencies")
    for name in ("get_lifecycle_repo", "get_phase_service", "get_plant_repo", "get_site_repo", "get_tenant_repo"):
        setattr(stand_in, name, MagicMock(name=name))
    monkeypatch.setitem(sys.modules, "app.common.dependencies", stand_in)
    import app.tasks.phase_transitions as module

    def run(count: int, *, page_size: int | None = None):  # noqa: ANN202
        if page_size is not None:
            monkeypatch.setattr(module, "_PAGE_SIZE", page_size)
        log = _Reads()
        plants = _plants(count)
        phase_repo = _PhaseRepo(log, _histories(plants))
        service = PhaseService(phase_repo, _PlantLookups(log, plants), phase_seq_repo=_SequenceRepo(log))
        transition = MagicMock(name="transition_phase")
        monkeypatch.setattr(service, "transition_phase", transition)
        monkeypatch.setattr(module, "get_plant_repo", lambda: TenantRows(plants))
        monkeypatch.setattr(module, "get_phase_service", lambda: service)
        monkeypatch.setattr(module, "get_lifecycle_repo", lambda: phase_repo)
        monkeypatch.setattr(module, "get_site_repo", lambda: _SiteRepo(log))
        monkeypatch.setattr(module, "get_tenant_repo", lambda: active("t1"))
        result = module.check_auto_transitions()
        transition.assert_not_called()
        return result, log

    return run


def test_plants_sharing_species_phase_and_location_cost_no_further_read(scan) -> None:
    few_result, few = scan(3)
    many_result, many = scan(40)

    # The whole claim: thirty-seven more plants of the same species, phase and tent, zero more reads.
    assert many.calls == few.calls, f"reads grew with the plants: {few.total()} for 3, {many.total()} for 40"
    assert few_result == {"transitioned": 0, "errors": 0, "checked": 3}
    assert many_result == {"transitioned": 0, "errors": 0, "checked": 40}


def test_the_page_reads_its_histories_once_and_never_a_plant_by_key(scan) -> None:
    _result, log = scan(40)

    assert log.calls["get_active_phase_histories"] == 1
    assert log.calls["get_phase_history"] == 0
    assert log.calls["get_or_raise"] == 0
    assert log.calls["get_by_key"] == 0


def test_the_photoperiod_path_is_measured_too(scan) -> None:
    """The tent's location and site are read (the SEC-B4 ownership walk ran), once per page."""
    _result, log = scan(40)

    assert log.calls["get_location_by_key"] == 1
    assert log.calls["get_site_by_key"] == 1
    assert log.calls["get_transition_rules"] == 1


def test_the_memo_lives_for_one_page(scan) -> None:
    """Four pages read the shared catalogue four times: the memory is bounded by a page, not the run."""
    _one, one_page = scan(40)
    _four, four_pages = scan(40, page_size=10)

    assert four_pages.calls["get_active_phase_histories"] == 4
    assert four_pages.calls["get_lifecycle_by_species"] == 4 * one_page.calls["get_lifecycle_by_species"]
    assert four_pages.calls["get_location_by_key"] == 4


def test_the_batched_positions_equal_the_per_plant_positions() -> None:
    """``get_current_phases`` answers, field by field, what ``get_current_phase`` answers per plant."""
    log = _Reads()
    plants = [
        *_plants(6),
        SimpleNamespace(
            key="p-unknown",
            tenant_key="t1",
            removed_on=None,
            current_phase_key="no-such-phase",
            current_phase_started_at=None,
            species_key="sp-legacy",
            site_key=None,
            location_key=None,
            chill_days_accumulated=0,
            cultivation_cycle_type=None,
        ),
    ]
    histories = _histories(plants)
    # A history whose phase differs from the plant's own field: the history wins in both paths.
    histories["p0001"] = PhaseHistory(
        plant_instance_key="p0001", phase_key="e-flower", entered_at=_NOW - timedelta(days=12), cycle_number=3
    )
    service = PhaseService(_PhaseRepo(log, histories), _PlantLookups(log, plants), phase_seq_repo=_SequenceRepo(log))

    batched = service.get_current_phases(plants)

    fields = ("phase", "phase_key", "days_in_phase", "cycle_number", "source", "is_terminal")
    for plant in plants:
        single = service.get_current_phase(plant.key)
        assert batched[plant.key] == {field: single[field] for field in fields}, plant.key
    assert batched["p0001"]["phase_key"] == "e-flower"
    assert batched["p0001"]["cycle_number"] == 3
    assert batched["p0001"]["days_in_phase"] == 12
    assert batched["p-unknown"]["source"] is None
