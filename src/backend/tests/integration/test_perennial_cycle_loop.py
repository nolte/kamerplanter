"""Integration test: the cyclic perennial loop (#565 Phase 1, WP-1..2).

Drives the REAL ``check_auto_transitions`` Celery task over the REAL
:class:`PhaseService` + :class:`PhaseTransitionEngine` + :class:`CyclicLifecycleEngine`
against in-memory repositories, simulating a full growing year one phase at a time.

DoD #1: a strawberry (``perennial_runner``) AND a representative Path-A staude
(``evergreen_foliage_perennial``) run through a full year and LOOP back into a new
vegetative growth cycle WITHOUT any manual phase editing — proving the cycle-restart
motor (``should_restart_cycle`` → ``cycle_restart_entry_order``) is actually wired into
the auto-transition path, not only exercised in unit tests.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType, SimpleNamespace

import pytest

from app.common.enums import CycleType, PhotoperiodType
from app.domain.models.lifecycle import LifecycleConfig
from app.domain.models.phase import PhaseHistory
from app.domain.models.phase_sequence import PhaseDefinition, PhaseSequence, PhaseSequenceEntry
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.phase_service import PhaseService

# ── Sequence blueprints (mirror seed_data/phase_sequences.yaml) ────────────────

# (phase_name, order, duration_days, is_terminal, is_recurring, allows_harvest)
_PERENNIAL_RUNNER = [
    ("establishment", 0, 45, False, False, False),
    ("sprouting", 1, 21, False, True, False),
    ("vegetative", 2, 45, False, True, False),
    ("flowering", 3, 25, False, True, False),
    ("fruiting", 4, 35, False, True, False),
    ("ripening", 5, 20, False, True, True),
    ("dormancy", 6, 120, True, True, False),
]
_EVERGREEN = [
    ("establishment", 0, 60, False, False, False),
    ("active_growth", 1, 180, False, True, False),
    ("flowering", 2, 30, False, True, False),
    ("maintenance", 3, 180, True, True, False),
]


class _FakePhaseSequenceRepo:
    """In-memory PhaseSequence repo covering the methods PhaseService/engine touch."""

    def __init__(self) -> None:
        self._sequences: dict[str, PhaseSequence] = {}
        self._entries: dict[str, PhaseSequenceEntry] = {}
        self._definitions: dict[str, PhaseDefinition] = {}
        self._species_to_seq: dict[str, str] = {}
        self._defs_by_name: dict[str, str] = {}

    def add_sequence(
        self,
        name: str,
        blueprint: list[tuple[str, int, int, bool, bool, bool]],
        *,
        cycle_restart_entry_order: int,
        species_keys: list[str],
    ) -> str:
        seq_key = f"seq-{name}"
        self._sequences[seq_key] = PhaseSequence(
            _key=seq_key,
            name=name,
            cycle_type=CycleType.PERENNIAL,
            is_repeating=True,
            cycle_restart_entry_order=cycle_restart_entry_order,
            photoperiod_type=PhotoperiodType.DAY_NEUTRAL,
        )
        for phase_name, order, duration, is_terminal, is_recurring, allows_harvest in blueprint:
            def_key = self._defs_by_name.get(phase_name)
            if def_key is None:
                def_key = f"def-{phase_name}"
                self._definitions[def_key] = PhaseDefinition(
                    _key=def_key, name=phase_name, typical_duration_days=max(duration, 1)
                )
                self._defs_by_name[phase_name] = def_key
            entry_key = f"e-{name}-{order}"
            self._entries[entry_key] = PhaseSequenceEntry(
                _key=entry_key,
                phase_sequence_key=seq_key,
                phase_definition_key=def_key,
                sequence_order=order,
                override_duration_days=duration,
                is_terminal=is_terminal,
                is_recurring=is_recurring,
                allows_harvest=allows_harvest,
            )
        for sp in species_keys:
            self._species_to_seq[sp] = seq_key
        return seq_key

    def entry_key(self, seq_name: str, order: int) -> str:
        return f"e-{seq_name}-{order}"

    # ── interface subset ──
    def get_sequence_by_species(self, species_key: str) -> PhaseSequence | None:
        seq_key = self._species_to_seq.get(species_key)
        return self._sequences.get(seq_key) if seq_key else None

    def get_sequence_by_key(self, key: str) -> PhaseSequence | None:
        return self._sequences.get(key)

    def get_entries_for_sequence(self, seq_key: str) -> list[PhaseSequenceEntry]:
        return [e for e in self._entries.values() if e.phase_sequence_key == seq_key]

    def get_entry_by_key(self, key: str) -> PhaseSequenceEntry | None:
        return self._entries.get(key)

    def get_definition_by_key(self, key: str) -> PhaseDefinition | None:
        return self._definitions.get(key)


class _FakePhaseRepo:
    """In-memory phase repo: histories are mutable, everything sequence-driven."""

    def __init__(self) -> None:
        self._histories: list[PhaseHistory] = []
        self._seq = 0

    def get_phase_history(self, plant_key: str) -> list[PhaseHistory]:
        return [h for h in self._histories if h.plant_instance_key == plant_key]

    def create_phase_history(self, history: PhaseHistory) -> PhaseHistory:
        self._seq += 1
        history.key = f"h-{self._seq}"
        self._histories.append(history)
        return history

    def update_phase_history(self, key: str, history: PhaseHistory) -> PhaseHistory:
        for i, h in enumerate(self._histories):
            if h.key == key:
                history.key = key
                self._histories[i] = history
                return history
        return history

    def get_transition_rules(self, from_phase_key: str) -> list:
        return []

    def get_phase_by_key(self, key: str):
        return None  # sequence-driven only

    def get_lifecycle_by_key(self, key: str):
        return None

    def get_lifecycle_by_species(self, species_key: str):
        # These plants are pure Weg-B (sequence-driven), so the engine's
        # effective-cycle gate has no LifecycleConfig here and falls through to the
        # sequence cycle_type / the per-instance override. The task layer already
        # suppresses annual-grown perennials before the engine is reached.
        return None

    def get_phases_by_lifecycle(self, lifecycle_key: str) -> list:
        return []


class _FakePlantRepo:
    def __init__(self, plants: list[PlantInstance]) -> None:
        self._plants = {p.key: p for p in plants}

    def get_by_key(self, key: str) -> PlantInstance | None:
        return self._plants.get(key)

    def get_or_raise(self, key: str) -> PlantInstance:
        return self._plants[key]

    def update(self, key: str, plant: PlantInstance) -> PlantInstance:
        self._plants[key] = plant
        return plant

    def get_all(self, offset: int = 0, limit: int = 1000, all_tenants: bool = False):
        plants = list(self._plants.values())
        return plants, len(plants)


class _FakeLifecycleRepo:
    def __init__(self, by_species: dict[str, LifecycleConfig]) -> None:
        self._by_species = by_species

    def get_lifecycle_by_species(self, species_key: str) -> LifecycleConfig | None:
        return self._by_species.get(species_key)


def _backdate_open_phase(phase_repo: _FakePhaseRepo, plant: PlantInstance, days: int = 500) -> None:
    """Push the plant's open phase far enough into the past that its duration elapsed."""
    past = datetime.now(UTC) - timedelta(days=days)
    plant.current_phase_started_at = past
    for h in phase_repo.get_phase_history(plant.key or ""):
        if h.exited_at is None:
            h.entered_at = past


@pytest.fixture
def _task_env(monkeypatch):
    """Wire the real task against in-memory repos + a real PhaseService."""
    seq_repo = _FakePhaseSequenceRepo()
    seq_repo.add_sequence(
        "perennial_runner", _PERENNIAL_RUNNER, cycle_restart_entry_order=1, species_keys=["sp-strawberry"]
    )
    seq_repo.add_sequence(
        "evergreen_foliage_perennial", _EVERGREEN, cycle_restart_entry_order=1, species_keys=["sp-ficus"]
    )
    # A facultative "tender perennial" (tomato): a cyclic sequence structure, but its
    # LifecycleConfig is grown as an ANNUAL by default (#565 Phase 2 / ADR-006 E1/E6).
    # Without a per-instance override it must NOT loop; a perennial override makes it loop.
    seq_repo.add_sequence(
        "tender_perennial", _PERENNIAL_RUNNER, cycle_restart_entry_order=1, species_keys=["sp-tomato"]
    )
    phase_repo = _FakePhaseRepo()

    strawberry = PlantInstance(
        _key="plant-strawberry",
        tenant_key="t1",
        instance_id="s1",
        species_key="sp-strawberry",
        planted_on=datetime.now(UTC).date(),
        current_phase_key=seq_repo.entry_key("perennial_runner", 0),  # establishment
        current_phase_started_at=datetime.now(UTC),
    )
    ficus = PlantInstance(
        _key="plant-ficus",
        tenant_key="t1",
        instance_id="f1",
        species_key="sp-ficus",
        planted_on=datetime.now(UTC).date(),
        current_phase_key=seq_repo.entry_key("evergreen_foliage_perennial", 0),  # establishment
        current_phase_started_at=datetime.now(UTC),
    )
    tomato = PlantInstance(
        _key="plant-tomato",
        tenant_key="t1",
        instance_id="tm1",
        species_key="sp-tomato",
        planted_on=datetime.now(UTC).date(),
        current_phase_key=seq_repo.entry_key("tender_perennial", 0),  # establishment
        current_phase_started_at=datetime.now(UTC),
    )
    plant_repo = _FakePlantRepo([strawberry, ficus, tomato])
    lifecycle_repo = _FakeLifecycleRepo(
        {
            "sp-strawberry": LifecycleConfig(species_key="sp-strawberry", cycle_type=CycleType.PERENNIAL),
            "sp-ficus": LifecycleConfig(species_key="sp-ficus", cycle_type=CycleType.PERENNIAL),
            # Grown as an annual by default — the instance override (E1) decides otherwise.
            "sp-tomato": LifecycleConfig(species_key="sp-tomato", cycle_type=CycleType.ANNUAL),
        }
    )

    # Open the first phase history for each plant (mirrors plant creation).
    for plant in (strawberry, ficus, tomato):
        phase_repo.create_phase_history(
            PhaseHistory(
                plant_instance_key=plant.key or "",
                phase_key=plant.current_phase_key or "",
                phase_name="establishment",
                entered_at=datetime.now(UTC),
                cycle_number=1,
            )
        )

    phase_service = PhaseService(phase_repo, plant_repo, phase_seq_repo=seq_repo)

    mock_deps = ModuleType("app.common.dependencies")
    mock_deps.get_phase_service = lambda: phase_service  # type: ignore[attr-defined]
    mock_deps.get_plant_repo = lambda: plant_repo  # type: ignore[attr-defined]
    mock_deps.get_lifecycle_repo = lambda: lifecycle_repo  # type: ignore[attr-defined]
    mock_deps.get_site_repo = lambda: SimpleNamespace()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "app.common.dependencies", mock_deps)

    import app.tasks.phase_transitions as task_module

    monkeypatch.setattr(task_module, "get_phase_service", mock_deps.get_phase_service)
    monkeypatch.setattr(task_module, "get_plant_repo", mock_deps.get_plant_repo)
    monkeypatch.setattr(task_module, "get_lifecycle_repo", mock_deps.get_lifecycle_repo)
    monkeypatch.setattr(task_module, "get_site_repo", mock_deps.get_site_repo)

    return SimpleNamespace(
        task=task_module,
        phase_service=phase_service,
        phase_repo=phase_repo,
        plant_repo=plant_repo,
        lifecycle_repo=lifecycle_repo,
        strawberry=strawberry,
        ficus=ficus,
        tomato=tomato,
    )


def _run_year(env, plant: PlantInstance, *, max_steps: int = 30) -> list[tuple[str, int]]:
    """Auto-advance one plant, back-dating each phase so every step fires.

    Returns the visited ``(phase_name, cycle_number)`` trail, stopping once the plant
    has looped into cycle 2 and returned to a growth phase, or after ``max_steps``.
    """
    trail: list[tuple[str, int]] = []
    for _ in range(max_steps):
        info = env.phase_service.get_current_phase(plant.key or "")
        step = (info["phase"], info["cycle_number"])
        if not trail or trail[-1] != step:
            trail.append(step)
        # Second-cycle growth phase reached → the loop closed.
        if info["cycle_number"] >= 2 and info["phase"] in {"vegetative", "active_growth"}:
            break
        _backdate_open_phase(env.phase_repo, plant)
        env.task.check_auto_transitions()
    return trail


class TestPerennialCycleLoop:
    def test_strawberry_loops_into_a_new_vegetative_cycle(self, _task_env) -> None:
        trail = _run_year(_task_env, _task_env.strawberry)

        phases = [p for p, _c in trail]
        # Full first-year run, in order, without any manual phase edit.
        assert phases[:7] == [
            "establishment",
            "sprouting",
            "vegetative",
            "flowering",
            "fruiting",
            "ripening",
            "dormancy",
        ]
        # The terminal dormancy loops back to the sprouting restart anchor (NOT
        # establishment — E4) and then on to a fresh vegetative phase in cycle 2.
        assert ("sprouting", 2) in trail
        assert ("vegetative", 2) in trail
        # establishment (once-only) is never revisited on the restart.
        assert phases.count("establishment") == 1

    def test_evergreen_staude_loops_into_a_new_active_growth_cycle(self, _task_env) -> None:
        trail = _run_year(_task_env, _task_env.ficus)

        phases = [p for p, _c in trail]
        assert phases[:4] == ["establishment", "active_growth", "flowering", "maintenance"]
        # maintenance (terminal) restarts at active_growth in a new cycle.
        assert ("active_growth", 2) in trail
        assert phases.count("establishment") == 1

    def test_no_manual_transition_needed(self, _task_env) -> None:
        """The whole year advances purely through the Celery auto-transition task."""
        result = None
        for _ in range(30):
            info = _task_env.phase_service.get_current_phase("plant-strawberry")
            if info["cycle_number"] >= 2:
                break
            _backdate_open_phase(_task_env.phase_repo, _task_env.strawberry)
            result = _task_env.task.check_auto_transitions()
        assert result is not None
        # Every step reported a transition (strawberry + ficus both advance).
        assert result["transitioned"] >= 1
        assert result["errors"] == 0


class TestInstanceCycleOverride:
    """DoD (#565 Phase 2): a per-instance ``cultivation_cycle_type`` override changes
    the effective growth flow END-TO-END through the real task/engine/service — driven
    entirely by the single ``resolve_effective_cycle`` cascade (ADR-006 E1).
    """

    def _max_cycle(self, trail: list[tuple[str, int]]) -> int:
        return max((c for _p, c in trail), default=1)

    def test_annual_override_on_perennial_species_does_not_restart(self, _task_env) -> None:
        """Override 'annual' on a perennial strawberry → it terminates at dormancy,
        the cycle NEVER restarts (the annual user intent wins over the species cycle)."""
        _task_env.strawberry.cultivation_cycle_type = CycleType.ANNUAL

        trail = _run_year(_task_env, _task_env.strawberry)

        phases = [p for p, _c in trail]
        # It still runs the full linear first year …
        assert "dormancy" in phases
        # … but the terminal dormancy does NOT loop: no cycle-2 growth phase, cycle stays 1.
        assert ("sprouting", 2) not in trail
        assert ("vegetative", 2) not in trail
        assert self._max_cycle(trail) == 1

    def test_perennial_override_on_annual_species_restarts(self, _task_env) -> None:
        """Override 'perennial' on the annual-by-default tomato → its cyclic sequence
        loops back into a new vegetative growth cycle (cycle 2)."""
        _task_env.tomato.cultivation_cycle_type = CycleType.PERENNIAL

        trail = _run_year(_task_env, _task_env.tomato)

        assert ("sprouting", 2) in trail
        assert ("vegetative", 2) in trail
        assert self._max_cycle(trail) == 2

    def test_annual_default_on_tomato_does_not_restart(self, _task_env) -> None:
        """Baseline: without an override the tomato inherits its ANNUAL species default
        (resolve_effective_cycle species tier) and does NOT loop."""
        trail = _run_year(_task_env, _task_env.tomato)

        assert ("vegetative", 2) not in trail
        assert self._max_cycle(trail) == 1

    def test_reclassified_tender_perennial_species_does_not_restart(self, _task_env) -> None:
        """ADR-006 E1 negative proof for the seed reclassification, end-to-end.

        Reclassifying tomato botanically PERENNIAL (to activate grown_as_annual) while its
        SPECIES cultivation_cycle_type stays ANNUAL — with NO per-instance override — must
        still terminate at dormancy without looping: the species-tier cultivation cycle wins
        in resolve_effective_cycle, so the real task/engine never restarts it.
        """
        _task_env.lifecycle_repo._by_species["sp-tomato"] = LifecycleConfig(
            species_key="sp-tomato",
            cycle_type=CycleType.PERENNIAL,
            cultivation_cycle_type=CycleType.ANNUAL,
        )

        trail = _run_year(_task_env, _task_env.tomato)

        assert ("sprouting", 2) not in trail
        assert ("vegetative", 2) not in trail
        assert self._max_cycle(trail) == 1
