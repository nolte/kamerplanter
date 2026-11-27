"""The cause class of a ``died`` loss through ``PlantInstanceService`` (REQ-003 E5 v2.23, #2888 F-19).

The production path: ``remove_plant`` checks the class against the pre-fill table, resolves it and stores
it through the real ``PhaseTransitionEngine``; ``get_termination_options`` resolves the table for one
plant from its open phase (E6 premature bolting) and its botanical family (wilt follow-up). Only the
repositories are doubles.
"""

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest

from app.common.enums import (
    FailureCauseClass,
    PathogenConfirmationSource,
    SoilHazard,
    TerminationCause,
    TerminationType,
)
from app.common.exceptions import NotFoundError, ValidationError
from app.domain.models.botanical_family import BotanicalFamily
from app.domain.models.phase import PhaseHistory
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.species import Species
from app.domain.services.plant_instance_service import PlantInstanceService


def _plant() -> PlantInstance:
    return PlantInstance(
        _key="plant-1",
        tenant_key="tenant-a",
        instance_id="P-1",
        species_key="sp-lettuce",
        planted_on=date(2026, 4, 1),
        current_phase_key="ph-bolting",
        current_phase_started_at=datetime(2026, 6, 1, tzinfo=UTC),
    )


def _history(*, name: str = "bolting", premature: bool = True) -> list[PhaseHistory]:
    """A vegetative phase the plant left and the phase it stands in now."""
    return [
        PhaseHistory(
            _key="h-veg",
            plant_instance_key="plant-1",
            phase_key="ph-veg",
            phase_name="vegetative",
            entered_at=datetime(2026, 4, 20, tzinfo=UTC),
            exited_at=datetime(2026, 6, 1, tzinfo=UTC),
        ),
        PhaseHistory(
            _key="h-now",
            plant_instance_key="plant-1",
            phase_key=f"ph-{name}",
            phase_name=name,
            entered_at=datetime(2026, 6, 1, tzinfo=UTC),
            is_premature=premature,
        ),
    ]


class _Families:
    """The one read the service needs of the family catalogue."""

    def __init__(self, *families: BotanicalFamily) -> None:
        self._by_key = {family.key: family for family in families}

    def get_by_key(self, key: str) -> BotanicalFamily | None:
        return self._by_key.get(key)


class _Base:
    def setup_method(self) -> None:
        self.plant_repo = MagicMock()
        self.phase_repo = MagicMock()
        self.species_repo = MagicMock()
        self.plant = _plant()
        self.plant_repo.get_or_raise.return_value = self.plant
        self.plant_repo.get_by_key.return_value = self.plant
        self.plant_repo.update.side_effect = lambda _key, p: p
        self.phase_repo.get_phase_history.return_value = _history()
        self.species_repo.get_by_key.return_value = Species(
            _key="sp-lettuce", scientific_name="Lactuca sativa", family_key="asteraceae"
        )
        self.families = _Families(
            BotanicalFamily(_key="asteraceae", name="Asteraceae"),
            BotanicalFamily(_key="solanaceae", name="Solanaceae"),
        )

    def _service(self) -> PlantInstanceService:
        return PlantInstanceService(
            self.plant_repo,
            MagicMock(),
            MagicMock(),
            MagicMock(),
            phase_repo=self.phase_repo,
            task_repo=MagicMock(),
            species_repo=self.species_repo,
            family_repo=self.families,
        )

    def _stored(self) -> PlantInstance:
        """The plant as handed to the repository by the last write."""
        return self.plant_repo.update.call_args.args[1]


class TestRemoveRecordsTheClass(_Base):
    """acceptance-1 and -4 through ``remove_plant``."""

    @pytest.mark.parametrize(
        ("cause", "expected"),
        [
            (TerminationCause.FROST, FailureCauseClass.ABIOTIC),
            (TerminationCause.BOLTING, FailureCauseClass.ABIOTIC),
            (TerminationCause.MECHANICAL, FailureCauseClass.MECHANICAL),
            (TerminationCause.UNKNOWN, FailureCauseClass.UNKNOWN),
        ],
    )
    def test_the_prefill_is_stored_when_the_class_is_omitted(self, cause, expected) -> None:
        self._service().remove_plant(
            "plant-1", termination_type=TerminationType.DIED, termination_cause=cause, tenant_key="tenant-a"
        )

        stored = self._stored()
        assert (stored.termination_type, stored.termination_cause, stored.failure_cause_class) == (
            TerminationType.DIED,
            cause,
            expected,
        )

    @pytest.mark.parametrize("cause", [TerminationCause.DISEASE, TerminationCause.PEST])
    def test_disease_or_pest_without_a_class_is_refused_before_any_write(self, cause) -> None:
        with pytest.raises(ValidationError, match="needs a failure_cause_class"):
            self._service().remove_plant(
                "plant-1", termination_type=TerminationType.DIED, termination_cause=cause, tenant_key="tenant-a"
            )

        self.plant_repo.update.assert_not_called()
        self.phase_repo.update_phase_history.assert_not_called()

    def test_a_class_that_does_not_fit_the_cause_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="does not fit"):
            self._service().remove_plant(
                "plant-1",
                termination_type=TerminationType.DIED,
                termination_cause=TerminationCause.FROST,
                failure_cause_class=FailureCauseClass.DISEASE_SOIL,
                tenant_key="tenant-a",
            )
        self.plant_repo.update.assert_not_called()

    def test_a_confirmed_soil_pathogen_is_stored_with_its_source(self) -> None:
        result = self._service().remove_plant(
            "plant-1",
            termination_type=TerminationType.DIED,
            termination_cause=TerminationCause.DISEASE,
            failure_cause_class=FailureCauseClass.DISEASE_SOIL,
            failure_pathogen=SoilHazard.VERTICILLIUM,
            failure_pathogen_confirmed=True,
            failure_pathogen_source=PathogenConfirmationSource.ADVISORY_SERVICE,
            tenant_key="tenant-a",
        )

        stored = self._stored()
        assert (
            stored.failure_cause_class,
            stored.failure_pathogen,
            stored.failure_pathogen_confirmed,
            stored.failure_pathogen_source,
        ) == (
            FailureCauseClass.DISEASE_SOIL,
            SoilHazard.VERTICILLIUM,
            True,
            PathogenConfirmationSource.ADVISORY_SERVICE,
        )
        assert result.failure_pathogen is SoilHazard.VERTICILLIUM

    def test_an_unconfirmed_pathogen_is_stored_as_unconfirmed(self) -> None:
        self._service().remove_plant(
            "plant-1",
            termination_type=TerminationType.DIED,
            termination_cause=TerminationCause.PEST,
            failure_cause_class=FailureCauseClass.PEST_SOIL,
            failure_pathogen=SoilHazard.CYST_NEMATODE,
            tenant_key="tenant-a",
        )

        stored = self._stored()
        assert (stored.failure_pathogen, stored.failure_pathogen_confirmed, stored.failure_pathogen_source) == (
            SoilHazard.CYST_NEMATODE,
            False,
            None,
        )

    def test_a_pathogen_on_a_foliar_loss_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="failure_pathogen needs"):
            self._service().remove_plant(
                "plant-1",
                termination_type=TerminationType.DIED,
                termination_cause=TerminationCause.DISEASE,
                failure_cause_class=FailureCauseClass.DISEASE_FOLIAR,
                failure_pathogen=SoilHazard.CLUBROOT,
                tenant_key="tenant-a",
            )
        self.plant_repo.update.assert_not_called()

    def test_a_class_on_a_planned_end_is_refused(self) -> None:
        with pytest.raises(ValidationError, match="only valid for termination_type='died'"):
            self._service().remove_plant(
                "plant-1",
                termination_type=TerminationType.HARVESTED,
                failure_cause_class=FailureCauseClass.ABIOTIC,
                tenant_key="tenant-a",
            )


class TestWithoutAClass(_Base):
    """acceptance-5: a loss without cause and class — the bulk-clear shape — keeps no class."""

    def test_died_without_a_cause_stores_no_class(self) -> None:
        self._service().remove_plant("plant-1", termination_type=TerminationType.DIED, tenant_key="tenant-a")

        stored = self._stored()
        assert (stored.termination_type, stored.termination_cause) == (TerminationType.DIED, None)
        assert (
            stored.failure_cause_class,
            stored.failure_pathogen,
            stored.failure_pathogen_confirmed,
            stored.failure_pathogen_source,
        ) == (None, None, None, None)

    def test_a_legacy_document_loads_without_a_class(self) -> None:
        """A document stored before F-19 carries none of the four fields; it loads and reads as no class."""
        legacy = PlantInstance(
            **{
                "_key": "old-1",
                "tenant_key": "tenant-a",
                "instance_id": "OLD-1",
                "species_key": "sp-lettuce",
                "planted_on": "2025-04-01",
                "removed_on": "2025-06-01",
                "termination_type": "died",
                "termination_cause": "disease",
            }
        )
        assert legacy.termination_cause is TerminationCause.DISEASE
        assert (
            legacy.failure_cause_class,
            legacy.failure_pathogen,
            legacy.failure_pathogen_confirmed,
            legacy.failure_pathogen_source,
        ) == (None, None, None, None)


class TestTerminationOptions(_Base):
    """acceptance-2 and -3 through ``get_termination_options``."""

    def test_a_premature_bolting_phase_suggests_bolting(self) -> None:
        options = self._service().get_termination_options("plant-1", tenant_key="tenant-a")

        assert options.suggested_cause is TerminationCause.BOLTING
        self.phase_repo.get_phase_history.assert_called_once_with("plant-1")

    def test_a_planned_bolting_phase_suggests_nothing(self) -> None:
        self.phase_repo.get_phase_history.return_value = _history(premature=False)

        assert self._service().get_termination_options("plant-1", tenant_key="tenant-a").suggested_cause is None

    def test_unknown_asks_the_wilt_follow_up_on_a_wilt_prone_family_only(self) -> None:
        def unknown_asks() -> bool:
            options = self._service().get_termination_options("plant-1", tenant_key="tenant-a")
            return next(r for r in options.rules if r.termination_cause is TerminationCause.UNKNOWN).asks_wilt_follow_up

        assert unknown_asks() is False  # lettuce, Asteraceae
        self.species_repo.get_by_key.return_value = Species(
            _key="sp-tomato", scientific_name="Solanum lycopersicum", family_key="solanaceae"
        )
        assert unknown_asks() is True

    def test_a_species_without_a_known_family_is_not_wilt_prone(self) -> None:
        self.species_repo.get_by_key.return_value = Species(
            _key="sp-x", scientific_name="Testus plantus", family_key="missing"
        )
        options = self._service().get_termination_options("plant-1", tenant_key="tenant-a")
        assert options.wilt_prone_family is False

    def test_a_plant_of_another_tenant_is_not_found(self) -> None:
        with pytest.raises(NotFoundError):
            self._service().get_termination_options("plant-1", tenant_key="tenant-b")
        self.phase_repo.get_phase_history.assert_not_called()
