"""The rules of a bed's soil hazards (REQ-054 §5.2, REQ-053 §11.3a Nr. 5, #2888 F-20).

Where a soil hazard may stand (acceptance-2: no vessel), what a recorded loss proposes (acceptance-3: an offer only for
a confirmed, listed pathogen; acceptance-4: the clean-system hint at hydroponics), how entries merge, and what the
knowledge table says about an entry (acceptance-1: hosts with their evidence status, read from the shipped table).

Every loss below is one the F-19 rule accepts (:func:`_loss` checks it with ``find_failure_cause_violations``), so no
test reasons about a plant the API could never have stored.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.common.enums import (
    EvidenceStatus,
    FailureCauseClass,
    HostLevel,
    IrrigationSystem,
    PathogenConfirmationSource,
    SoilHazard,
    SoilHazardFollowUpKind,
    SoilHazardRefusal,
    TerminationCause,
    TerminationType,
)
from app.data_access.knowledge.soil_hazard_knowledge_source import YamlSoilHazardKnowledgeSource
from app.domain.engines.bed_soil_hazard_engine import (
    LossNotPromotableError,
    entry_from_loss,
    follow_up_for_loss,
    merged_entries,
    resolve_entries,
    soil_hazard_refusal,
    soil_hazard_refusal_for_type,
)
from app.domain.engines.crop_rotation_validator import ROTATION_OFF_LOCATION_TYPES
from app.domain.engines.failure_cause_engine import find_failure_cause_violations
from app.domain.models.bed_soil_hazard import CONTAINER_LOCATION_TYPES, LOSS_SOIL_HAZARDS, BedSoilHazard
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.site import Location

LOSS_DAY = date(2026, 7, 1)


def _bed(key: str = "bed", *, type_key: str = "bed", irrigation: IrrigationSystem = IrrigationSystem.MANUAL, **kw):
    return Location(
        _key=key,
        name="Beet",
        site_key="site",
        area_m2=2.0,
        location_type_key=type_key,
        irrigation_system=irrigation,
        **kw,
    )


def _loss(
    *,
    cls: FailureCauseClass = FailureCauseClass.DISEASE_SOIL,
    cause: TerminationCause = TerminationCause.DISEASE,
    pathogen: SoilHazard | None = SoilHazard.CLUBROOT,
    confirmed: bool | None = True,
    source: PathogenConfirmationSource | None = PathogenConfirmationSource.LAB_TEST,
    location_key: str | None = "bed",
    legacy: bool = False,
) -> PlantInstance:
    """A died plant as ``POST /plant-instances/{key}/remove`` stores it - refused here if F-19 would refuse it.

    ``legacy``: a loss stored before #2888 F-20 (juglone was accepted then); the current rule is not applied.
    """
    if pathogen is not None and confirmed is None:
        confirmed = False
    violations = (
        []
        if legacy
        else find_failure_cause_violations(
            termination_type=TerminationType.DIED,
            termination_cause=cause,
            failure_cause_class=cls,
            failure_pathogen=pathogen,
            failure_pathogen_confirmed=confirmed,
            failure_pathogen_source=source,
        )
    )
    assert violations == [], f"the fixture names a loss F-19 refuses: {violations}"
    return PlantInstance(
        _key="pi_1",
        tenant_key="ten",
        instance_id="KOHL-1",
        species_key="sp_kohl",
        site_key="site",
        location_key=location_key,
        planted_on=date(2026, 4, 1),
        removed_on=LOSS_DAY,
        termination_type=TerminationType.DIED,
        termination_cause=cause,
        failure_cause_class=cls,
        failure_pathogen=pathogen,
        failure_pathogen_confirmed=confirmed,
        failure_pathogen_source=source,
    )


class TestWhereASoilHazardMayStand:
    @pytest.mark.parametrize("type_key", ["planter", "tent", "shelf"])
    def test_a_vessel_carries_none(self, type_key: str) -> None:
        # ``planter`` is a bed type and still refused: the vessel rule comes first.
        assert soil_hazard_refusal(_bed(type_key=type_key), is_bed=True) is SoilHazardRefusal.CONTAINER

    def test_a_location_that_is_no_bed_carries_none(self) -> None:
        assert soil_hazard_refusal(_bed(type_key="greenhouse"), is_bed=False) is SoilHazardRefusal.NOT_A_BED

    @pytest.mark.parametrize("system", [IrrigationSystem.HYDRO, IrrigationSystem.NFT, IrrigationSystem.EBB_FLOW])
    def test_a_hydroponic_bed_has_no_soil(self, system: IrrigationSystem) -> None:
        assert soil_hazard_refusal(_bed(irrigation=system), is_bed=True) is SoilHazardRefusal.HYDROPONIC

    @pytest.mark.parametrize("system", [IrrigationSystem.MANUAL, IrrigationSystem.DRIP, IrrigationSystem.MIST])
    def test_a_bed_with_soil_may_carry_one(self, system: IrrigationSystem) -> None:
        assert soil_hazard_refusal(_bed(type_key="raised_bed", irrigation=system), is_bed=True) is None

    def test_the_type_rule_alone_is_what_the_import_applies(self) -> None:
        assert soil_hazard_refusal_for_type("tent", is_bed=False) is SoilHazardRefusal.CONTAINER
        assert soil_hazard_refusal_for_type("", is_bed=False) is SoilHazardRefusal.NOT_A_BED
        assert soil_hazard_refusal_for_type("bed", is_bed=True) is None

    def test_the_vessels_are_the_types_the_rotation_check_skips(self) -> None:
        assert ROTATION_OFF_LOCATION_TYPES == CONTAINER_LOCATION_TYPES == {"planter", "tent", "shelf"}


class TestALossBecomesAnEntryOnlyWhenConfirmed:
    def test_a_confirmed_listed_pathogen_is_the_entry_dated_on_the_loss(self) -> None:
        assert entry_from_loss(_loss()) == BedSoilHazard(
            hazard=SoilHazard.CLUBROOT, confirmed_at=LOSS_DAY, source=PathogenConfirmationSource.LAB_TEST
        )

    def test_a_soil_pest_with_a_confirmed_nematode_is_an_entry_too(self) -> None:
        plant = _loss(cls=FailureCauseClass.PEST_SOIL, cause=TerminationCause.PEST, pathogen=SoilHazard.CYST_NEMATODE)
        assert entry_from_loss(plant).hazard is SoilHazard.CYST_NEMATODE

    def test_an_unconfirmed_suspicion_never_is(self) -> None:
        with pytest.raises(LossNotPromotableError, match="not confirmed"):
            entry_from_loss(_loss(confirmed=False, source=None))

    def test_a_soil_borne_loss_without_a_pathogen_never_is(self) -> None:
        with pytest.raises(LossNotPromotableError, match="names no pathogen"):
            entry_from_loss(_loss(pathogen=None, confirmed=None, source=None))

    def test_juglone_is_entered_by_hand_not_taken_over_from_a_loss(self) -> None:
        # F-19 lets a loss name it (the list is SoilHazard); the walnut is no pathogen of the plant (research §2).
        with pytest.raises(LossNotPromotableError, match="by hand"):
            entry_from_loss(_loss(pathogen=SoilHazard.JUGLONE, legacy=True))
        assert set(SoilHazard) - LOSS_SOIL_HAZARDS == {SoilHazard.JUGLONE}

    def test_a_foliar_loss_never_is(self) -> None:
        plant = _loss(cls=FailureCauseClass.DISEASE_FOLIAR, pathogen=None, confirmed=None, source=None)
        with pytest.raises(LossNotPromotableError, match="no soil-borne loss"):
            entry_from_loss(plant)

    def test_a_harvested_plant_never_is(self) -> None:
        # As stored: a harvest carries no cause and no class (F-19 refuses them outside ``died``).
        harvested = PlantInstance(
            _key="pi_2",
            tenant_key="ten",
            instance_id="KOHL-2",
            species_key="sp_kohl",
            location_key="bed",
            planted_on=date(2026, 4, 1),
            removed_on=LOSS_DAY,
            termination_type=TerminationType.HARVESTED,
        )
        with pytest.raises(LossNotPromotableError, match="no soil-borne loss"):
            entry_from_loss(harvested)


class TestEntriesMerge:
    _OLD = BedSoilHazard(
        hazard=SoilHazard.CLUBROOT, confirmed_at=date(2024, 6, 1), source=PathogenConfirmationSource.CLEAR_SYMPTOMS
    )

    def test_a_new_hazard_is_added(self) -> None:
        other = BedSoilHazard(
            hazard=SoilHazard.WHITE_ROT, confirmed_at=LOSS_DAY, source=PathogenConfirmationSource.LAB_TEST
        )
        assert merged_entries([self._OLD], other) == [self._OLD, other]

    def test_a_later_confirmation_replaces_the_entry(self) -> None:
        newer = self._OLD.model_copy(update={"confirmed_at": LOSS_DAY, "source": PathogenConfirmationSource.LAB_TEST})
        assert merged_entries([self._OLD], newer) == [newer]

    def test_an_earlier_confirmation_never_shortens_it(self) -> None:
        earlier = self._OLD.model_copy(update={"confirmed_at": date(2020, 1, 1)})
        assert merged_entries([self._OLD], earlier) == [self._OLD]


class TestWhatALossProposes:
    def test_a_confirmed_loss_in_a_bed_offers_the_entry(self) -> None:
        follow_up = follow_up_for_loss(_loss(), _bed(), is_bed=True)

        assert follow_up is not None
        assert follow_up.kind is SoilHazardFollowUpKind.OFFER
        assert (follow_up.location_key, follow_up.hazard, follow_up.confirmed_at, follow_up.source) == (
            "bed",
            SoilHazard.CLUBROOT,
            LOSS_DAY,
            PathogenConfirmationSource.LAB_TEST,
        )

    def test_an_unconfirmed_loss_proposes_nothing(self) -> None:
        assert follow_up_for_loss(_loss(confirmed=False, source=None), _bed(), is_bed=True) is None

    def test_a_juglone_loss_proposes_nothing(self) -> None:
        assert follow_up_for_loss(_loss(pathogen=SoilHazard.JUGLONE, legacy=True), _bed(), is_bed=True) is None

    @pytest.mark.parametrize("type_key", ["planter", "shelf"])
    def test_a_vessel_proposes_nothing(self, type_key: str) -> None:
        assert follow_up_for_loss(_loss(), _bed(type_key=type_key), is_bed=type_key == "planter") is None

    @pytest.mark.parametrize("system", [IrrigationSystem.HYDRO, IrrigationSystem.NFT, IrrigationSystem.EBB_FLOW])
    def test_a_soil_borne_loss_at_hydroponics_is_the_clean_system_hint(self, system: IrrigationSystem) -> None:
        follow_up = follow_up_for_loss(_loss(), _bed(irrigation=system), is_bed=True)

        assert follow_up is not None
        assert follow_up.kind is SoilHazardFollowUpKind.CLEAN_SYSTEM
        assert (follow_up.hazard, follow_up.confirmed_at, follow_up.source) == (None, None, None)

    def test_the_hint_does_not_wait_for_a_confirmation_and_reaches_a_hydroponic_tent(self) -> None:
        tent = _bed("tent_1", type_key="tent", irrigation=IrrigationSystem.NFT)
        plant = _loss(pathogen=None, confirmed=None, source=None, location_key="tent_1")

        follow_up = follow_up_for_loss(plant, tent, is_bed=False)

        assert follow_up is not None and follow_up.kind is SoilHazardFollowUpKind.CLEAN_SYSTEM

    def test_an_abiotic_loss_at_hydroponics_proposes_nothing(self) -> None:
        plant = _loss(
            cls=FailureCauseClass.ABIOTIC, cause=TerminationCause.FROST, pathogen=None, confirmed=None, source=None
        )
        assert follow_up_for_loss(plant, _bed(irrigation=IrrigationSystem.HYDRO), is_bed=True) is None

    def test_a_bed_that_holds_the_hazard_as_late_is_not_offered_it_again(self) -> None:
        held = BedSoilHazard(
            hazard=SoilHazard.CLUBROOT, confirmed_at=LOSS_DAY, source=PathogenConfirmationSource.ADVISORY_SERVICE
        )
        assert follow_up_for_loss(_loss(), _bed(soil_hazards=[held]), is_bed=True) is None

    def test_a_bed_that_holds_an_older_confirmation_is_offered_the_newer_one(self) -> None:
        held = BedSoilHazard(
            hazard=SoilHazard.CLUBROOT, confirmed_at=date(2023, 5, 1), source=PathogenConfirmationSource.LAB_TEST
        )
        follow_up = follow_up_for_loss(_loss(), _bed(soil_hazards=[held]), is_bed=True)
        assert follow_up is not None and follow_up.confirmed_at == LOSS_DAY

    def test_a_plant_without_a_location_proposes_nothing(self) -> None:
        assert follow_up_for_loss(_loss(location_key=None), None, is_bed=False) is None


class TestTheTableResolvesTheHosts:
    def test_an_entry_shows_its_pathogen_and_hosts_with_their_evidence_status(self) -> None:
        table = YamlSoilHazardKnowledgeSource().get_table()
        entry = BedSoilHazard(
            hazard=SoilHazard.CLUBROOT, confirmed_at=LOSS_DAY, source=PathogenConfirmationSource.LAB_TEST
        )

        (resolved,) = resolve_entries([entry], table)

        assert resolved.pathogens == ("Plasmodiophora brassicae",)
        assert resolved.soft is False
        assert [(h.level, h.name, h.evidence_status) for h in resolved.hosts] == [
            (HostLevel.FAMILY, "Brassicaceae", EvidenceStatus.EVIDENCED)
        ]

    def test_a_host_below_three_sources_is_shown_with_its_status_not_left_out(self) -> None:
        # P4 is open: whether a 2/3 host warns is undecided, so the read model shows it as data.
        table = YamlSoilHazardKnowledgeSource().get_table()
        entry = BedSoilHazard(
            hazard=SoilHazard.SCLEROTINIA, confirmed_at=LOSS_DAY, source=PathogenConfirmationSource.LAB_TEST
        )

        (resolved,) = resolve_entries([entry], table)

        row = next(row for row in table.hazards if row.hazard is SoilHazard.SCLEROTINIA)
        assert len(resolved.hosts) == len(row.hosts) > 0
        assert {host.evidence_status for host in resolved.hosts} == {host.evidence.status for host in row.hosts}
        assert resolved.soft is True

    def test_entries_come_newest_first(self) -> None:
        table = YamlSoilHazardKnowledgeSource().get_table()
        old = BedSoilHazard(
            hazard=SoilHazard.CLUBROOT, confirmed_at=date(2023, 1, 1), source=PathogenConfirmationSource.LAB_TEST
        )
        new = BedSoilHazard(
            hazard=SoilHazard.WHITE_ROT, confirmed_at=LOSS_DAY, source=PathogenConfirmationSource.LAB_TEST
        )

        assert [r.hazard for r in resolve_entries([old, new], table)] == [SoilHazard.WHITE_ROT, SoilHazard.CLUBROOT]


class TestTheStoredField:
    def test_a_legacy_location_loads_without_soil_hazards(self) -> None:
        legacy = Location.model_validate({"_key": "old", "name": "Altbeet", "site_key": "s", "area_m2": 1.0})
        assert legacy.soil_hazards == []

    def test_a_hazard_listed_twice_is_refused(self) -> None:
        entry = {"hazard": "clubroot", "confirmed_at": "2026-07-01", "source": "lab_test"}
        with pytest.raises(ValueError, match="twice"):
            _bed(soil_hazards=[entry, entry])

    def test_an_unknown_hazard_key_is_refused(self) -> None:
        with pytest.raises(ValueError, match="hazard"):
            _bed(soil_hazards=[{"hazard": "fusarium", "confirmed_at": "2026-07-01", "source": "lab_test"}])


class TestTheConfirmationDate:
    """Review D5: one rule on the entry for every writer - not after today (UTC), not before 1900."""

    @pytest.mark.parametrize("day", ["1899-12-31", "2999-01-01"])
    def test_an_implausible_day_is_refused(self, day: str) -> None:
        with pytest.raises(ValueError, match="confirmed_at"):
            BedSoilHazard.model_validate({"hazard": "clubroot", "confirmed_at": day, "source": "lab_test"})

    def test_1900_and_today_are_accepted(self) -> None:
        from app.common.datetimes import today_utc

        for day in (date(1900, 1, 1), today_utc()):
            assert (
                BedSoilHazard(
                    hazard=SoilHazard.CLUBROOT, confirmed_at=day, source=PathogenConfirmationSource.LAB_TEST
                ).confirmed_at
                == day
            )

    def test_a_container_group_is_refused_like_a_vessel_but_keeps_its_rotation(self) -> None:
        assert soil_hazard_refusal_for_type("container", is_bed=False) is SoilHazardRefusal.CONTAINER
        assert "container" not in ROTATION_OFF_LOCATION_TYPES
