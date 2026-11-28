"""The rules of a bed's soil hazards (REQ-054 §5.2, REQ-053 §11.3a Nr. 5, #2888 F-20).

Where a soil hazard may stand (acceptance-2: no vessel; O3: juglone at an area too), what a recorded loss proposes
(acceptance-3: an offer only for a confirmed, listed pathogen; acceptance-4: the clean-system hint at hydroponics, O5:
also inherited from a parent), what the soil under a location carries (its own and its parent chain's entries, REQ-053
§11.3a Nr. 5 v1.60), how entries merge, and what the knowledge table says about an entry (acceptance-1: hosts with
their evidence status, read from the shipped table).

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
    SoilHazardScope,
    TerminationCause,
    TerminationType,
)
from app.data_access.knowledge.soil_hazard_knowledge_source import YamlSoilHazardKnowledgeSource
from app.domain.engines.bed_soil_hazard_engine import (
    LossNotPromotableError,
    effective_irrigation_system,
    effective_soil_hazards,
    entry_from_loss,
    follow_up_for_loss,
    is_hydroponic,
    merged_entries,
    resolve_entries,
    soil_hazard_refusal,
    soil_hazard_refusal_for_type,
    soil_hazard_scope,
)
from app.domain.engines.crop_rotation_validator import ROTATION_OFF_LOCATION_TYPES
from app.domain.engines.failure_cause_engine import find_failure_cause_violations
from app.domain.models.bed_soil_hazard import (
    CONTAINER_LOCATION_TYPES,
    LOSS_SOIL_HAZARDS,
    BedSoilHazard,
    substrate_replaced_on_change,
)
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


def _refusal(
    location: Location,
    *,
    is_bed: bool,
    hazard: SoilHazard | None = SoilHazard.CLUBROOT,
    ancestors: tuple[Location, ...] = (),
) -> SoilHazardRefusal | None:
    return soil_hazard_refusal(location, is_bed=is_bed, hazard=hazard, ancestors=ancestors)


def _area(key: str, *, type_key: str = "garden", parent: str | None = None, **kw) -> Location:
    return _bed(key, type_key=type_key, parent_location_key=parent, **kw)


JUGLONE_2019 = BedSoilHazard(
    hazard=SoilHazard.JUGLONE, confirmed_at=date(2019, 3, 1), source=PathogenConfirmationSource.CLEAR_SYMPTOMS
)
CLUBROOT_2024 = BedSoilHazard(
    hazard=SoilHazard.CLUBROOT, confirmed_at=date(2024, 6, 1), source=PathogenConfirmationSource.LAB_TEST
)


class TestWhereASoilHazardMayStand:
    @pytest.mark.parametrize("type_key", ["planter", "tent", "shelf"])
    def test_a_vessel_carries_none(self, type_key: str) -> None:
        # ``planter`` is a bed type and still refused: the vessel rule comes first.
        assert _refusal(_bed(type_key=type_key), is_bed=True) is SoilHazardRefusal.CONTAINER

    @pytest.mark.parametrize("type_key", ["planter", "tent", "shelf", "container"])
    def test_a_vessel_carries_no_juglone_either(self, type_key: str) -> None:
        assert _refusal(_bed(type_key=type_key), is_bed=False, hazard=SoilHazard.JUGLONE) is SoilHazardRefusal.CONTAINER

    def test_a_location_that_is_no_bed_carries_no_pathogen(self) -> None:
        assert _refusal(_bed(type_key="greenhouse"), is_bed=False) is SoilHazardRefusal.NOT_A_BED

    @pytest.mark.parametrize("type_key", ["garden", "zone", "greenhouse", "orchard_meadow", ""])
    def test_an_area_that_is_no_bed_carries_juglone(self, type_key: str) -> None:
        """O3 (2026-11-27): juglone at every location that is no vessel - also a tenant's own type, also no type."""
        assert _refusal(_bed(type_key=type_key), is_bed=False, hazard=SoilHazard.JUGLONE) is None

    def test_a_loss_whose_pathogen_is_not_known_yet_is_held_to_the_bed_rule(self) -> None:
        assert _refusal(_bed(type_key="garden"), is_bed=False, hazard=None) is SoilHazardRefusal.NOT_A_BED
        assert _refusal(_bed(), is_bed=True, hazard=None) is None

    @pytest.mark.parametrize("system", [IrrigationSystem.HYDRO, IrrigationSystem.NFT, IrrigationSystem.EBB_FLOW])
    def test_a_hydroponic_bed_has_no_soil(self, system: IrrigationSystem) -> None:
        assert _refusal(_bed(irrigation=system), is_bed=True) is SoilHazardRefusal.HYDROPONIC

    def test_juglone_at_a_hydroponic_area_is_refused_as_hydroponic(self) -> None:
        area = _bed(type_key="greenhouse", irrigation=IrrigationSystem.HYDRO)
        assert _refusal(area, is_bed=False, hazard=SoilHazard.JUGLONE) is SoilHazardRefusal.HYDROPONIC

    @pytest.mark.parametrize("system", [IrrigationSystem.MANUAL, IrrigationSystem.DRIP, IrrigationSystem.MIST])
    def test_a_bed_with_soil_may_carry_one(self, system: IrrigationSystem) -> None:
        assert _refusal(_bed(type_key="raised_bed", irrigation=system), is_bed=True) is None

    def test_the_type_rule_alone_is_what_the_import_applies(self) -> None:
        clubroot, juglone = SoilHazard.CLUBROOT, SoilHazard.JUGLONE
        assert soil_hazard_refusal_for_type("tent", is_bed=False, hazard=juglone) is SoilHazardRefusal.CONTAINER
        assert soil_hazard_refusal_for_type("", is_bed=False, hazard=clubroot) is SoilHazardRefusal.NOT_A_BED
        assert soil_hazard_refusal_for_type("garden", is_bed=False, hazard=juglone) is None
        assert soil_hazard_refusal_for_type("bed", is_bed=True, hazard=clubroot) is None

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
        follow_up = follow_up_for_loss(_loss(), _bed(), is_bed=True, ancestors=())

        assert follow_up is not None
        assert follow_up.kind is SoilHazardFollowUpKind.OFFER
        assert (follow_up.location_key, follow_up.hazard, follow_up.confirmed_at, follow_up.source) == (
            "bed",
            SoilHazard.CLUBROOT,
            LOSS_DAY,
            PathogenConfirmationSource.LAB_TEST,
        )

    def test_an_unconfirmed_loss_proposes_nothing(self) -> None:
        assert follow_up_for_loss(_loss(confirmed=False, source=None), _bed(), is_bed=True, ancestors=()) is None

    def test_a_juglone_loss_proposes_nothing(self) -> None:
        assert (
            follow_up_for_loss(_loss(pathogen=SoilHazard.JUGLONE, legacy=True), _bed(), is_bed=True, ancestors=())
            is None
        )

    @pytest.mark.parametrize("type_key", ["planter", "shelf"])
    def test_a_vessel_proposes_nothing(self, type_key: str) -> None:
        assert follow_up_for_loss(_loss(), _bed(type_key=type_key), is_bed=type_key == "planter", ancestors=()) is None

    @pytest.mark.parametrize("system", [IrrigationSystem.HYDRO, IrrigationSystem.NFT, IrrigationSystem.EBB_FLOW])
    def test_a_soil_borne_loss_at_hydroponics_is_the_clean_system_hint(self, system: IrrigationSystem) -> None:
        follow_up = follow_up_for_loss(_loss(), _bed(irrigation=system), is_bed=True, ancestors=())

        assert follow_up is not None
        assert follow_up.kind is SoilHazardFollowUpKind.CLEAN_SYSTEM
        assert (follow_up.hazard, follow_up.confirmed_at, follow_up.source) == (None, None, None)

    def test_the_hint_does_not_wait_for_a_confirmation_and_reaches_a_hydroponic_tent(self) -> None:
        tent = _bed("tent_1", type_key="tent", irrigation=IrrigationSystem.NFT)
        plant = _loss(pathogen=None, confirmed=None, source=None, location_key="tent_1")

        follow_up = follow_up_for_loss(plant, tent, is_bed=False, ancestors=())

        assert follow_up is not None and follow_up.kind is SoilHazardFollowUpKind.CLEAN_SYSTEM

    def test_an_abiotic_loss_at_hydroponics_proposes_nothing(self) -> None:
        plant = _loss(
            cls=FailureCauseClass.ABIOTIC, cause=TerminationCause.FROST, pathogen=None, confirmed=None, source=None
        )
        assert follow_up_for_loss(plant, _bed(irrigation=IrrigationSystem.HYDRO), is_bed=True, ancestors=()) is None

    def test_a_bed_that_holds_the_hazard_as_late_is_not_offered_it_again(self) -> None:
        held = BedSoilHazard(
            hazard=SoilHazard.CLUBROOT, confirmed_at=LOSS_DAY, source=PathogenConfirmationSource.ADVISORY_SERVICE
        )
        assert follow_up_for_loss(_loss(), _bed(soil_hazards=[held]), is_bed=True, ancestors=()) is None

    def test_a_bed_that_holds_an_older_confirmation_is_offered_the_newer_one(self) -> None:
        held = BedSoilHazard(
            hazard=SoilHazard.CLUBROOT, confirmed_at=date(2023, 5, 1), source=PathogenConfirmationSource.LAB_TEST
        )
        follow_up = follow_up_for_loss(_loss(), _bed(soil_hazards=[held]), is_bed=True, ancestors=())
        assert follow_up is not None and follow_up.confirmed_at == LOSS_DAY

    def test_a_plant_without_a_location_proposes_nothing(self) -> None:
        assert follow_up_for_loss(_loss(location_key=None), None, is_bed=False, ancestors=()) is None


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
        assert (
            soil_hazard_refusal_for_type("container", is_bed=False, hazard=SoilHazard.CLUBROOT)
            is SoilHazardRefusal.CONTAINER
        )
        assert "container" not in ROTATION_OFF_LOCATION_TYPES


class TestTheIrrigationSystemComesFromTheParents:
    """O5 (2026-11-27): ``manual`` is "nothing entered" - the nearest parent with another value decides."""

    def test_a_shelf_left_at_manual_under_a_hydroponic_room_is_hydroponic(self) -> None:
        room = _area("room", type_key="room", irrigation=IrrigationSystem.NFT)
        shelf = _bed("shelf", type_key="shelf", parent_location_key="room")

        assert effective_irrigation_system(shelf, [room]) is IrrigationSystem.NFT
        assert is_hydroponic(shelf, [room]) is True

    def test_the_nearest_parent_with_a_value_decides(self) -> None:
        tent = _bed("tent", type_key="tent", irrigation=IrrigationSystem.DRIP)
        room = _area("room", type_key="room", irrigation=IrrigationSystem.HYDRO)
        shelf = _bed("shelf", type_key="shelf")

        assert effective_irrigation_system(shelf, [tent, room]) is IrrigationSystem.DRIP
        assert is_hydroponic(shelf, [tent, room]) is False

    def test_an_own_value_other_than_manual_wins_over_the_parents(self) -> None:
        room = _area("room", type_key="room", irrigation=IrrigationSystem.HYDRO)
        bed = _bed("bed", irrigation=IrrigationSystem.MIST)

        assert is_hydroponic(bed, [room]) is False

    def test_without_a_value_anywhere_it_stays_manual(self) -> None:
        assert effective_irrigation_system(_bed(), [_area("garden")]) is IrrigationSystem.MANUAL

    def test_an_inherited_hydroponic_system_refuses_the_entry_at_a_location_without_a_bed_type(self) -> None:
        room = _area("room", type_key="room", irrigation=IrrigationSystem.EBB_FLOW)
        area = _area("zone", type_key="zone", parent="room")

        refusal = _refusal(area, is_bed=False, hazard=SoilHazard.JUGLONE, ancestors=(room,))

        assert refusal is SoilHazardRefusal.HYDROPONIC

    def test_a_soil_bed_under_a_hydroponic_room_takes_an_entry(self) -> None:
        """Review S1 (REQ-053 v1.61): a bed type left at ``manual`` stays a soil bed; only its own value counts."""
        room = _area("room", type_key="room", irrigation=IrrigationSystem.EBB_FLOW)

        assert _refusal(_bed(), is_bed=True, ancestors=(room,)) is None
        assert (
            _refusal(_bed(irrigation=IrrigationSystem.NFT), is_bed=True, ancestors=()) is SoilHazardRefusal.HYDROPONIC
        )

    def test_an_inherited_hydroponic_system_is_the_clean_system_hint_after_a_loss(self) -> None:
        room = _area("room", type_key="room", irrigation=IrrigationSystem.HYDRO)
        shelf = _bed("shelf_1", type_key="shelf")
        plant = _loss(pathogen=None, confirmed=None, source=None, location_key="shelf_1")

        follow_up = follow_up_for_loss(plant, shelf, is_bed=False, ancestors=[room])

        assert follow_up is not None and follow_up.kind is SoilHazardFollowUpKind.CLEAN_SYSTEM
        assert follow_up_for_loss(plant, shelf, is_bed=False, ancestors=[]) is None

    def test_a_soil_bed_under_a_hydroponic_room_is_offered_the_take_over(self) -> None:
        room = _area("room", type_key="room", irrigation=IrrigationSystem.HYDRO)

        follow_up = follow_up_for_loss(_loss(), _bed(), is_bed=True, ancestors=[room])

        assert follow_up is not None and follow_up.kind is SoilHazardFollowUpKind.OFFER


def _hazards(located) -> list[BedSoilHazard]:
    return [item.entry for item in located]


class TestWhatTheSoilUnderALocationCarries:
    """REQ-053 §11.3a Nr. 5 v1.60/v1.61: a location's soil hazards reach the locations below it, with their origin."""

    def test_a_bed_carries_the_juglone_of_the_garden_it_lies_in(self) -> None:
        garden = _area("garden", soil_hazards=[JUGLONE_2019])
        bed = _bed(parent_location_key="garden", soil_hazards=[CLUBROOT_2024])

        located = effective_soil_hazards(bed, [garden])

        assert _hazards(located) == [CLUBROOT_2024, JUGLONE_2019]
        assert [item.origin.key if item.origin else None for item in located] == [None, "garden"]

    def test_the_whole_parent_chain_counts(self) -> None:
        garden = _area("garden", soil_hazards=[JUGLONE_2019])
        zone = _area("zone", type_key="zone", parent="garden")
        bed = _bed(parent_location_key="zone")

        (item,) = effective_soil_hazards(bed, [zone, garden])

        assert (item.entry, item.origin) == (JUGLONE_2019, garden)

    def test_a_hazard_held_at_two_levels_counts_once_with_the_later_confirmation(self) -> None:
        later = JUGLONE_2019.model_copy(update={"confirmed_at": date(2025, 1, 1)})
        garden = _area("garden", soil_hazards=[later])
        bed = _bed(parent_location_key="garden", soil_hazards=[JUGLONE_2019])

        (item,) = effective_soil_hazards(bed, [garden])
        assert (item.entry, item.origin) == (later, garden)
        (own,) = effective_soil_hazards(_bed(soil_hazards=[later]), [_area("g", soil_hazards=[JUGLONE_2019])])
        assert (own.entry, own.origin) == (later, None)

    @pytest.mark.parametrize("type_key", ["planter", "tent", "shelf", "container"])
    def test_a_vessel_carries_none_of_its_parents(self, type_key: str) -> None:
        garden = _area("garden", soil_hazards=[JUGLONE_2019])
        assert effective_soil_hazards(_bed(type_key=type_key), [garden]) == []

    def test_a_vessel_in_the_chain_ends_it(self) -> None:
        garden = _area("garden", soil_hazards=[JUGLONE_2019])
        tent = _bed("tent", type_key="tent", parent_location_key="garden")
        bed = _bed(parent_location_key="tent")

        assert effective_soil_hazards(bed, [tent, garden]) == []

    def test_under_inherited_hydroponics_the_own_entries_stay_and_the_inherited_go(self) -> None:
        """Review S1: a greenhouse on ``hydro`` for its NFT channel keeps the clubroot of its soil bed."""
        greenhouse = _area("greenhouse", soil_hazards=[JUGLONE_2019], irrigation=IrrigationSystem.HYDRO)
        bed = _bed(parent_location_key="greenhouse", soil_hazards=[CLUBROOT_2024])

        assert _hazards(effective_soil_hazards(bed, [greenhouse])) == [CLUBROOT_2024]

    def test_an_own_hydroponic_value_carries_none(self) -> None:
        bed = _bed(irrigation=IrrigationSystem.NFT, soil_hazards=[CLUBROOT_2024])

        assert effective_soil_hazards(bed, [_area("garden", soil_hazards=[JUGLONE_2019])]) == []

    def test_without_parents_it_is_the_own_list(self) -> None:
        assert _hazards(effective_soil_hazards(_bed(soil_hazards=[CLUBROOT_2024]), [])) == [CLUBROOT_2024]


class TestWhatALocationTakes:
    """The scope the form offers: the rule the write applies, shown before."""

    @pytest.mark.parametrize(
        ("location", "is_bed", "ancestors", "scope"),
        [
            (_bed(), True, (), SoilHazardScope.ALL),
            (_bed("garden", type_key="garden"), False, (), SoilHazardScope.JUGLONE_ONLY),
            (_bed("planter", type_key="planter"), True, (), SoilHazardScope.CONTAINER),
            (_bed("pots", type_key="container"), False, (), SoilHazardScope.CONTAINER),
            (_bed(irrigation=IrrigationSystem.NFT), True, (), SoilHazardScope.HYDROPONIC),
            (_bed(), True, (_bed("room", type_key="room", irrigation=IrrigationSystem.HYDRO),), SoilHazardScope.ALL),
            (
                _bed("zone", type_key="zone"),
                False,
                (_bed("room", type_key="room", irrigation=IrrigationSystem.HYDRO),),
                SoilHazardScope.HYDROPONIC,
            ),
        ],
        ids=["bed", "area", "planter", "container_group", "own_hydro", "soil_bed_in_hydro_room", "area_in_hydro_room"],
    )
    def test_the_scope(self, location, is_bed, ancestors, scope) -> None:
        assert soil_hazard_scope(location, is_bed=is_bed, ancestors=ancestors) is scope


class TestTheSubstrateDateChange:
    """D-S3: the summary of the audit row - old and new ISO day, ``none`` for no day; nothing without a change."""

    @pytest.mark.parametrize(
        ("stored", "sent", "summary"),
        [
            (None, {"substrate_replaced_on": "2026-04-01"}, "none -> 2026-04-01"),
            (
                {"substrate_replaced_on": "2026-04-01"},
                {"substrate_replaced_on": "2026-05-01"},
                "2026-04-01 -> 2026-05-01",
            ),
            ({"substrate_replaced_on": "2026-04-01"}, {"drainage": "poor"}, "2026-04-01 -> none"),
            ({"substrate_replaced_on": "2026-04-01"}, None, "2026-04-01 -> none"),
            ({"substrate_replaced_on": date(2026, 4, 1)}, {"substrate_replaced_on": "2026-04-01"}, None),
            ({"drainage": "good"}, {"drainage": "poor"}, None),
            (None, None, None),
        ],
        ids=["set", "change", "cleared_field", "cleared_profile", "same_day", "other_field", "nothing"],
    )
    def test_the_summary(self, stored, sent, summary) -> None:
        assert substrate_replaced_on_change(stored, sent) == summary
