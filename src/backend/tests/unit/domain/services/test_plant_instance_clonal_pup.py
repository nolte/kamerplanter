"""Tests for clonal continuation of monocarpic mothers (REQ-003 D10 / REQ-017).

When a **monocarpic** mother auto-transitions into its terminal reproductive
phase (``flowering`` / ``fruit_development`` / ``ripening``), the service spawns
exactly **one** new plant instance — the clonal pup — instead of restarting the
mother's cycle. The pup is forced into ``pup_establishment`` (falling back to the
species' first phase), inherits the mother's tenant / species / cultivar /
location but NOT its slot, is linked back to the mother by a ``descended_from``
edge, and is recorded as a ``PropagationEvent(method='clone')``. Re-evaluation is
idempotent (no second pup / edge).
"""

from datetime import date
from unittest.mock import MagicMock

from app.common.enums import CycleType, FloweringStrategy
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.plant_instance import PlantInstance
from app.domain.services.plant_instance_service import PlantInstanceService


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

        def _create(pup: PlantInstance) -> PlantInstance:
            pup.key = "pup-1"
            return pup

        self.plant_repo.create.side_effect = _create

        self.phase_repo.get_lifecycle_by_species.return_value = _lifecycle()
        # species sequence includes a dedicated pup-entry phase.
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

    def test_pup_spawned_at_pup_establishment_with_inherited_attrs(self) -> None:
        pup = self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        assert pup is not None
        assert pup.current_phase_key == "ph-pup"  # forced pup_establishment (R2)
        assert pup.mother_key == "mother-1"  # denormalized lineage field (R5)
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
        self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        self.plant_repo.create_descended_from_edge.assert_called_once_with("pup-1", "mother-1")

    def test_clone_propagation_event_persisted(self) -> None:
        self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        self.propagation.record.assert_called_once()
        event = self.propagation.record.call_args[0][0]
        assert event.method == "clone"
        assert event.parent_plant_keys == ["mother-1"]
        assert event.child_plant_keys == ["pup-1"]
        assert event.tenant_key == "tenant-a"  # tenant carried onto the event (R10)

    def test_not_a_cycle_restart(self) -> None:
        """R8: continuation is a new instance — the mother is never mutated and no
        cycle-restart history is written for it (only the pup's initial history)."""
        self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        self.plant_repo.update.assert_not_called()
        # the only phase history created belongs to the pup, not the mother.
        self.phase_repo.create_phase_history.assert_called_once()
        history = self.phase_repo.create_phase_history.call_args[0][0]
        assert history.plant_instance_key == "pup-1"
        assert history.transition_reason == "clonal_pup"

    def test_idempotent_no_second_pup(self) -> None:
        """R7: a mother that already has a pup (inbound descended_from edge) does
        not spawn a second one on re-evaluation."""
        self.plant_repo.has_descendants.return_value = True

        result = self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        assert result is None
        self.plant_repo.create.assert_not_called()
        self.plant_repo.create_descended_from_edge.assert_not_called()
        self.propagation.record.assert_not_called()

    def test_phase_fallback_when_no_pup_establishment(self) -> None:
        """R2: a species whose sequence has no dedicated pup-entry phase falls back
        to its first phase."""
        self.phase_repo.get_phases_by_lifecycle.return_value = [
            _phase("ph-seedling", "seedling", 0),
            _phase("ph-flowering", "flowering", 2, terminal=True),
        ]

        pup = self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        assert pup is not None
        assert pup.current_phase_key == "ph-seedling"  # first phase of the sequence

    def test_non_monocarpic_mother_is_left_alone(self) -> None:
        """A polycarpic perennial keeps its normal (restart) path — no pup spawn."""
        self.phase_repo.get_lifecycle_by_species.return_value = _lifecycle(FloweringStrategy.POLYCARPIC)

        result = self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        assert result is None
        self.plant_repo.create.assert_not_called()
        self.plant_repo.create_descended_from_edge.assert_not_called()

    def test_non_terminal_phase_does_not_spawn(self) -> None:
        """Entering a pre-terminal phase (still vegetative) must not spawn a pup."""
        result = self._service().handle_monocarpic_terminal_transition("mother-1", "juvenile")

        assert result is None
        self.plant_repo.create.assert_not_called()

    def test_cross_tenant_isolation_pup_inherits_mother_tenant(self) -> None:
        """R10 / SEC-001: the pup and its clone event carry the mother's tenant_key."""
        self.mother.tenant_key = "tenant-b"

        pup = self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        assert pup is not None
        assert pup.tenant_key == "tenant-b"
        event = self.propagation.record.call_args[0][0]
        assert event.tenant_key == "tenant-b"

    def test_unknown_mother_is_noop(self) -> None:
        self.plant_repo.get_by_key.return_value = None

        result = self._service().handle_monocarpic_terminal_transition("ghost", "flowering")

        assert result is None
        self.plant_repo.create.assert_not_called()

    def test_missing_lifecycle_is_noop(self) -> None:
        self.phase_repo.get_lifecycle_by_species.return_value = None

        result = self._service().handle_monocarpic_terminal_transition("mother-1", "flowering")

        assert result is None
        self.plant_repo.create.assert_not_called()

    def test_spawn_without_propagation_service_still_creates_pup_and_edge(self) -> None:
        """The propagation event is optional; the pup and lineage edge are not."""
        pup = self._service(with_propagation=False).handle_monocarpic_terminal_transition("mother-1", "flowering")

        assert pup is not None
        self.plant_repo.create_descended_from_edge.assert_called_once_with("pup-1", "mother-1")
