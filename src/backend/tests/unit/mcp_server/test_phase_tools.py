"""REQ-033 §2 / issue #949 — the growth-phase and lifecycle tools.

The fixtures below reproduce the exact situation the issue was filed from, because
that is what the tools have to be able to describe:

* *Yucca gigantea* — evergreen, perennial, polycarpic — bound to ``indoor_default``,
  a 126-day annual cycle whose terminal ``ripening`` phase allows a harvest. Nothing
  in ``get_plant``'s ``current_phase_key: null`` could express any of that.
* An instance sitting in an **empty** phase for 50 days: an open history record whose
  ``phase_key`` resolves to no phase at all. That is neither "never initialised" nor
  "between cycles", and every one of the three needs a different action.

Every tool is also asserted to be reachable through the *registry*, not merely
importable — a tool that exists as a class but never registers is invisible to
``tools/list`` while its own unit tests keep passing, a failure mode this
repository has hit.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.common.enums import CycleType, McpPermission, TenantRole
from app.common.exceptions import NotFoundError
from app.domain.models.phase import PhaseHistory
from app.domain.models.phase_sequence import PhaseSequence
from app.mcp_server.base import McpToolError
from app.mcp_server.context import ToolContext
from app.mcp_server.principal import McpPrincipal, McpTenantMembership
from app.mcp_server.registry import load_tools
from app.mcp_server.tools.phases import (
    PHASE_STATE_BETWEEN_CYCLES,
    PHASE_STATE_IN_PHASE,
    PHASE_STATE_NEVER_INITIALISED,
    PHASE_STATE_UNRESOLVED,
    AssignSpeciesPhaseSequence,
    GetPlantPhaseHistory,
    GetPlantPhaseStatus,
    GetSpeciesLifecycle,
    GetSpeciesPhaseSequence,
    ListPhaseSequences,
    ListSpeciesByPhaseSequence,
    TransitionPlantPhase,
)

# ── The real `indoor_default` shape from the issue ────────────────────────────
_INDOOR_DEFAULT_ROWS = [
    ("seedling", 0, 14, False, False),
    ("vegetative", 1, 28, False, False),
    ("flowering", 2, 56, False, False),
    ("flushing", 3, 14, False, False),
    ("ripening", 4, 14, True, True),  # terminal, allows_harvest
]

_EVERGREEN_ROWS = [
    ("establishment", 0, 60, False, False),
    ("active_growth", 1, 120, False, False),
    ("flowering", 2, 45, False, False),
    ("maintenance", 3, 140, True, False),  # terminal but restarts, no harvest
]


def _membership() -> McpTenantMembership:
    return McpTenantMembership(
        tenant_key="t-mein-garten",
        tenant_slug="mein-garten",
        tenant_name="Mein Garten",
        role=TenantRole.LEAD,
    )


def _ctx(**services) -> ToolContext:
    principal = McpPrincipal(account_key="u-1", display_name="Gardener", memberships=(_membership(),))
    return ToolContext(principal, _membership(), services=services)


def _entries(rows, seq_key: str) -> list[dict]:
    """``get_full_sequence``-shaped entries: enriched dicts, duration already resolved."""

    return [
        {
            "key": f"{seq_key}-e{order}",
            "phase_sequence_key": seq_key,
            "phase_definition_key": f"def-{name}",
            "sequence_order": order,
            "override_duration_days": duration,
            "effective_duration_days": duration,
            "is_terminal": is_terminal,
            "allows_harvest": allows_harvest,
            "is_recurring": False,
            "phase_definition": {
                "name": name,
                "display_name": name.replace("_", " ").title(),
                "display_name_de": "",
                "stress_tolerance": "medium",
                "watering_interval_days": 7,
            },
        }
        for name, order, duration, is_terminal, allows_harvest in rows
    ]


_INDOOR_DEFAULT = PhaseSequence(
    _key="21507465",
    name="indoor_default",
    display_name="Indoor Default Cycle",
    cycle_type=CycleType.ANNUAL,
    is_repeating=False,
    is_system=True,
)
_EVERGREEN = PhaseSequence(
    _key="19013377",
    name="evergreen_foliage_perennial",
    display_name="Evergreen Foliage Perennial",
    cycle_type=CycleType.PERENNIAL,
    is_repeating=True,
    cycle_restart_entry_order=1,
    is_system=True,
)


def _sequence_service(*, bound: PhaseSequence | None = _INDOOR_DEFAULT) -> MagicMock:
    by_key = {"21507465": (_INDOOR_DEFAULT, _INDOOR_DEFAULT_ROWS), "19013377": (_EVERGREEN, _EVERGREEN_ROWS)}

    def _full(key: str) -> dict:
        sequence, rows = by_key[key]
        return {**sequence.model_dump(), "entries": _entries(rows, key)}

    def _get(key: str) -> PhaseSequence:
        if key not in by_key:
            raise NotFoundError("PhaseSequence", key)
        return by_key[key][0]

    service = MagicMock()
    service.get_sequence_by_species.return_value = bound
    service.get_full_sequence.side_effect = _full
    service.get_sequence.side_effect = _get
    service.list_sequences.return_value = ([_INDOOR_DEFAULT, _EVERGREEN], 2)
    return service


class _Plant:
    def __init__(self, phase_key: str | None = None):
        self.key = "11507329"
        self.instance_id = "YUCCA-0617-DIJ"
        self.plant_name = "Yucca"
        self.species_key = "11507159"
        self.planted_on = "2026-06-16"
        self.current_phase_key = phase_key


def _plant_service(plant: _Plant | None = None) -> MagicMock:
    """Override for ``ctx.plant_service``.

    Note the service-dict key is ``plant_instance_service`` — that is what
    ``ToolContext.plant_service`` resolves; passing ``plant_service`` instead
    silently falls through to the real dependency factory and hits ArangoDB.
    """

    service = MagicMock()
    service.get_plant.return_value = plant or _Plant()
    return service


class TestGetSpeciesPhaseSequence:
    @pytest.mark.asyncio
    async def test_it_returns_the_two_fields_that_separate_a_tree_from_a_vegetable(self) -> None:
        ctx = _ctx(phase_sequence_service=_sequence_service())
        result = await GetSpeciesPhaseSequence().run(ctx, GetSpeciesPhaseSequence.Input(species_key="11507159"))

        sequence = result.data["sequence"]
        assert sequence["cycle_type"] == "annual"
        assert sequence["is_repeating"] is False
        assert sequence["dormancy_required"] is False

    @pytest.mark.asyncio
    async def test_every_entry_carries_the_three_flags_a_harvest_judgement_needs(self) -> None:
        ctx = _ctx(phase_sequence_service=_sequence_service())
        result = await GetSpeciesPhaseSequence().run(ctx, GetSpeciesPhaseSequence.Input(species_key="11507159"))

        entries = result.data["sequence"]["entries"]
        assert [e["name"] for e in entries] == [
            "seedling",
            "vegetative",
            "flowering",
            "flushing",
            "ripening",
        ]
        assert all({"effective_duration_days", "is_terminal", "allows_harvest"} <= e.keys() for e in entries)
        # Ordered by sequence_order, not by whatever the store happened to return:
        # a caller reads "what comes next" straight off the list.
        assert [e["sequence_order"] for e in entries] == [0, 1, 2, 3, 4]
        assert entries[-1]["is_terminal"] is True
        assert entries[-1]["allows_harvest"] is True

    @pytest.mark.asyncio
    async def test_it_derives_the_126_days_that_made_the_issue_legible(self) -> None:
        ctx = _ctx(phase_sequence_service=_sequence_service())
        result = await GetSpeciesPhaseSequence().run(ctx, GetSpeciesPhaseSequence.Input(species_key="11507159"))

        sequence = result.data["sequence"]
        assert sequence["total_duration_days"] == 126
        # The composite that says "this plant is scheduled to die after a harvest".
        assert sequence["terminates_in_harvest"] is True
        assert "terminal harvest phase" in result.summary

    @pytest.mark.asyncio
    async def test_a_repeating_perennial_cycle_does_not_terminate_in_harvest(self) -> None:
        ctx = _ctx(phase_sequence_service=_sequence_service(bound=_EVERGREEN))
        result = await GetSpeciesPhaseSequence().run(ctx, GetSpeciesPhaseSequence.Input(species_key="11507159"))

        sequence = result.data["sequence"]
        assert sequence["is_repeating"] is True
        assert sequence["terminates_in_harvest"] is False
        assert sequence["has_harvest_phase"] is False

    @pytest.mark.asyncio
    async def test_an_unbound_species_says_so_instead_of_returning_an_empty_sequence(self) -> None:
        """ "Bound to nothing" and "bound to something empty" are different answers."""

        ctx = _ctx(phase_sequence_service=_sequence_service(bound=None))
        result = await GetSpeciesPhaseSequence().run(ctx, GetSpeciesPhaseSequence.Input(species_key="unknown"))

        assert result.data["sequence"] is None
        assert "not bound" in result.summary


class TestListPhaseSequences:
    @pytest.mark.asyncio
    async def test_it_returns_the_catalogue_so_an_alternative_can_be_named(self) -> None:
        ctx = _ctx(phase_sequence_service=_sequence_service())
        result = await ListPhaseSequences().run(ctx, ListPhaseSequences.Input())

        names = [item["name"] for item in result.data["items"]]
        assert "evergreen_foliage_perennial" in names
        candidate = next(i for i in result.data["items"] if i["name"] == "evergreen_foliage_perennial")
        # Enough to pick it without a second call.
        assert candidate["cycle_type"] == "perennial"
        assert candidate["is_repeating"] is True

    @pytest.mark.asyncio
    async def test_entries_are_off_by_default_and_available_on_request(self) -> None:
        ctx = _ctx(phase_sequence_service=_sequence_service())
        compact = await ListPhaseSequences().run(ctx, ListPhaseSequences.Input())
        assert "entries" not in compact.data["items"][0]

        full = await ListPhaseSequences().run(ctx, ListPhaseSequences.Input(include_entries=True))
        assert full.data["items"][0]["entries"]

    @pytest.mark.asyncio
    async def test_the_query_filter_searches_the_whole_catalogue_not_one_page(self) -> None:
        # limit=1 must not turn "on page 2" into "does not exist".
        ctx = _ctx(phase_sequence_service=_sequence_service())
        result = await ListPhaseSequences().run(ctx, ListPhaseSequences.Input(query="evergreen", limit=1))

        assert result.data["matched"] == 1
        assert result.data["items"][0]["name"] == "evergreen_foliage_perennial"


class TestListSpeciesByPhaseSequence:
    @pytest.mark.asyncio
    async def test_the_reverse_lookup_surfaces_a_template_collision(self) -> None:
        """The strongest verification lever the investigation had.

        Yucca sharing a sequence with Rosenkohl and Porree is what turned "this
        looks off" into "this is a systemic template collision".
        """

        service = _sequence_service()
        service.get_species_for_sequence.return_value = [
            {"key": "11507159", "scientific_name": "Yucca gigantea", "common_names": ["Yucca-Palme"]},
            {"key": "s-2", "scientific_name": "Brassica oleracea", "common_names": ["Rosenkohl"]},
            {"key": "s-3", "scientific_name": "Allium porrum", "common_names": ["Porree"]},
        ]
        ctx = _ctx(phase_sequence_service=service)
        result = await ListSpeciesByPhaseSequence().run(ctx, ListSpeciesByPhaseSequence.Input(sequence_key="21507465"))

        assert result.data["total"] == 3
        assert result.data["cycle_type"] == "annual"
        assert {i["scientific_name"] for i in result.data["items"]} == {
            "Yucca gigantea",
            "Brassica oleracea",
            "Allium porrum",
        }

    @pytest.mark.asyncio
    async def test_an_unknown_sequence_raises_rather_than_reporting_zero_species(self) -> None:
        service = _sequence_service()
        ctx = _ctx(phase_sequence_service=service)
        with pytest.raises(NotFoundError):
            await ListSpeciesByPhaseSequence().run(ctx, ListSpeciesByPhaseSequence.Input(sequence_key="nope"))


class _Lifecycle:
    def __init__(self, **overrides):
        self.key = "lc-1"
        self.cycle_type = CycleType.PERENNIAL
        self.cultivation_cycle_type = None
        self.flowering_strategy = "polycarpic"
        self.growth_determinacy = None
        self.typical_lifespan_years = 50
        self.dormancy_required = False
        self.vernalization_required = False
        self.photoperiod_type = "day_neutral"
        self.critical_day_length_hours = None
        self.max_seasons = None
        self.first_bearing_year = 3
        self.expected_productive_years = None
        self.phase_sequence_key = "19013377"
        self.__dict__.update(overrides)


class TestGetSpeciesLifecycle:
    @pytest.mark.asyncio
    async def test_it_exposes_the_layer_where_perennial_and_polycarpic_are_stated(self) -> None:
        service = MagicMock()
        service.get_lifecycle_by_species.return_value = _Lifecycle()
        ctx = _ctx(phase_service=service)

        result = await GetSpeciesLifecycle().run(ctx, GetSpeciesLifecycle.Input(species_key="11507159"))

        lifecycle = result.data["lifecycle"]
        # Exactly the facts that make the annual sequence wrong for this species.
        assert lifecycle["cycle_type"] == "perennial"
        assert lifecycle["flowering_strategy"] == "polycarpic"
        assert lifecycle["typical_lifespan_years"] == 50
        assert lifecycle["dormancy_required"] is False
        assert lifecycle["phase_sequence_key"] == "19013377"

    @pytest.mark.asyncio
    async def test_a_missing_lifecycle_is_reported_as_the_finding_it_is(self) -> None:
        """``ENTITY_NOT_FOUND`` was itself the finding — it routes the resolver's fallback."""

        service = MagicMock()
        service.get_lifecycle_by_species.side_effect = NotFoundError("LifecycleConfig for species", "11507159")
        ctx = _ctx(phase_service=service)

        result = await GetSpeciesLifecycle().run(ctx, GetSpeciesLifecycle.Input(species_key="11507159"))

        assert result.data["lifecycle"] is None
        assert "no lifecycle configuration" in result.summary

    @pytest.mark.asyncio
    async def test_grown_as_annual_is_derived_the_same_way_rest_derives_it(self) -> None:
        service = MagicMock()
        service.get_lifecycle_by_species.return_value = _Lifecycle(
            cycle_type=CycleType.PERENNIAL, cultivation_cycle_type=CycleType.ANNUAL
        )
        ctx = _ctx(phase_service=service)

        result = await GetSpeciesLifecycle().run(ctx, GetSpeciesLifecycle.Input(species_key="sp-tomato"))

        assert result.data["lifecycle"]["grown_as_annual"] is True


def _history(*, phase_key: str = "", phase_name: str = "", open_record: bool = True) -> PhaseHistory:
    entered = datetime.now(UTC) - timedelta(days=50)
    return PhaseHistory(
        _key="11507331",
        plant_instance_key="11507329",
        phase_key=phase_key,
        phase_name=phase_name,
        entered_at=entered,
        exited_at=None if open_record else entered + timedelta(days=20),
        cycle_number=1,
        transition_reason="initial",
    )


def _phase_service(current: dict, history: list[PhaseHistory]) -> MagicMock:
    service = MagicMock()
    service.get_current_phase.return_value = current
    service.get_phase_history.return_value = history
    return service


class TestGetPlantPhaseStatus:
    """The discriminator ``get_plant``'s bare ``current_phase_key: null`` cannot express."""

    @pytest.mark.asyncio
    async def test_the_investigated_instance_reads_as_unresolved_not_as_uninitialised(self) -> None:
        # The exact snapshot from the issue: phase "" / phase_key "", 50 days,
        # one open history record. The plant HAS been started; its phase points
        # at nothing. Treating that as "never initialised" would prescribe the
        # wrong repair.
        ctx = _ctx(
            plant_instance_service=_plant_service(),
            phase_service=_phase_service(
                {
                    "phase": "",
                    "phase_key": "",
                    "days_in_phase": 50,
                    "next_phase": None,
                    "cycle_number": 1,
                    "has_harvest_phase": True,
                },
                [_history()],
            ),
        )
        result = await GetPlantPhaseStatus().run(ctx, GetPlantPhaseStatus.Input(plant_key="11507329"))

        assert result.data["phase_state"] == PHASE_STATE_UNRESOLVED
        assert result.data["days_in_phase"] == 50
        assert result.data["has_harvest_phase"] is True
        assert "not advancing" in result.summary

    @pytest.mark.asyncio
    async def test_a_plant_with_no_history_at_all_reads_as_never_initialised(self) -> None:
        ctx = _ctx(
            plant_instance_service=_plant_service(),
            phase_service=_phase_service(
                {"phase": "", "phase_key": "", "days_in_phase": 0, "cycle_number": 1},
                [],
            ),
        )
        result = await GetPlantPhaseStatus().run(ctx, GetPlantPhaseStatus.Input(plant_key="11507329"))

        assert result.data["phase_state"] == PHASE_STATE_NEVER_INITIALISED
        assert "never initialised" in result.summary

    @pytest.mark.asyncio
    async def test_a_completed_cycle_with_no_open_record_reads_as_between_cycles(self) -> None:
        ctx = _ctx(
            plant_instance_service=_plant_service(),
            phase_service=_phase_service(
                {"phase": "", "phase_key": "", "days_in_phase": 0, "cycle_number": 2},
                [_history(phase_key="e-3", phase_name="dormancy", open_record=False)],
            ),
        )
        result = await GetPlantPhaseStatus().run(ctx, GetPlantPhaseStatus.Input(plant_key="11507329"))

        assert result.data["phase_state"] == PHASE_STATE_BETWEEN_CYCLES

    @pytest.mark.asyncio
    async def test_a_healthy_plant_reports_its_phase_next_phase_and_cycle(self) -> None:
        ctx = _ctx(
            plant_instance_service=_plant_service(),
            phase_service=_phase_service(
                {
                    "phase": "active_growth",
                    "phase_key": "19013377-e1",
                    "days_in_phase": 12,
                    "next_phase": "flowering",
                    "cycle_number": 3,
                    "cycle_type": "perennial",
                    "has_harvest_phase": False,
                },
                [_history(phase_key="19013377-e1", phase_name="active_growth")],
            ),
        )
        result = await GetPlantPhaseStatus().run(ctx, GetPlantPhaseStatus.Input(plant_key="11507329"))

        assert result.data["phase_state"] == PHASE_STATE_IN_PHASE
        assert result.data["next_phase"] == "flowering"
        assert result.data["cycle_number"] == 3
        assert result.data["days_in_phase"] == 12

    @pytest.mark.asyncio
    async def test_the_read_is_tenant_scoped(self) -> None:
        plant_service = _plant_service()
        ctx = _ctx(
            plant_instance_service=plant_service,
            phase_service=_phase_service({"phase": "", "phase_key": ""}, []),
        )
        await GetPlantPhaseStatus().run(ctx, GetPlantPhaseStatus.Input(plant_key="11507329"))

        # A foreign key must raise not_found in the service, which only happens
        # when the tenant is actually carried into the lookup (SEC-001).
        plant_service.get_plant.assert_called_once_with("11507329", tenant_key="t-mein-garten")


class TestGetPlantPhaseHistory:
    @pytest.mark.asyncio
    async def test_it_returns_transitions_with_their_reason(self) -> None:
        ctx = _ctx(
            plant_instance_service=_plant_service(),
            phase_service=_phase_service({}, [_history()]),
        )
        result = await GetPlantPhaseHistory().run(ctx, GetPlantPhaseHistory.Input(plant_key="11507329"))

        row = result.data["items"][0]
        assert row["transition_reason"] == "initial"
        assert row["is_current"] is True
        assert row["cycle_number"] == 1

    @pytest.mark.asyncio
    async def test_an_empty_phase_name_is_kept_because_it_is_the_symptom(self) -> None:
        ctx = _ctx(
            plant_instance_service=_plant_service(),
            phase_service=_phase_service({}, [_history(phase_name="")]),
        )
        result = await GetPlantPhaseHistory().run(ctx, GetPlantPhaseHistory.Input(plant_key="11507329"))

        assert "phase_name" in result.data["items"][0]
        assert result.data["items"][0]["phase_name"] == ""

    @pytest.mark.asyncio
    async def test_the_limit_keeps_the_most_recent_transitions(self) -> None:
        base = datetime.now(UTC) - timedelta(days=400)
        rows = [
            PhaseHistory(
                _key=f"h-{i}",
                plant_instance_key="11507329",
                phase_key=f"e-{i}",
                phase_name=f"phase-{i}",
                entered_at=base + timedelta(days=i),
                exited_at=base + timedelta(days=i + 1),
                transition_reason="auto",
            )
            for i in range(10)
        ]
        ctx = _ctx(plant_instance_service=_plant_service(), phase_service=_phase_service({}, rows))

        result = await GetPlantPhaseHistory().run(ctx, GetPlantPhaseHistory.Input(plant_key="11507329", limit=3))

        assert result.data["total"] == 10
        assert [r["phase_name"] for r in result.data["items"]] == ["phase-7", "phase-8", "phase-9"]


class TestTransitionPlantPhase:
    def _ctx_for(self, *, bound: PhaseSequence | None = _INDOOR_DEFAULT) -> tuple[ToolContext, MagicMock]:
        phase_service = _phase_service(
            {"phase": "seedling", "phase_key": "21507465-e0", "days_in_phase": 20},
            [_history(phase_key="21507465-e0", phase_name="seedling")],
        )
        phase_service.transition_phase.return_value = _Plant(phase_key="21507465-e1")
        ctx = _ctx(
            plant_instance_service=_plant_service(),
            phase_service=phase_service,
            phase_sequence_service=_sequence_service(bound=bound),
        )
        return ctx, phase_service

    @pytest.mark.asyncio
    async def test_it_validates_the_target_against_the_species_own_sequence(self) -> None:
        """A key from some other species' sequence would strand the plant."""

        ctx, phase_service = self._ctx_for()
        with pytest.raises(McpToolError) as exc:
            await TransitionPlantPhase().execute(
                ctx,
                TransitionPlantPhase.Input(plant_key="11507329", target_phase_key="19013377-e2"),
            )

        assert exc.value.error_code == "validation.phase_not_in_sequence"
        # The refusal names the legal alternatives instead of leaving the caller guessing.
        assert "21507465-e0" in exc.value.error_details["valid_phase_keys"]
        phase_service.transition_phase.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_species_with_no_sequence_is_refused_with_its_own_code(self) -> None:
        ctx, phase_service = self._ctx_for(bound=None)
        with pytest.raises(McpToolError) as exc:
            await TransitionPlantPhase().execute(
                ctx,
                TransitionPlantPhase.Input(plant_key="11507329", target_phase_key="anything"),
            )

        assert exc.value.error_code == "validation.no_phase_sequence"
        phase_service.transition_phase.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_valid_transition_delegates_to_the_phase_service(self) -> None:
        ctx, phase_service = self._ctx_for()
        result = await TransitionPlantPhase().execute(
            ctx,
            TransitionPlantPhase.Input(
                plant_key="11507329", target_phase_key="21507465-e1", reason="corrected by agent"
            ),
        )

        phase_service.transition_phase.assert_called_once_with(
            "11507329", "21507465-e1", "corrected by agent", force=False
        )
        assert result.data["phase"] == "vegetative"

    @pytest.mark.asyncio
    async def test_the_dry_run_names_a_terminal_harvest_before_it_happens(self) -> None:
        ctx, phase_service = self._ctx_for()
        result = await TransitionPlantPhase().preview(
            ctx,
            TransitionPlantPhase.Input(plant_key="11507329", target_phase_key="21507465-e4", dry_run=True),
        )

        assert result.data["target_is_terminal"] is True
        assert result.data["target_allows_harvest"] is True
        assert result.data["from_phase"] == "seedling"
        phase_service.transition_phase.assert_not_called()

    @pytest.mark.asyncio
    async def test_the_dry_run_refuses_what_the_write_would_refuse(self) -> None:
        """A preview that approves an invalid transition is worse than no preview."""

        ctx, _phase_service = self._ctx_for()
        with pytest.raises(McpToolError):
            await TransitionPlantPhase().preview(
                ctx,
                TransitionPlantPhase.Input(plant_key="11507329", target_phase_key="19013377-e2", dry_run=True),
            )


class TestAssignSpeciesPhaseSequence:
    def _ctx_for(self, *, bound: PhaseSequence | None = _INDOOR_DEFAULT) -> tuple[ToolContext, MagicMock]:
        phase_service = MagicMock()
        phase_service.assign_phase_sequence.return_value = {
            "sequence_key": "19013377",
            "previous_sequence_key": bound.key if bound else None,
            "lifecycle_key": "lc-1",
        }
        ctx = _ctx(phase_service=phase_service, phase_sequence_service=_sequence_service(bound=bound))
        return ctx, phase_service

    @pytest.mark.asyncio
    async def test_it_binds_through_the_service_that_writes_the_edge(self) -> None:
        ctx, phase_service = self._ctx_for()
        result = await AssignSpeciesPhaseSequence().execute(
            ctx,
            AssignSpeciesPhaseSequence.Input(species_key="11507159", sequence_key="19013377"),
        )

        phase_service.assign_phase_sequence.assert_called_once_with("11507159", "19013377")
        assert result.data["sequence_name"] == "evergreen_foliage_perennial"
        assert result.data["cycle_type"] == "perennial"
        assert result.data["is_repeating"] is True

    @pytest.mark.asyncio
    async def test_it_reports_the_binding_it_replaced(self) -> None:
        ctx, _phase_service = self._ctx_for()
        result = await AssignSpeciesPhaseSequence().execute(
            ctx,
            AssignSpeciesPhaseSequence.Input(species_key="11507159", sequence_key="19013377"),
        )

        assert result.data["replaced_sequence_key"] == "21507465"
        assert "previous binding was replaced" in result.summary

    @pytest.mark.asyncio
    async def test_the_dry_run_names_what_would_be_lost_and_writes_nothing(self) -> None:
        ctx, phase_service = self._ctx_for()
        result = await AssignSpeciesPhaseSequence().preview(
            ctx,
            AssignSpeciesPhaseSequence.Input(species_key="11507159", sequence_key="19013377", dry_run=True),
        )

        assert result.data["replaces_sequence_name"] == "indoor_default"
        assert result.data["sequence_name"] == "evergreen_foliage_perennial"
        phase_service.assign_phase_sequence.assert_not_called()

    @pytest.mark.asyncio
    async def test_an_unknown_sequence_is_refused_before_anything_is_written(self) -> None:
        ctx, phase_service = self._ctx_for()
        with pytest.raises(NotFoundError):
            await AssignSpeciesPhaseSequence().execute(
                ctx,
                AssignSpeciesPhaseSequence.Input(species_key="11507159", sequence_key="typo"),
            )
        phase_service.assign_phase_sequence.assert_not_called()


class TestTheRegistryActuallyExposesThem:
    """A tool that never registers is invisible to ``tools/list`` and un-callable.

    Asserted through :func:`load_tools` rather than through the imports above,
    because the imports are exactly what keeps passing when registration breaks.
    """

    EXPECTED = {
        "get_species_phase_sequence": (McpPermission.READ, False, False),
        "list_phase_sequences": (McpPermission.READ, False, False),
        "list_species_by_phase_sequence": (McpPermission.READ, False, False),
        "get_species_lifecycle": (McpPermission.READ, False, False),
        "get_plant_phase_status": (McpPermission.READ, False, True),
        "get_plant_phase_history": (McpPermission.READ, False, True),
        "transition_plant_phase": (McpPermission.WRITE, True, True),
        "assign_species_phase_sequence": (McpPermission.SETUP, True, False),
    }

    @pytest.mark.parametrize("name", sorted(EXPECTED))
    def test_the_tool_is_reachable_through_the_registry(self, name: str) -> None:
        assert name in load_tools().names()

    @pytest.mark.parametrize(("name", "expected"), sorted(EXPECTED.items()))
    def test_the_registered_classification_matches_the_contract(self, name: str, expected) -> None:
        permission, is_write, tenant_scoped = expected
        tool = load_tools().get(name)
        assert tool.permission == permission
        assert tool.write is is_write
        assert tool.tenant_scoped is tenant_scoped

    @pytest.mark.parametrize("name", sorted(EXPECTED))
    def test_the_published_schema_is_readable_by_a_recipe(self, name: str) -> None:
        spec = load_tools().get(name).spec()
        assert spec.input_schema["type"] == "object"
        assert spec.input_schema.get("properties")
        assert spec.description and not spec.description.endswith(("...", ":"))

    @pytest.mark.parametrize("name", ["transition_plant_phase", "assign_species_phase_sequence"])
    def test_both_writes_declare_dry_run_and_idempotency(self, name: str) -> None:
        properties = load_tools().get(name).spec().input_schema["properties"]
        assert "dry_run" in properties
        assert "idempotency_key" in properties

    def test_the_global_write_tool_carries_no_tenant_argument(self) -> None:
        """It acts on shared catalogue data; a ``tenant`` field would be a lie.

        ``tenant_scoped`` is derived from the Input model, so a stray ``tenant``
        field here would make the dispatcher demand a tenant it then never uses.
        """

        properties = load_tools().get("assign_species_phase_sequence").spec().input_schema["properties"]
        assert "tenant" not in properties

    def test_the_tenant_scoped_tools_do_carry_one(self) -> None:
        for name in ("get_plant_phase_status", "get_plant_phase_history", "transition_plant_phase"):
            assert "tenant" in load_tools().get(name).spec().input_schema["properties"], name


class TestGetSpeciesInfoExposesTheResolversInputs:
    """§949: an agent cannot assess a resolution whose inputs it cannot see."""

    @pytest.mark.asyncio
    async def test_the_discriminator_fields_are_returned(self) -> None:
        from app.mcp_server.tools.species import GetSpeciesInfo

        species = MagicMock()
        species.key = "11507159"
        species.scientific_name = "Yucca gigantea"
        species.common_names = ["Yucca-Palme"]
        species.genus = "Yucca"
        species.plant_category = "indoor_houseplant"
        species.photosynthesis_type = "cam"
        species.indoor_suitable = "excellent"
        species.growth_habit = "tree"
        species.mature_height_cm = "800-1200"
        species.frost_sensitivity = "sensitive"
        species.seed_profile = None
        species.growing_periods = []

        service = MagicMock()
        service.get_species.return_value = species
        service.get_compatible_species.return_value = []
        service.list_cultivars.return_value = []
        ctx = _ctx(species_service=service)

        result = await GetSpeciesInfo().run(ctx, GetSpeciesInfo.Input(species_key="11507159", include_cultivars=False))

        for field in (
            "plant_category",
            "photosynthesis_type",
            "indoor_suitable",
            "growth_habit",
            "mature_height_cm",
            "frost_sensitivity",
        ):
            assert field in result.data, f"{field} is a resolver input and must be visible"
