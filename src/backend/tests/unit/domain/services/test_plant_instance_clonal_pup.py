"""Tests for clonal continuation of monocarpic mothers (REQ-003 D10 / REQ-017).

When a **monocarpic** mother **auto**-transitions into the **last phase of its
species sequence** (a reproductive terminal phase), the service spawns exactly
**one** new plant instance — the clonal pup — instead of restarting the mother's
cycle. The pup is forced into ``pup_establishment`` (falling back to the species'
first phase), inherits the mother's tenant / species / cultivar / location but
NOT its slot, is linked back to the mother by a ``descended_from`` edge, and is
recorded as a ``PropagationEvent(method='clone')``. Re-evaluation is idempotent
(no second pup / edge — keyed on the pup document, not just the edge). A manual
transition never spawns; an intermediate reproductive phase never spawns.
"""

from datetime import date
from unittest.mock import MagicMock

from freezegun import freeze_time

from app.common.enums import CycleType, FloweringStrategy, TransitionTrigger
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_instance_service import PlantInstanceService

AUTO = TransitionTrigger.AUTO
MANUAL = TransitionTrigger.MANUAL


def _mother(**overrides) -> PlantInstance:
    base = {
        "_key": "mother-1",
        "tenant_key": "tenant-a",
        "instance_id": "AGV-1",
        "species_key": "agave",
        "cultivar_key": "cv-1",
        "site_key": "site-1",
        "location_key": "loc-1",
        "slot_key": "slot-1",
        "substrate_key": "sub-1",
        "planted_on": date(2018, 4, 1),
        "current_phase_key": "ph-flowering",
    }
    base.update(overrides)
    return PlantInstance(**base)


def _lifecycle(strategy: FloweringStrategy = FloweringStrategy.MONOCARPIC) -> LifecycleConfig:
    return LifecycleConfig(
        _key="lc-1",
        species_key="agave",
        cycle_type=CycleType.PERENNIAL,
        flowering_strategy=strategy,
    )


def _phase(key: str, name: str, order: int, *, terminal: bool = False) -> GrowthPhase:
    return GrowthPhase(_key=key, name=name, typical_duration_days=30, sequence_order=order, is_terminal=terminal)


class TestClonalPupSpawn:
    def setup_method(self) -> None:
        self.plant_repo = MagicMock()
        self.site_repo = MagicMock()
        self.rotation = MagicMock()
        self.companion = MagicMock()
        self.phase_repo = MagicMock()
        self.propagation = MagicMock()

        self.mother = _mother()
        self.plant_repo.get_by_key.return_value = self.mother
        self.plant_repo.has_descendants.return_value = False
        # Fix #1: idempotency is keyed on the pup DOCUMENT. Default: no pup yet.
        self.plant_repo.get_by_instance_id.return_value = None

        def _create(pup: PlantInstance) -> PlantInstance:
            pup.key = "pup-1"
            return pup

        self.plant_repo.create.side_effect = _create

        self.phase_repo.get_lifecycle_by_species.return_value = _lifecycle()
        # Agave pattern: the sequence's last phase IS flowering (order 3).
        self.phase_repo.get_phases_by_lifecycle.return_value = [
            _phase("ph-pup", "pup_establishment", 0),
            _phase("ph-juv", "juvenile", 1),
            _phase("ph-flowering", "flowering", 3, terminal=True),
        ]
        self.phase_repo.get_phase_by_key.return_value = _phase("ph-pup", "pup_establishment", 0)

    def _service(self, *, with_propagation: bool = True) -> PlantInstanceService:
        return PlantInstanceService(
            self.plant_repo,
            self.site_repo,
            self.rotation,
            self.companion,
            phase_repo=self.phase_repo,
            phase_seq_repo=None,
            propagation_service=self.propagation if with_propagation else None,
        )

    def _handle(self, phase: str = "flowering", *, mother_key: str = "mother-1", trigger: TransitionTrigger = AUTO):
        return self._service().handle_monocarpic_terminal_transition(mother_key, phase, trigger=trigger)

    @freeze_time("2026-07-11")
    def test_pup_spawned_at_pup_establishment_with_inherited_attrs(self) -> None:
        pup = self._handle()

        assert pup is not None
        assert pup.current_phase_key == "ph-pup"  # forced pup_establishment (R2)
        assert pup.mother_key == "mother-1"  # denormalized lineage field (R5)
        assert pup.instance_id == "AGV-1-pup"  # deterministic id (Fix #1)
        # inherited from the mother (R4) …
        assert pup.tenant_key == "tenant-a"
        assert pup.species_key == "agave"
        assert pup.cultivar_key == "cv-1"
        assert pup.location_key == "loc-1"
        assert pup.site_key == "site-1"
        assert pup.planted_on == date.today()  # terminal-transition date
        # … but NOT the slot: the mother still occupies it while senescing (R4).
        assert pup.slot_key is None
        self.plant_repo.create.assert_called_once()

    def test_descended_from_edge_child_to_mother(self) -> None:
        self._handle()

        self.plant_repo.create_descended_from_edge.assert_called_once_with("pup-1", "mother-1")

    def test_clone_propagation_event_persisted(self) -> None:
        self._handle()

        self.propagation.record.assert_called_once()
        event = self.propagation.record.call_args[0][0]
        assert event.method == "clone"
        assert event.parent_plant_keys == ["mother-1"]
        assert event.child_plant_keys == ["pup-1"]
        assert event.tenant_key == "tenant-a"  # tenant carried onto the event (R10)

    def test_not_a_cycle_restart(self) -> None:
        """R8: continuation is a new instance — the mother is never mutated and no
        cycle-restart history is written for it (only the pup's initial history)."""
        self._handle()

        self.plant_repo.update.assert_not_called()
        # the only phase history created belongs to the pup, not the mother.
        self.phase_repo.create_phase_history.assert_called_once()
        history = self.phase_repo.create_phase_history.call_args[0][0]
        assert history.plant_instance_key == "pup-1"
        assert history.transition_reason == "clonal_pup"

    def test_idempotent_no_second_pup_when_descendant_exists(self) -> None:
        """R7: a mother that already has a descendant edge (but no matching pup doc
        under the deterministic id) does not spawn a second one on re-evaluation."""
        self.plant_repo.has_descendants.return_value = True

        result = self._handle()

        assert result is None
        self.plant_repo.create.assert_not_called()
        self.plant_repo.create_descended_from_edge.assert_not_called()
        self.propagation.record.assert_not_called()

    def test_idempotent_existing_complete_pup_is_noop(self) -> None:
        """Fix #1 / R7: an already-spawned pup (doc + edge present) is a clean no-op —
        no second create, no duplicate edge/event."""
        existing = _mother(_key="pup-1", instance_id="AGV-1-pup", slot_key=None)
        self.plant_repo.get_by_instance_id.return_value = existing
        self.plant_repo.has_descendants.return_value = True  # edge already present

        result = self._handle()

        assert result is None
        self.plant_repo.create.assert_not_called()
        self.plant_repo.create_descended_from_edge.assert_not_called()
        self.propagation.record.assert_not_called()

    def test_orphan_pup_lineage_is_backfilled_without_second_create(self) -> None:
        """Fix #1: a partially-spawned orphan pup (doc exists, edge/event missing from
        a prior transient failure) has its lineage completed idempotently — crucially
        WITHOUT a second create that would crash on the unique instance_id index."""
        orphan = _mother(_key="pup-1", instance_id="AGV-1-pup", slot_key=None)
        self.plant_repo.get_by_instance_id.return_value = orphan
        self.plant_repo.has_descendants.return_value = False  # edge is missing

        result = self._handle()

        assert result is None  # not re-spawned
        self.plant_repo.create.assert_not_called()  # no unique-index collision
        # missing edge + event are back-filled.
        self.plant_repo.create_descended_from_edge.assert_called_once_with("pup-1", "mother-1")
        self.propagation.record.assert_called_once()
        event = self.propagation.record.call_args[0][0]
        assert event.parent_plant_keys == ["mother-1"]
        assert event.child_plant_keys == ["pup-1"]

    def test_get_by_instance_id_lookup_is_tenant_scoped(self) -> None:
        """Fix #1 / R10: the pup existence check is constrained to the mother's tenant."""
        self._handle()

        self.plant_repo.get_by_instance_id.assert_called_once_with("AGV-1-pup", tenant_key="tenant-a")

    def test_phase_fallback_when_no_pup_establishment(self) -> None:
        """R2: a species whose sequence has no dedicated pup-entry phase falls back
        to its first phase."""
        self.phase_repo.get_phases_by_lifecycle.return_value = [
            _phase("ph-seedling", "seedling", 0),
            _phase("ph-flowering", "flowering", 2, terminal=True),
        ]

        pup = self._handle()

        assert pup is not None
        assert pup.current_phase_key == "ph-seedling"  # first phase of the sequence

    def test_non_monocarpic_mother_is_left_alone(self) -> None:
        """A polycarpic perennial keeps its normal (restart) path — no pup spawn."""
        self.phase_repo.get_lifecycle_by_species.return_value = _lifecycle(FloweringStrategy.POLYCARPIC)

        result = self._handle()

        assert result is None
        self.plant_repo.create.assert_not_called()
        self.plant_repo.create_descended_from_edge.assert_not_called()

    def test_non_terminal_phase_does_not_spawn(self) -> None:
        """Entering a pre-terminal phase (still vegetative) must not spawn a pup."""
        result = self._handle("juvenile")

        assert result is None
        self.plant_repo.create.assert_not_called()

    # ── Fix #4: spawn only at the ACTUAL last phase of the sequence ────────────

    def _three_phase_reproductive_sequence(self) -> None:
        """A monocarp whose sequence continues past flowering:
        flowering → fruit_development → ripening (ripening is the terminal node)."""
        self.phase_repo.get_phases_by_lifecycle.return_value = [
            _phase("ph-veg", "vegetative", 0),
            _phase("ph-flowering", "flowering", 1),
            _phase("ph-fruit", "fruit_development", 2),
            _phase("ph-ripening", "ripening", 3, terminal=True),
        ]

    def test_no_spawn_at_flowering_when_ripening_still_follows(self) -> None:
        """Fix #4: flowering is reproductive-terminal by role but NOT the last phase —
        no pup is spawned until the sequence's real terminal node."""
        self._three_phase_reproductive_sequence()
        self.mother.current_phase_key = "ph-flowering"

        result = self._handle("flowering")

        assert result is None
        self.plant_repo.create.assert_not_called()

    def test_spawn_at_ripening_the_last_phase(self) -> None:
        """Fix #4: the same monocarp DOES continue once it reaches its last phase."""
        self._three_phase_reproductive_sequence()
        self.mother.current_phase_key = "ph-ripening"

        result = self._handle("ripening")

        assert result is not None
        self.plant_repo.create.assert_called_once()

    def test_agave_pattern_spawns_at_flowering_when_it_is_last(self) -> None:
        """Fix #4: a monocarp whose LAST phase is flowering (agave) still spawns at
        flowering — the gate is 'last phase', not 'not flowering'."""
        # default setup already makes flowering the last phase.
        result = self._handle("flowering")

        assert result is not None
        self.plant_repo.create.assert_called_once()

    # ── Fix #5: only automatic transitions continue a monocarp ─────────────────

    def test_manual_transition_does_not_spawn(self) -> None:
        """Fix #5 / Q1: a manual phase correction into the terminal phase must NOT
        spawn a clonal pup."""
        result = self._handle(trigger=MANUAL)

        assert result is None
        self.plant_repo.create.assert_not_called()
        self.plant_repo.create_descended_from_edge.assert_not_called()

    def test_manual_is_the_default_trigger(self) -> None:
        """The callback contract defaults to MANUAL, so an un-tagged call is inert."""
        result = self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        assert result is None
        self.plant_repo.create.assert_not_called()

    def test_auto_transition_spawns(self) -> None:
        result = self._handle(trigger=AUTO)

        assert result is not None
        self.plant_repo.create.assert_called_once()

    # ── Cross-cutting invariants ───────────────────────────────────────────────

    def test_cross_tenant_isolation_pup_inherits_mother_tenant(self) -> None:
        """R10 / SEC-001: the pup and its clone event carry the mother's tenant_key."""
        self.mother.tenant_key = "tenant-b"

        pup = self._handle()

        assert pup is not None
        assert pup.tenant_key == "tenant-b"
        event = self.propagation.record.call_args[0][0]
        assert event.tenant_key == "tenant-b"

    def test_unknown_mother_is_noop(self) -> None:
        self.plant_repo.get_by_key.return_value = None

        result = self._handle(mother_key="ghost")

        assert result is None
        self.plant_repo.create.assert_not_called()

    def test_missing_lifecycle_is_noop(self) -> None:
        self.phase_repo.get_lifecycle_by_species.return_value = None

        result = self._handle()

        assert result is None
        self.plant_repo.create.assert_not_called()

    def test_spawn_without_propagation_service_still_creates_pup_and_edge(self) -> None:
        """The propagation event is optional; the pup and lineage edge are not."""
        pup = self._service(with_propagation=False).handle_monocarpic_terminal_transition(
            "mother-1", "flowering", trigger=AUTO
        )

        assert pup is not None
        self.plant_repo.create_descended_from_edge.assert_called_once_with("pup-1", "mother-1")

    def test_spawn_failure_is_swallowed_and_logged(self) -> None:
        """Fix #1: a repository failure during spawn must not break the transition —
        it is caught and the callback returns None (retried idempotently later)."""
        self.plant_repo.create.side_effect = RuntimeError("arango down")

        result = self._handle()

        assert result is None
