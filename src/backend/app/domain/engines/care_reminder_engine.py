from datetime import date, timedelta

from app.common.enums import (
    CareStyleType,
    ConfirmAction,
    FrostTolerance,
    HardinessRating,
    ReminderType,
    SeasonPhase,
    TuberStatus,
    WateringMethod,
)
from app.domain.engines.winter_hardiness_engine import map_frost_sensitivity
from app.domain.models.care_reminder import CareConfirmation, CareProfile
from app.domain.models.overwintering_profile import OverwinteringProfile
from app.domain.models.species import SeasonalWateringAdjustment, WateringGuide

# ── Overwintering / winter reminder wiring (REQ-022 §3.2) ──────────────

#: Reminder types whose generation is driven by an ``OverwinteringProfile`` and
#: suppressed for frost-hardy species (REQ-022 §"Winterschutz-Guard").
WINTER_PROTECTION_TYPES: frozenset[ReminderType] = frozenset(
    {
        ReminderType.WINTER_PROTECTION,
        ReminderType.SPRING_UNCOVER,
        ReminderType.TUBER_DIG,
        ReminderType.STORAGE_CHECK,
    }
)

#: Care styles for which deadheading reminders make sense (blooming ornamentals).
DEADHEADING_CARE_STYLES: frozenset[CareStyleType] = frozenset(
    {
        CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
        CareStyleType.OUTDOOR_PERENNIAL,
        CareStyleType.ROSE,
    }
)

#: Months in which deadheading is generated (northern-hemisphere growing season).
DEADHEADING_MONTHS: frozenset[int] = frozenset({5, 6, 7, 8, 9})

# ── Dormancy-aware phases ──────────────────────────────────────────────

DORMANCY_PHASES: frozenset[str] = frozenset(
    {
        "dormancy",
        "senescence",
        "hardening_off",
        "maintenance",
        "acclimatization",
        "repotting_recovery",
    }
)

# ── Care style presets ─────────────────────────────────────────────────

CARE_STYLE_PRESETS: dict[CareStyleType, dict] = {
    CareStyleType.TROPICAL: {
        "watering_interval_days": 7,
        "winter_watering_multiplier": 1.5,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 14,
        "fertilizing_active_months": [3, 4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 24,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": True,
        "humidity_check_interval_days": 7,
    },
    CareStyleType.SUCCULENT: {
        "watering_interval_days": 14,
        "winter_watering_multiplier": 3.0,
        "watering_method": WateringMethod.DRENCH_AND_DRAIN,
        "fertilizing_interval_days": 30,
        "fertilizing_active_months": [4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 36,
        "pest_check_interval_days": 21,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 14,
    },
    CareStyleType.ORCHID: {
        "watering_interval_days": 7,
        "winter_watering_multiplier": 2.0,
        "watering_method": WateringMethod.SOAK,
        "fertilizing_interval_days": 14,
        "fertilizing_active_months": [3, 4, 5, 6, 7, 8, 9, 10],
        "repotting_interval_months": 24,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": True,
        "humidity_check_interval_days": 7,
    },
    CareStyleType.CALATHEA: {
        "watering_interval_days": 5,
        "winter_watering_multiplier": 1.5,
        "watering_method": WateringMethod.BOTTOM_WATER,
        "water_quality_hint": "Filtered or rainwater only — sensitive to fluoride and chlorine",
        "fertilizing_interval_days": 21,
        "fertilizing_active_months": [4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 24,
        "pest_check_interval_days": 7,
        "humidity_check_enabled": True,
        "humidity_check_interval_days": 3,
    },
    CareStyleType.HERB_TROPICAL: {
        "watering_interval_days": 5,
        "winter_watering_multiplier": 1.5,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 14,
        "fertilizing_active_months": [3, 4, 5, 6, 7, 8, 9, 10],
        "repotting_interval_months": 12,
        "pest_check_interval_days": 7,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 14,
    },
    CareStyleType.MEDITERRANEAN: {
        "watering_interval_days": 10,
        "winter_watering_multiplier": 2.0,
        "watering_method": WateringMethod.DRENCH_AND_DRAIN,
        "fertilizing_interval_days": 30,
        "fertilizing_active_months": [4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 36,
        "pest_check_interval_days": 21,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 14,
    },
    CareStyleType.FERN: {
        "watering_interval_days": 4,
        "winter_watering_multiplier": 1.5,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 21,
        "fertilizing_active_months": [3, 4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 18,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": True,
        "humidity_check_interval_days": 3,
    },
    CareStyleType.CACTUS: {
        "watering_interval_days": 21,
        "winter_watering_multiplier": 4.0,
        "watering_method": WateringMethod.DRENCH_AND_DRAIN,
        "fertilizing_interval_days": 30,
        "fertilizing_active_months": [5, 6, 7, 8],
        "repotting_interval_months": 48,
        "pest_check_interval_days": 30,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 30,
    },
    CareStyleType.OUTDOOR_ANNUAL_VEG: {
        "watering_interval_days": 3,
        "winter_watering_multiplier": 1.0,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 14,
        "fertilizing_active_months": [4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 12,
        "pest_check_interval_days": 7,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 14,
    },
    CareStyleType.OUTDOOR_PERENNIAL: {
        "watering_interval_days": 5,
        "winter_watering_multiplier": 2.0,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 21,
        "fertilizing_active_months": [3, 4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 36,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 14,
    },
    # Outdoor/Freiland presets (REQ-022 §"Outdoor-/Freiland-Care-Style-Presets").
    # repotting_interval_months is capped at 60 (= "practically never" for
    # field-grown plants) because the model constrains it to 6..60; outdoor
    # plants don't get a repotting task unless auto_create_repotting_task is set.
    CareStyleType.FRUIT_TREE: {
        # Apple, pear, cherry, plum — established trees rarely need watering.
        "watering_interval_days": 14,
        "winter_watering_multiplier": 1.0,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 90,
        "fertilizing_active_months": [3, 4, 5],
        "repotting_interval_months": 60,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 30,
    },
    CareStyleType.BERRY_SHRUB: {
        # Raspberry, currant, gooseberry — water regularly in dry spells.
        "watering_interval_days": 7,
        "winter_watering_multiplier": 1.0,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 30,
        "fertilizing_active_months": [3, 4, 5, 6],
        "repotting_interval_months": 60,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 30,
    },
    CareStyleType.ROSE: {
        # Bed/shrub/climbing roses — water deeply once a week, near the base
        # (foliage wetting promotes black spot). Disease-prone, so a short
        # pest-check interval.
        "watering_interval_days": 7,
        "winter_watering_multiplier": 1.5,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 30,
        "fertilizing_active_months": [4, 5, 6, 7],
        "repotting_interval_months": 60,
        "pest_check_interval_days": 7,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 30,
    },
    CareStyleType.FROST_TENDER_TUBER: {
        # Dahlia, gladiolus, canna — dug up and stored frost-free over winter,
        # hence the maximal winter multiplier (effectively no winter watering).
        # Annual dig-and-replant cycle drives the 12-month repotting interval.
        "watering_interval_days": 5,
        "winter_watering_multiplier": 5.0,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 21,
        "fertilizing_active_months": [5, 6, 7, 8],
        "repotting_interval_months": 12,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 30,
    },
    CareStyleType.FROST_TENDER_CONTAINER: {
        # Oleander, citrus, olive — containers dry fast in summer, kept nearly
        # dry in the 5-12 C winter quarters.
        "watering_interval_days": 5,
        "winter_watering_multiplier": 4.0,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 21,
        "fertilizing_active_months": [4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 36,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 30,
    },
    CareStyleType.WINTER_VEGETABLE: {
        # Kale, lamb's lettuce, winter purslane — sown late summer, reduced
        # watering, left outdoors with fleece on bare frost.
        "watering_interval_days": 7,
        "winter_watering_multiplier": 2.0,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 30,
        "fertilizing_active_months": [8, 9],
        "repotting_interval_months": 12,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 30,
    },
    CareStyleType.SPRING_BULB: {
        # Tulip, daffodil, crocus, hyacinth — hardy, left in the ground; summer
        # dormancy means watering only matters during spring growth.
        "watering_interval_days": 14,
        "winter_watering_multiplier": 1.0,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 30,
        "fertilizing_active_months": [3, 4, 5],
        "repotting_interval_months": 60,
        "pest_check_interval_days": 30,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 30,
    },
    CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL: {
        # Pansy, primrose, geranium, lobelia — annual balcony/bed culture in
        # fast-drying containers; continuous bloomers need regular feeding.
        "watering_interval_days": 3,
        "winter_watering_multiplier": 1.0,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 14,
        "fertilizing_active_months": [4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 12,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 14,
    },
    CareStyleType.CUSTOM: {
        "watering_interval_days": 7,
        "winter_watering_multiplier": 1.5,
        "watering_method": WateringMethod.TOP_WATER,
        "fertilizing_interval_days": 14,
        "fertilizing_active_months": [3, 4, 5, 6, 7, 8, 9],
        "repotting_interval_months": 24,
        "pest_check_interval_days": 14,
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 14,
    },
}

# ── Botanical family → care style mapping ──────────────────────────────

FAMILY_CARE_MAP: dict[str, CareStyleType] = {
    "Araceae": CareStyleType.TROPICAL,
    "Marantaceae": CareStyleType.CALATHEA,
    "Orchidaceae": CareStyleType.ORCHID,
    "Cactaceae": CareStyleType.CACTUS,
    "Crassulaceae": CareStyleType.SUCCULENT,
    "Asphodelaceae": CareStyleType.SUCCULENT,
    "Polypodiaceae": CareStyleType.FERN,
    "Lamiaceae": CareStyleType.HERB_TROPICAL,
    "Oleaceae": CareStyleType.MEDITERRANEAN,
    "Moraceae": CareStyleType.TROPICAL,
    # REQ-022 §"FAMILY_CARE_MAP-Erweiterung für Zierpflanzen" — annual outdoor
    # ornamentals (pansy, primrose, geranium, lobelia, busy Lizzie).
    "Violaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
    "Primulaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
    "Geraniaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
    "Campanulaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
    "Balsaminaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
}


class CareReminderEngine:
    """Pure domain logic for care reminders — no I/O."""

    def calculate_due_date(
        self,
        profile: CareProfile,
        reminder_type: ReminderType,
        last_confirmation: CareConfirmation | None,
        current_phase: str | None = None,
        hemisphere: str = "north",
        phase_watering_interval: int | None = None,
        overwintering_profile: OverwinteringProfile | None = None,
    ) -> date | None:
        """Calculate the next due date for a specific reminder type."""
        interval = self._get_interval_days(
            profile,
            reminder_type,
            hemisphere,
            phase_watering_interval=phase_watering_interval,
            overwintering_profile=overwintering_profile,
        )
        if interval is None:
            return None

        if last_confirmation is not None:
            base = last_confirmation.confirmed_at.date()
            if last_confirmation.action == ConfirmAction.SNOOZED and last_confirmation.snooze_days:
                return base + timedelta(days=last_confirmation.snooze_days)
            return base + timedelta(days=interval)

        # No previous confirmation — due immediately (creation date)
        if profile.created_at:
            return profile.created_at.date()
        return date.today()

    def calculate_urgency(self, due_date: date | None) -> str:
        """Determine urgency level from due date."""
        if due_date is None:
            return "not_due"
        today = date.today()
        delta = (due_date - today).days
        if delta < 0:
            return "overdue"
        if delta == 0:
            return "due_today"
        if delta <= 2:
            return "upcoming"
        return "not_due"

    def should_generate_reminder(
        self,
        profile: CareProfile,
        reminder_type: ReminderType,
        current_phase: str | None = None,
        hemisphere: str = "north",
        month: int | None = None,
        has_active_watering_plan: bool = False,
        has_nutrient_plan: bool = False,
        overwintering_profile: OverwinteringProfile | None = None,
        frost_sensitivity: FrostTolerance | None = None,
        cultivar_traits: list[str] | None = None,
        winter_quarter_has_livedata: bool = False,
        season_phase: SeasonPhase | None = None,
    ) -> bool:
        """Check whether a reminder should be generated.

        ``season_phase`` is the REQ-047 SeasonState phase of the plant's site when
        one exists. It is the *primary* trigger for the winter-protection reminders:
        given a phase, they fire on the season transition (``pre_winter`` /
        ``pre_spring``) rather than on a fixed calendar month. ``None`` means the
        site has no SeasonState, so the month-based calendar fallback applies.
        """
        if month is None:
            month = date.today().month

        # Winter protection reminders (REQ-022 §3.2 / REQ-047 §3.2) — driven by the
        # OverwinteringProfile. When a SeasonState governs the site the season phase
        # is the trigger (pre_winter → protection/dig, pre_spring → uncover);
        # otherwise the calendar month is the fallback.
        if reminder_type in WINTER_PROTECTION_TYPES:
            return self._should_generate_winter_reminder(
                reminder_type,
                overwintering_profile,
                frost_sensitivity,
                month,
                season_phase,
            )

        # REQ-047 §2.5 dormancy control reminders — only while the dormancy-care
        # mode is active (set by the season state machine on winter_dormancy).
        # Evaluated before the generic tail, which would otherwise return True.
        if reminder_type == ReminderType.DORMANCY_HEALTH_CHECK:
            return profile.dormancy_care_mode
        if reminder_type == ReminderType.QUARTER_CLIMATE_CHECK:
            # The winter-quarter climate warning needs live data of the quarter
            # (sensor/HA); without it, it cannot fire (REQ-047 §2.5 / AC-13).
            return profile.dormancy_care_mode and winter_quarter_has_livedata

        # Deadheading (REQ-022 §3.2 / AB-016) — blooming ornamentals only, and
        # never for self-cleaning cultivars.
        if reminder_type == ReminderType.DEADHEADING:
            if cultivar_traits and "self_cleaning" in cultivar_traits:
                return False
            return profile.care_style in DEADHEADING_CARE_STYLES and month in DEADHEADING_MONTHS

        # Gießplan-Guard: suppress watering/fertilizing if active watering plan
        if has_active_watering_plan and reminder_type in (
            ReminderType.WATERING,
            ReminderType.FERTILIZING,
        ):
            return False

        # Per-type toggle guards
        if reminder_type == ReminderType.FERTILIZING and not profile.auto_create_fertilizing_task:
            return False
        if reminder_type == ReminderType.REPOTTING and not profile.auto_create_repotting_task:
            return False
        if reminder_type == ReminderType.PEST_CHECK and not profile.auto_create_pest_check_task:
            return False

        # Fertilizing only makes sense when a nutrient plan is assigned
        if reminder_type == ReminderType.FERTILIZING and not has_nutrient_plan:
            return False

        # Dormancy guard — suppress all except pest_check during dormancy
        if current_phase and current_phase.lower() in DORMANCY_PHASES:
            return reminder_type == ReminderType.PEST_CHECK

        # Fertilizing guard — only in active months
        if reminder_type == ReminderType.FERTILIZING and month not in profile.fertilizing_active_months:
            return False

        # Location check guard
        if reminder_type == ReminderType.LOCATION_CHECK:
            if not profile.location_check_enabled:
                return False
            if profile.location_check_months and month not in profile.location_check_months:
                return False

        # Humidity check guard
        return not (reminder_type == ReminderType.HUMIDITY_CHECK and not profile.humidity_check_enabled)

    def apply_adaptive_learning(
        self,
        profile: CareProfile,
        reminder_type: ReminderType,
        confirmations: list[CareConfirmation],
    ) -> int | None:
        """Compute a learned interval from confirmation history.

        Returns a new interval if ≥3 consistent signals, else None.
        Deviation capped at ±30% of base interval.
        """
        if not profile.adaptive_learning_enabled:
            return None

        # Only watering and fertilizing support adaptive learning
        if reminder_type == ReminderType.WATERING:
            base_interval = profile.watering_interval_days
        elif reminder_type == ReminderType.FERTILIZING:
            base_interval = profile.fertilizing_interval_days
        else:
            return None

        # Need at least 3 confirmed (not snoozed/skipped) entries
        confirmed = [
            c for c in confirmations if c.action == ConfirmAction.CONFIRMED and c.reminder_type == reminder_type
        ]
        if len(confirmed) < 3:
            return None

        # Look at the last 5 for trend
        recent = sorted(confirmed, key=lambda c: c.confirmed_at)[-5:]

        # Calculate actual intervals between confirmations
        actual_intervals: list[int] = []
        for i in range(1, len(recent)):
            delta = (recent[i].confirmed_at.date() - recent[i - 1].confirmed_at.date()).days
            if delta > 0:
                actual_intervals.append(delta)

        if len(actual_intervals) < 2:
            return None

        avg_actual = sum(actual_intervals) / len(actual_intervals)

        # Cap deviation at ±30%
        min_interval = max(1, int(base_interval * 0.7))
        max_interval = int(base_interval * 1.3)
        learned = max(min_interval, min(max_interval, round(avg_actual)))

        # Only adjust by ±1 day at a time
        if reminder_type == ReminderType.WATERING:
            current = profile.watering_interval_learned or base_interval
        else:
            current = profile.fertilizing_interval_learned or base_interval

        if learned > current:
            return current + 1
        if learned < current:
            return current - 1
        return current

    def auto_generate_profile(
        self,
        species_name: str | None = None,
        botanical_family: str | None = None,
        plant_key: str = "",
        watering_guide: WateringGuide | None = None,
    ) -> CareProfile:
        """Generate a CareProfile from species/family defaults.

        Three-tier fallback:
        1. WateringGuide (species-specific structured data) — highest priority
        2. FAMILY_CARE_MAP → CARE_STYLE_PRESETS (family-level generic)
        3. TROPICAL preset (default fallback)
        """
        care_style = CareStyleType.TROPICAL  # default fallback

        if botanical_family and botanical_family in FAMILY_CARE_MAP:
            care_style = FAMILY_CARE_MAP[botanical_family]

        preset = dict(CARE_STYLE_PRESETS[care_style])

        # Tier 2: Override preset values with species-specific WateringGuide
        if watering_guide is not None:
            preset["watering_interval_days"] = watering_guide.interval_days
            preset["watering_method"] = watering_guide.watering_method
            if watering_guide.water_quality_hint:
                preset["water_quality_hint"] = watering_guide.water_quality_hint
            # Compute winter multiplier from seasonal adjustments
            winter_adj = self._find_winter_adjustment(watering_guide)
            if winter_adj is not None and watering_guide.interval_days > 0:
                preset["winter_watering_multiplier"] = round(
                    winter_adj.interval_days / watering_guide.interval_days,
                    2,
                )

        return CareProfile(
            care_style=care_style,
            plant_key=plant_key,
            auto_generated=True,
            notes=watering_guide.practical_tip if watering_guide else None,
            **preset,
        )

    @staticmethod
    def _find_winter_adjustment(
        guide: WateringGuide,
    ) -> SeasonalWateringAdjustment | None:
        """Find the seasonal adjustment that covers winter months."""

        winter_months = {11, 12, 1, 2}
        for adj in guide.seasonal_adjustments:
            if winter_months & set(adj.months):
                return adj
        return None

    # ── Private helpers ──────────────────────────────────────────────

    @staticmethod
    def _should_generate_winter_reminder(
        reminder_type: ReminderType,
        overwintering_profile: OverwinteringProfile | None,
        frost_sensitivity: FrostTolerance | None,
        month: int,
        season_phase: SeasonPhase | None = None,
    ) -> bool:
        """Gate the four overwintering reminder types against the profile.

        No profile → nothing to remind about. Frost-hardy species never receive
        winter-protection reminders (REQ-022 §"Winterschutz-Guard").

        When ``season_phase`` is given (the plant's site has a REQ-047 SeasonState),
        the season transition is the trigger: ``winter_protection`` / ``tuber_dig``
        on ``pre_winter``, ``spring_uncover`` on ``pre_spring`` — independent of the
        calendar month. Without a SeasonState the month windows are the fallback.
        """
        if overwintering_profile is None:
            return False
        if map_frost_sensitivity(frost_sensitivity) == "hardy":
            return False

        profile = overwintering_profile
        is_dig_and_store = profile.hardiness_rating == HardinessRating.DIG_AND_STORE

        if reminder_type == ReminderType.STORAGE_CHECK:
            # Recurring while tubers are actually drying/stored — status-gated on
            # both tiers (never month- or phase-gated).
            return (
                is_dig_and_store
                and profile.storage_check_interval_days is not None
                and profile.tuber_status in (TuberStatus.DRYING, TuberStatus.STORED)
            )

        if season_phase is not None:
            # SeasonState-driven (primary): the phase is the trigger, not the month.
            if reminder_type == ReminderType.WINTER_PROTECTION:
                return season_phase == SeasonPhase.PRE_WINTER
            if reminder_type == ReminderType.TUBER_DIG:
                return season_phase == SeasonPhase.PRE_WINTER and is_dig_and_store
            if reminder_type == ReminderType.SPRING_UNCOVER:
                return season_phase == SeasonPhase.PRE_SPRING and profile.spring_action is not None
            return False

        # Calendar fallback (no SeasonState for the site): month-gated.
        if reminder_type == ReminderType.WINTER_PROTECTION:
            return month == profile.winter_action_month
        if reminder_type == ReminderType.SPRING_UNCOVER:
            return profile.spring_action is not None and profile.spring_action_month == month
        if reminder_type == ReminderType.TUBER_DIG:
            return is_dig_and_store and month == profile.winter_action_month
        return False

    def _get_interval_days(
        self,
        profile: CareProfile,
        reminder_type: ReminderType,
        hemisphere: str = "north",
        phase_watering_interval: int | None = None,
        overwintering_profile: OverwinteringProfile | None = None,
    ) -> int | None:
        """Get the interval in days for a reminder type, season-adjusted."""
        month = date.today().month
        is_winter = self._is_winter(month, hemisphere)

        # REQ-047 §2.5 dormancy control reminders.
        if reminder_type == ReminderType.DORMANCY_HEALTH_CHECK:
            return profile.dormancy_check_interval_days
        if reminder_type == ReminderType.QUARTER_CLIMATE_CHECK:
            # Frequent check while the quarter has live data — a temperature
            # violation is time-critical (plant freezes / breaks dormancy early).
            return 7

        # Overwintering reminder types (REQ-022 §3.2).
        if reminder_type == ReminderType.DEADHEADING:
            return 7
        if reminder_type == ReminderType.STORAGE_CHECK:
            if overwintering_profile and overwintering_profile.storage_check_interval_days:
                return overwintering_profile.storage_check_interval_days
            return 30
        if reminder_type in (
            ReminderType.WINTER_PROTECTION,
            ReminderType.SPRING_UNCOVER,
            ReminderType.TUBER_DIG,
        ):
            # Annual, month-gated actions — recur once per year.
            return 365

        if reminder_type == ReminderType.WATERING:
            # Phase-specific interval takes priority over care profile
            base = phase_watering_interval or profile.watering_interval_learned or profile.watering_interval_days
            # REQ-047 §3.5 dormancy-care mode replaces the seasonal multiplier with
            # the discrete dormancy_watering regime.
            if profile.dormancy_care_mode and profile.dormancy_watering is not None:
                dormant = self._dormancy_watering_interval(profile, base)
                if dormant is not None or profile.dormancy_watering == "none":
                    return dormant
            if is_winter:
                return int(base * profile.winter_watering_multiplier)
            return base

        if reminder_type == ReminderType.FERTILIZING:
            return profile.fertilizing_interval_learned or profile.fertilizing_interval_days

        if reminder_type == ReminderType.REPOTTING:
            return profile.repotting_interval_months * 30

        if reminder_type == ReminderType.PEST_CHECK:
            return profile.pest_check_interval_days

        if reminder_type == ReminderType.LOCATION_CHECK:
            return 30  # monthly

        if reminder_type == ReminderType.HUMIDITY_CHECK:
            return profile.humidity_check_interval_days

        return None

    @staticmethod
    def _dormancy_watering_interval(profile: CareProfile, base: int) -> int | None:
        """REQ-047 §3.5 — discrete dormancy watering interval (days).

        ``none`` → no watering reminder; ``minimal`` → ~38 days; ``reduced`` →
        ``winter_watering_multiplier × 1.5`` of the base; ``normal`` → the plain
        seasonal interval.
        """
        regime = profile.dormancy_watering
        if regime == "none":
            return None
        if regime == "minimal":
            return 38
        if regime == "reduced":
            return max(1, int(base * profile.winter_watering_multiplier * 1.5))
        return base

    @staticmethod
    def _is_winter(month: int, hemisphere: str) -> bool:
        if hemisphere == "south":
            return month in (6, 7, 8)
        return month in (12, 1, 2)
