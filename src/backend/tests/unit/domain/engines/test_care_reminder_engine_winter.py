"""REQ-022 §3.2 — winter/overwintering reminder wiring in CareReminderEngine."""

from app.common.enums import (
    CareStyleType,
    FrostTolerance,
    HardinessRating,
    ReminderType,
    SpringAction,
    TuberStatus,
    WinterAction,
)
from app.domain.engines.care_reminder_engine import FAMILY_CARE_MAP, CareReminderEngine
from app.domain.models.care_reminder import CareProfile
from app.domain.models.overwintering_profile import OverwinteringProfile

ENGINE = CareReminderEngine()


def _owp(**overrides) -> OverwinteringProfile:
    data = {
        "plant_key": "p1",
        "hardiness_rating": HardinessRating.DIG_AND_STORE,
        "winter_action": WinterAction.DIG_STORE,
        "winter_action_month": 10,
        "spring_action": SpringAction.REPLANT,
        "spring_action_month": 3,
        "storage_check_interval_days": 30,
        "tuber_status": TuberStatus.STORED,
    }
    data.update(overrides)
    return OverwinteringProfile(**data)


def _care(style: CareStyleType = CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL) -> CareProfile:
    return CareProfile(care_style=style, plant_key="p1")


class TestWinterReminderGeneration:
    def test_all_five_winter_reminders_generated(self) -> None:
        owp = _owp()
        care = _care()
        frost = FrostTolerance.SENSITIVE

        assert ENGINE.should_generate_reminder(
            care, ReminderType.WINTER_PROTECTION, month=10, overwintering_profile=owp, frost_sensitivity=frost
        )
        assert ENGINE.should_generate_reminder(
            care, ReminderType.TUBER_DIG, month=10, overwintering_profile=owp, frost_sensitivity=frost
        )
        assert ENGINE.should_generate_reminder(
            care, ReminderType.SPRING_UNCOVER, month=3, overwintering_profile=owp, frost_sensitivity=frost
        )
        assert ENGINE.should_generate_reminder(
            care, ReminderType.STORAGE_CHECK, month=1, overwintering_profile=owp, frost_sensitivity=frost
        )
        assert ENGINE.should_generate_reminder(care, ReminderType.DEADHEADING, month=6, cultivar_traits=None)

    def test_winter_reminders_need_profile(self) -> None:
        care = _care()
        assert not ENGINE.should_generate_reminder(
            care, ReminderType.WINTER_PROTECTION, month=10, frost_sensitivity=FrostTolerance.SENSITIVE
        )

    def test_winter_protection_month_gated(self) -> None:
        owp = _owp()
        assert not ENGINE.should_generate_reminder(
            _care(),
            ReminderType.WINTER_PROTECTION,
            month=6,
            overwintering_profile=owp,
            frost_sensitivity=FrostTolerance.SENSITIVE,
        )


class TestWinterProtectionGuard:
    def test_hardy_species_get_no_winter_reminders(self) -> None:
        owp = _owp()
        for rt in (
            ReminderType.WINTER_PROTECTION,
            ReminderType.TUBER_DIG,
            ReminderType.SPRING_UNCOVER,
            ReminderType.STORAGE_CHECK,
        ):
            assert not ENGINE.should_generate_reminder(
                _care(),
                rt,
                month=10,
                overwintering_profile=owp,
                frost_sensitivity=FrostTolerance.HARDY,
            )
        assert not ENGINE.should_generate_reminder(
            _care(),
            ReminderType.WINTER_PROTECTION,
            month=10,
            overwintering_profile=owp,
            frost_sensitivity=FrostTolerance.VERY_HARDY,
        )


class TestDeadheadingGuard:
    def test_self_cleaning_cultivar_gets_no_deadheading(self) -> None:
        assert not ENGINE.should_generate_reminder(
            _care(), ReminderType.DEADHEADING, month=6, cultivar_traits=["self_cleaning"]
        )

    def test_deadheading_only_for_blooming_styles(self) -> None:
        assert not ENGINE.should_generate_reminder(_care(CareStyleType.CACTUS), ReminderType.DEADHEADING, month=6)

    def test_deadheading_out_of_season(self) -> None:
        assert not ENGINE.should_generate_reminder(_care(), ReminderType.DEADHEADING, month=1)


class TestFamilyCareMap:
    def test_new_ornamental_families_mapped(self) -> None:
        for family in ("Violaceae", "Primulaceae", "Geraniaceae", "Campanulaceae", "Balsaminaceae"):
            assert FAMILY_CARE_MAP[family] == CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL


class TestWinterIntervals:
    def test_storage_check_uses_profile_interval(self) -> None:
        owp = _owp(storage_check_interval_days=21)
        assert ENGINE._get_interval_days(_care(), ReminderType.STORAGE_CHECK, overwintering_profile=owp) == 21

    def test_annual_winter_actions_recur_yearly(self) -> None:
        assert ENGINE._get_interval_days(_care(), ReminderType.WINTER_PROTECTION) == 365
        assert ENGINE._get_interval_days(_care(), ReminderType.TUBER_DIG) == 365
        assert ENGINE._get_interval_days(_care(), ReminderType.SPRING_UNCOVER) == 365
