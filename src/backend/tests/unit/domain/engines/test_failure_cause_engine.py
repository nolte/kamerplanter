"""The cause class of an unplanned loss (REQ-003 E5 v2.23, REQ-053 §11.3a Nr. 1-2, 5, #2888 F-19).

The pre-fill table of research §5 lives once, in ``app/domain/models/failure_cause.py``; these tests read
it through the engine every caller uses (``find_failure_cause_violations`` for the request schema and the
service, ``FailureCauseEngine`` for the stored record and the dialog options).
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from app.common.enums import (
    FailureCauseClass,
    PathogenConfirmationSource,
    SoilHazard,
    TerminationCause,
    TerminationType,
    WiltFollowUp,
)
from app.domain.engines.crop_rotation_validator import ABIOTIC_TERMINATION_CAUSES, BIOTIC_TERMINATION_CAUSES
from app.domain.engines.failure_cause_engine import FailureCauseEngine, find_failure_cause_violations
from app.domain.models.failure_cause import (
    FAILURE_CAUSE_TABLE,
    WILT_PRONE_FAMILIES,
    FailureCauseRule,
    FailureCauseTable,
)
from app.domain.models.phase import PhaseHistory

_SEED_FAMILIES = Path(__file__).resolve().parents[4] / "app" / "migrations" / "seed_data" / "botanical_families.yaml"


def _violations(cause: TerminationCause | None, cls: FailureCauseClass | None = None, **pathogen) -> list[str]:
    return find_failure_cause_violations(
        termination_type=TerminationType.DIED,
        termination_cause=cause,
        failure_cause_class=cls,
        failure_pathogen=pathogen.get("pathogen"),
        failure_pathogen_confirmed=pathogen.get("confirmed"),
        failure_pathogen_source=pathogen.get("source"),
    )


def _resolve(cause: TerminationCause | None, cls: FailureCauseClass | None = None, **pathogen):
    return FailureCauseEngine().resolve(
        termination_cause=cause,
        failure_cause_class=cls,
        failure_pathogen=pathogen.get("pathogen"),
        failure_pathogen_confirmed=pathogen.get("confirmed"),
        failure_pathogen_source=pathogen.get("source"),
    )


def _phase(name: str, *, premature: bool, exited: bool = False) -> PhaseHistory:
    return PhaseHistory(
        _key="h-1",
        plant_instance_key="plant-1",
        phase_key=f"ph-{name}",
        phase_name=name,
        entered_at=datetime(2026, 6, 1, tzinfo=UTC),
        exited_at=datetime(2026, 6, 20, tzinfo=UTC) if exited else None,
        is_premature=premature,
    )


class TestPrefillTable:
    """acceptance-1: abiotic causes are pre-filled, disease and pest need a foliar/soil choice (research §5)."""

    @pytest.mark.parametrize(
        ("cause", "prefill"),
        [
            (TerminationCause.FROST, FailureCauseClass.ABIOTIC),
            (TerminationCause.HEAT, FailureCauseClass.ABIOTIC),
            (TerminationCause.DROUGHT, FailureCauseClass.ABIOTIC),
            (TerminationCause.WATERLOGGING, FailureCauseClass.ABIOTIC),
            (TerminationCause.NEGLECT, FailureCauseClass.ABIOTIC),
            (TerminationCause.BOLTING, FailureCauseClass.ABIOTIC),
            (TerminationCause.MECHANICAL, FailureCauseClass.MECHANICAL),
            (TerminationCause.UNKNOWN, FailureCauseClass.UNKNOWN),
        ],
    )
    def test_a_cause_without_a_class_takes_its_prefill(self, cause, prefill) -> None:
        assert _violations(cause) == []
        assert _resolve(cause).failure_cause_class is prefill

    @pytest.mark.parametrize(
        ("cause", "choices"),
        [
            (TerminationCause.DISEASE, {FailureCauseClass.DISEASE_FOLIAR, FailureCauseClass.DISEASE_SOIL}),
            (TerminationCause.PEST, {FailureCauseClass.PEST_FOLIAR, FailureCauseClass.PEST_SOIL}),
        ],
    )
    def test_disease_and_pest_must_choose_foliar_or_soil(self, cause, choices) -> None:
        assert FAILURE_CAUSE_TABLE.rule_for(cause).prefill is None
        assert set(FAILURE_CAUSE_TABLE.rule_for(cause).choices) == choices
        assert _violations(cause) == [
            f"termination_cause '{cause}' needs a failure_cause_class: one of "
            + ", ".join(FAILURE_CAUSE_TABLE.rule_for(cause).choices)
        ]
        for cls in choices:
            assert _violations(cause, cls) == []
            assert _resolve(cause, cls).failure_cause_class is cls

    @pytest.mark.parametrize(
        ("cause", "refused"),
        [
            (TerminationCause.DISEASE, FailureCauseClass.PEST_SOIL),
            (TerminationCause.PEST, FailureCauseClass.DISEASE_FOLIAR),
            (TerminationCause.FROST, FailureCauseClass.DISEASE_SOIL),
            (TerminationCause.BOLTING, FailureCauseClass.DISEASE_SOIL),
            (TerminationCause.MECHANICAL, FailureCauseClass.ABIOTIC),
            (TerminationCause.HEAT, FailureCauseClass.PEST_SOIL),
        ],
    )
    def test_a_class_the_cause_does_not_allow_is_refused(self, cause, refused) -> None:
        assert len(_violations(cause, refused)) == 1
        assert f"does not fit termination_cause '{cause}'" in _violations(cause, refused)[0]

    def test_unknown_allows_every_class(self) -> None:
        for cls in FailureCauseClass:
            assert _violations(TerminationCause.UNKNOWN, cls) == []

    def test_a_class_without_a_died_loss_is_refused(self) -> None:
        for termination_type in (None, TerminationType.HARVESTED, TerminationType.SENESCED, TerminationType.CANCELLED):
            assert find_failure_cause_violations(
                termination_type=termination_type,
                termination_cause=None,
                failure_cause_class=FailureCauseClass.ABIOTIC,
                failure_pathogen=None,
                failure_pathogen_confirmed=None,
                failure_pathogen_source=None,
            ) == ["failure_cause_class and the pathogen fields are only valid for termination_type='died'"]

    def test_every_cause_has_exactly_one_row(self) -> None:
        assert [rule.termination_cause for rule in FAILURE_CAUSE_TABLE.rules] == list(TerminationCause)

    def test_a_table_missing_a_cause_is_refused_at_load(self) -> None:
        rows = tuple(r for r in FAILURE_CAUSE_TABLE.rules if r.termination_cause is not TerminationCause.BOLTING)
        with pytest.raises(ValueError, match="causes without a row"):
            FailureCauseTable(rules=rows)

    def test_a_prefill_outside_the_choices_is_refused_at_load(self) -> None:
        with pytest.raises(ValueError, match="not among the choices"):
            FailureCauseRule(
                termination_cause=TerminationCause.FROST,
                prefill=FailureCauseClass.ABIOTIC,
                choices=(FailureCauseClass.MECHANICAL,),
            )

    def test_the_replant_hint_sets_agree_with_the_table(self) -> None:
        """The replant rule (REQ-053 §11.3) and the table name the same abiotic and biotic causes."""
        no_hint = {
            rule.termination_cause.value
            for rule in FAILURE_CAUSE_TABLE.rules
            if rule.prefill in {FailureCauseClass.ABIOTIC, FailureCauseClass.MECHANICAL}
        }
        must_choose = {rule.termination_cause.value for rule in FAILURE_CAUSE_TABLE.rules if rule.prefill is None}
        assert no_hint == ABIOTIC_TERMINATION_CAUSES
        assert must_choose == BIOTIC_TERMINATION_CAUSES


class TestWiltFollowUp:
    """acceptance-2: heat, drought, waterlogging always ask; unknown asks on a wilt-prone family."""

    def test_heat_drought_and_waterlogging_always_ask_and_may_become_disease_soil(self) -> None:
        options = FailureCauseEngine().options(open_phase=None, family_name="Apiaceae")
        asks = {rule.termination_cause for rule in options.rules if rule.asks_wilt_follow_up}
        assert asks == {TerminationCause.HEAT, TerminationCause.DROUGHT, TerminationCause.WATERLOGGING}
        assert options.wilt_prone_family is False
        for cause in asks:
            assert _violations(cause, options.wilt_follow_up_class) == []
            assert _resolve(cause, options.wilt_follow_up_class).failure_cause_class is FailureCauseClass.DISEASE_SOIL

    @pytest.mark.parametrize("family", sorted(WILT_PRONE_FAMILIES))
    def test_unknown_asks_on_a_wilt_prone_family(self, family) -> None:
        options = FailureCauseEngine().options(open_phase=None, family_name=family)
        asks = {rule.termination_cause for rule in options.rules if rule.asks_wilt_follow_up}
        assert TerminationCause.UNKNOWN in asks
        assert options.wilt_prone_family is True

    @pytest.mark.parametrize("family", ["Apiaceae", "Fabaceae", None])
    def test_unknown_does_not_ask_on_another_or_no_family(self, family) -> None:
        options = FailureCauseEngine().options(open_phase=None, family_name=family)
        unknown = next(r for r in options.rules if r.termination_cause is TerminationCause.UNKNOWN)
        assert unknown.asks_wilt_follow_up is False

    def test_frost_neglect_mechanical_bolting_disease_and_pest_never_ask(self) -> None:
        options = FailureCauseEngine().options(open_phase=None, family_name="Solanaceae")
        never = {
            TerminationCause.FROST,
            TerminationCause.NEGLECT,
            TerminationCause.MECHANICAL,
            TerminationCause.BOLTING,
            TerminationCause.DISEASE,
            TerminationCause.PEST,
        }
        assert not [
            r.termination_cause for r in options.rules if r.termination_cause in never and r.asks_wilt_follow_up
        ]

    def test_the_wilt_rows_of_the_table(self) -> None:
        assert {r.termination_cause for r in FAILURE_CAUSE_TABLE.rules if r.wilt_follow_up is WiltFollowUp.ALWAYS} == {
            TerminationCause.HEAT,
            TerminationCause.DROUGHT,
            TerminationCause.WATERLOGGING,
        }
        assert {
            r.termination_cause for r in FAILURE_CAUSE_TABLE.rules if r.wilt_follow_up is WiltFollowUp.WILT_PRONE_FAMILY
        } == {TerminationCause.UNKNOWN}

    def test_every_wilt_prone_family_is_a_seeded_family_name(self) -> None:
        """A typo in the family list would silently never match (``BotanicalFamily.name`` is compared as is)."""
        seeded = {entry["name"] for entry in yaml.safe_load(_SEED_FAMILIES.read_text(encoding="utf-8"))["families"]}
        assert seeded >= WILT_PRONE_FAMILIES


class TestBoltingSuggestion:
    """acceptance-3: ``bolting`` is suggested when the plant went into the bolting phase prematurely (E6)."""

    def test_a_premature_bolting_phase_suggests_bolting(self) -> None:
        engine = FailureCauseEngine()
        assert engine.suggested_cause(_phase("bolting", premature=True)) is TerminationCause.BOLTING
        options = engine.options(open_phase=_phase("bolting", premature=True), family_name=None)
        assert options.suggested_cause is TerminationCause.BOLTING

    @pytest.mark.parametrize(
        "phase",
        [
            _phase("bolting", premature=False),  # planned biennial bolting (D1), no loss cause
            _phase("vegetative", premature=False),
            _phase("flowering", premature=True),  # premature, but not the bolting phase
            _phase("bolting", premature=True, exited=True),  # not the phase it stands in
            None,
        ],
    )
    def test_no_suggestion_otherwise(self, phase) -> None:
        assert FailureCauseEngine().suggested_cause(phase) is None


class TestPathogen:
    """acceptance-4: a soil-borne loss may name a hazard-list pathogen with whether and by whom it was confirmed."""

    @pytest.mark.parametrize("cls", [FailureCauseClass.PEST_SOIL, FailureCauseClass.DISEASE_SOIL])
    def test_a_soil_borne_loss_records_pathogen_confirmation_and_source(self, cls) -> None:
        cause = TerminationCause.PEST if cls is FailureCauseClass.PEST_SOIL else TerminationCause.DISEASE
        fields = {
            "pathogen": SoilHazard.CLUBROOT,
            "confirmed": True,
            "source": PathogenConfirmationSource.LAB_TEST,
        }
        assert _violations(cause, cls, **fields) == []
        record = _resolve(cause, cls, **fields)
        assert (record.failure_pathogen, record.failure_pathogen_confirmed, record.failure_pathogen_source) == (
            SoilHazard.CLUBROOT,
            True,
            PathogenConfirmationSource.LAB_TEST,
        )

    def test_a_named_pathogen_is_unconfirmed_unless_stated(self) -> None:
        record = _resolve(TerminationCause.DISEASE, FailureCauseClass.DISEASE_SOIL, pathogen=SoilHazard.VERTICILLIUM)
        assert (record.failure_pathogen_confirmed, record.failure_pathogen_source) == (False, None)

    def test_the_wilt_follow_up_class_may_name_a_pathogen(self) -> None:
        assert (
            _violations(TerminationCause.HEAT, FailureCauseClass.DISEASE_SOIL, pathogen=SoilHazard.VERTICILLIUM) == []
        )

    @pytest.mark.parametrize(
        ("cause", "cls"),
        [
            (TerminationCause.DISEASE, FailureCauseClass.DISEASE_FOLIAR),
            (TerminationCause.PEST, FailureCauseClass.PEST_FOLIAR),
            (TerminationCause.HEAT, None),  # pre-filled abiotic
            (TerminationCause.UNKNOWN, FailureCauseClass.UNKNOWN),
        ],
    )
    def test_a_pathogen_outside_a_soil_borne_class_is_refused(self, cause, cls) -> None:
        assert _violations(cause, cls, pathogen=SoilHazard.CLUBROOT) == [
            "failure_pathogen needs failure_cause_class 'pest_soil' or 'disease_soil'"
        ]

    def test_confirmation_needs_a_pathogen_and_a_source_needs_a_confirmation(self) -> None:
        soil = (TerminationCause.DISEASE, FailureCauseClass.DISEASE_SOIL)
        assert _violations(*soil, confirmed=False) == ["failure_pathogen_confirmed needs a failure_pathogen"]
        assert _violations(*soil, pathogen=SoilHazard.CLUBROOT, source=PathogenConfirmationSource.LAB_TEST) == [
            "failure_pathogen_source needs failure_pathogen_confirmed=true"
        ]
        assert _violations(*soil, pathogen=SoilHazard.CLUBROOT, confirmed=True) == [
            "a confirmed pathogen needs failure_pathogen_source (who confirmed it)"
        ]

    def test_the_dialog_options_offer_the_hazard_list_and_the_soil_borne_classes(self) -> None:
        options = FailureCauseEngine().options(open_phase=None, family_name=None)
        assert list(options.pathogens) == list(SoilHazard)
        assert set(options.pathogen_classes) == {FailureCauseClass.PEST_SOIL, FailureCauseClass.DISEASE_SOIL}
        assert list(options.confirmation_sources) == list(PathogenConfirmationSource)


class TestNoClassStaysNoClass:
    """acceptance-5: a loss with no cause and no class (bulk clear, legacy) records no class."""

    def test_no_cause_and_no_class_records_nothing(self) -> None:
        assert _violations(None) == []
        record = _resolve(None)
        assert (
            record.failure_cause_class,
            record.failure_pathogen,
            record.failure_pathogen_confirmed,
            record.failure_pathogen_source,
        ) == (None, None, None, None)
