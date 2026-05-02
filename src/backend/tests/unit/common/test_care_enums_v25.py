"""REQ-022 v2.5 enum extensions — outdoor presets + overwintering reminder types."""

from app.common.enums import CareStyleType, ReminderType


class TestOutdoorPresets:
    def test_seven_new_outdoor_presets_exist(self):
        # All seven follow-up presets called out in Phase 0 (REQ-022 v2.5 §3.1)
        # must be representable as enum members.
        for name in (
            "FRUIT_TREE",
            "BERRY_SHRUB",
            "ROSE",
            "FROST_TENDER_TUBER",
            "FROST_TENDER_CONTAINER",
            "WINTER_VEGETABLE",
            "SPRING_BULB",
            "OUTDOOR_ANNUAL_ORNAMENTAL",
        ):
            assert hasattr(CareStyleType, name), name

    def test_existing_presets_still_present(self):
        # Backwards compatibility — the v2.3 presets must keep their values.
        assert CareStyleType.TROPICAL.value == "tropical"
        assert CareStyleType.OUTDOOR_ANNUAL_VEG.value == "outdoor_annual_veg"
        assert CareStyleType.CUSTOM.value == "custom"


class TestOverwinteringReminderTypes:
    def test_five_new_reminder_types_exist(self):
        # REQ-022 v2.5 §3.2 — outdoor + overwintering verbs.
        for name in (
            "DEADHEADING",
            "TUBER_DIG",
            "STORAGE_CHECK",
            "SPRING_UNCOVER",
            "WINTER_PROTECTION",
        ):
            assert hasattr(ReminderType, name), name

    def test_existing_reminder_types_still_present(self):
        assert ReminderType.WATERING.value == "watering"
        assert ReminderType.FERTILIZING.value == "fertilizing"
        assert ReminderType.PEST_CHECK.value == "pest_check"
