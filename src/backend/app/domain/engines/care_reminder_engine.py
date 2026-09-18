from datetime import date, timedelta

import structlog

from app.common.datetimes import today_utc
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

logger = structlog.get_logger()

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


def evaluate_quarter_climate_violation(
    profile: OverwinteringProfile,
    current_temp_c: float | None,
) -> str | None:
    """REQ-047 §3.7.3 / AC-22 — classify a winter-quarter temperature violation.

    Compares the quarter's live temperature against the profile's
    ``winter_quarter_temp_min`` / ``winter_quarter_temp_max`` band. Returns
    ``"too_cold"`` below the minimum (heating failure → the plant freezes),
    ``"too_warm"`` above the maximum (overheating → premature budding) and ``None``
    when the reading is inside the band or the data needed for a comparison is
    missing (no reading, or the profile carries no bound). Pure and deterministic.
    """
    if current_temp_c is None:
        return None
    if profile.winter_quarter_temp_min is not None and current_temp_c < profile.winter_quarter_temp_min:
        return "too_cold"
    if profile.winter_quarter_temp_max is not None and current_temp_c > profile.winter_quarter_temp_max:
        return "too_warm"
    return None


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
    # REQ-022 §"FAMILY_CARE_MAP-Abdeckung aller geseedeten Familien" (#1505) — the
    # two seeded families no existing preset fits. Every value below is the median
    # of the `care_profiles.*` rows the seeded species' own Steckbriefe declare in
    # `spec/knowledge/plants/*.md` §4.1; the source is named per field.
    CareStyleType.BROMELIAD: {
        # Funnel-watered epiphytes (Aechmea, Guzmania, Neoregelia, Vriesea,
        # Tillandsia). Neither TROPICAL nor ORCHID fits: the water goes into the
        # leaf funnel rather than the substrate, and the family is an extreme light
        # feeder (botanical_families.yaml: "extreme Schwachzehrer"), so ORCHID's
        # 14-day feeding would overfeed it.
        # 7 d: median of 7/7/7/10/3 (guzmania, vriesea, aechmea, neoregelia,
        #      tillandsia §4.1 "Giessintervall Sommer").
        "watering_interval_days": 7,
        # 1.5: guzmania_lingulata.md / neoregelia_carolinae.md / vriesea_splendens.md
        #      (aechmea + tillandsia say 2.0).
        "winter_watering_multiplier": 1.5,
        # top_water "in Trichter" — 4 of 5 docs; only the rootless Tillandsia soaks.
        "watering_method": WateringMethod.TOP_WATER,
        # All five docs carry a lime-free hint; wording condensed from
        # guzmania_lingulata.md §4.1 + its "Trichter-Giesskultur" instructions.
        "water_quality_hint": (
            "Lime-free water (rain or well-stood tap water) into the leaf funnel — hard water clogs the "
            "trichomes. Swap the funnel water every 4-6 weeks and keep the substrate only slightly moist"
        ),
        # 28 d: median of 28/21/42/42/28.
        "fertilizing_interval_days": 28,
        # 4-9: aechmea/neoregelia/vriesea/tillandsia; guzmania starts in March.
        "fertilizing_active_months": [4, 5, 6, 7, 8, 9],
        # 24 months: guzmania/aechmea/neoregelia/vriesea (Tillandsia has no pot).
        "repotting_interval_months": 24,
        # 21 d: median of 21/14/21/14/21.
        "pest_check_interval_days": 21,
        # true in all five docs.
        "humidity_check_enabled": True,
        # 14 d: guzmania_lingulata.md §4.1.
        "humidity_check_interval_days": 14,
    },
    CareStyleType.AQUATIC: {
        # Pond plants rooted in a planting basket (Nymphaea). nymphaea_alba.md §4.1
        # states outright: "`custom` (kein Standard-Preset passt fuer aquatische
        # Pflanzen)" — this preset is that missing one, built from the same table.
        # A water lily is never watered; the watering reminder is the weekly
        # pond-level top-up the doc quantifies as "ca. 2-5 cm/Woche im Sommer".
        "watering_interval_days": 7,
        # The doc's overwintering table says winter watering is "none (aquatisch,
        # steht im Wasser)" — 4.0 turns the weekly top-up into a monthly level check.
        "winter_watering_multiplier": 4.0,
        # "nicht anwendbar (Teich)" in the doc; TOP_WATER is the only enum member
        # that does not misdescribe topping a pond up.
        "watering_method": WateringMethod.TOP_WATER,
        # Condensed from nymphaea_alba.md §3.1 and §4.1 "Wasserqualitaet-Hinweis".
        "water_quality_hint": (
            "Pond-level check, not a watering: top up 2-5 cm per week in summer. Tap water is fine at "
            "pH 6.5-8.5. Feed with depot tablets pressed into the basket substrate only — liquid "
            "fertiliser in the pond water causes an algae bloom"
        ),
        # "28-42 (alle 4-6 Wochen, Depot-Tabletten)" → 30.
        "fertilizing_interval_days": 30,
        # "4-8 (April bis August)"; the doc's care calendar names August as the last feed.
        "fertilizing_active_months": [4, 5, 6, 7, 8],
        # "36-60 (alle 3-5 Jahre Pflanzkorb erneuern und Rhizom teilen)" → 48.
        "repotting_interval_months": 48,
        # 14 d in the doc (water-lily aphid, water-lily leaf beetle).
        "pest_check_interval_days": 14,
        # "false (aquatisch)".
        "humidity_check_enabled": False,
        "humidity_check_interval_days": 30,
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

#: Botanical family **name** → the care-style preset a plant of that family gets
#: when its species carries no ``WateringGuide`` (tier 2 of
#: :meth:`CareReminderEngine.auto_generate_profile`).
#:
#: **Coverage (#1505).** Until 2026-09-18 this was a houseplant map: it knew 14 of
#: the 63 families the seeds create, and a tomato, a cabbage and a rose fell to the
#: tier-3 ``TROPICAL`` 7-day houseplant fallback. It now covers every seeded family;
#: ``TROPICAL`` stays the last tier for a family no seed declares (a user-created
#: species, an import).
#:
#: The issue measured "18 seeded families, 4 mapped" from
#: ``botanical_families.yaml`` alone. Measured over *every* seed file
#: (``plant_info_*.yaml``, ``adventskalender.yaml`` each carry a ``new_families``
#: block, and six more families are named only by a species' ``family``): **63
#: seeded, 14 mapped, 49 added here.** The guard in
#: ``tests/unit/domain/engines/test_care_reminder_engine_family_map.py`` derives the
#: population the same way, so the map cannot fall behind a new seed file again.
#:
#: **How each style was derived, in this order:**
#:
#: 1. The ``Pflege-Stil`` value the family's own Steckbriefe declare in
#:    ``spec/knowledge/plants/<species>.md`` §4.1 ``care_profiles.care_style`` —
#:    209 of the 210 documents carry one — taking the majority per family.
#: 2. Where that majority is absent, tied, ``custom``, or not a ``CareStyleType``
#:    member at all (two documents say ``temperate``, which no version of the enum
#:    has ever had), the style whose preset matches the family's dominant
#:    cultivation form in the seeds (``plant_category``, ``growth_habit``,
#:    ``frost_sensitivity``). Every such deviation is named on its line.
#: 3. ``CUSTOM`` is never a family default: as a *default* it is the ``TROPICAL``
#:    numbers under a name that tells the user nothing.
#:
#: A family default is necessarily coarse — Rosaceae holds an apple tree and a
#: strawberry, Asparagaceae a snake plant and asparagus. It is the *third* tier: a
#: species with a ``WateringGuide`` overrides the watering fields (#1481), and the
#: user can change the profile. The choice is "which preset is least wrong for the
#: species this family actually seeds", not "which is right for all of them".
FAMILY_CARE_MAP: dict[str, CareStyleType] = {
    # ── Indoor / houseplant families ──────────────────────────────────
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
    # #1505 additions. Rule 1 unless the line says otherwise.
    "Acanthaceae": CareStyleType.CALATHEA,  # aphelandra, fittonia: calathea 2/2
    "Aizoaceae": CareStyleType.CACTUS,  # lithops_spp.md: cactus
    "Apocynaceae": CareStyleType.TROPICAL,  # hoya, stephanotis 2/3 (ceropegia: succulent)
    "Araliaceae": CareStyleType.MEDITERRANEAN,  # fatsia, hedera 2/3 — cool-tolerant, dries back
    "Arecaceae": CareStyleType.TROPICAL,  # indoor palms 4/4
    # Rule 1 on the deduplicated docs (dracaena_marginata appears twice):
    # succulent 4 (aspidistra, d. angolensis, d. trifasciata, yucca) vs tropical 2.
    # The family record itself warns it is heterogeneous ("Artspezifische
    # Pflegedaten beachten") — SUCCULENT is the safer default, since these store
    # water and rot when watered on a 7-day tropical rhythm.
    "Asparagaceae": CareStyleType.SUCCULENT,
    "Aspleniaceae": CareStyleType.FERN,  # asplenium_nidus.md: fern
    "Begoniaceae": CareStyleType.TROPICAL,  # rule 2: calathea/tropical tie, generic wins
    "Bromeliaceae": CareStyleType.BROMELIAD,  # rule 2: no preset fitted — see CARE_STYLE_PRESETS
    "Commelinaceae": CareStyleType.TROPICAL,  # tradescantia_zebrina.md: tropical
    "Euphorbiaceae": CareStyleType.TROPICAL,  # croton, poinsettia 2/2
    "Gesneriaceae": CareStyleType.CALATHEA,  # streptocarpus 2/3 — bottom water, soft water
    "Malvaceae": CareStyleType.TROPICAL,  # hibiscus, pachira 2/2
    "Nephrolepidaceae": CareStyleType.FERN,  # nephrolepis_exaltata.md: fern
    "Oxalidaceae": CareStyleType.TROPICAL,  # oxalis_triangularis.md: tropical
    "Piperaceae": CareStyleType.SUCCULENT,  # peperomia_obtusifolia.md: succulent
    "Pteridaceae": CareStyleType.FERN,  # adiantum_raddianum.md: fern
    "Rubiaceae": CareStyleType.TROPICAL,  # rule 2: coffea/gardenia tie, both warm indoor
    # Rule 2. strelitzia_reginae.md says `mediterranean`, which the seeds
    # contradict: tropical_foliage, indoor_suitable=yes, frost sensitive. The
    # MEDITERRANEAN preset's 10-day drench-and-drain is a winter-dry regime.
    "Strelitziaceae": CareStyleType.TROPICAL,
    "Urticaceae": CareStyleType.TROPICAL,  # rule 2: pilea/soleirolia tie, both warm indoor
    # ── Outdoor edible families ───────────────────────────────────────
    "Amaranthaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,  # beetroot, spinach
    # Rule 2. Split docs (2 tropical for the indoor bulbs Clivia/Hippeastrum), but
    # 4 of the 6 seeded species are kitchen-garden Alliums (onion, leek, garlic,
    # chives).
    "Amaryllidaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,
    "Apiaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,  # carrot, celery, parsnip … 5/9
    # Rule 2. mediterranean 3 / outdoor_annual_veg 3 / custom 2 (lactuca, dahlia);
    # counting the two `custom` vegetables, the kitchen-garden reading is 5 of 10.
    # Trade-off named: Tagetes and Dahlia thereby lose the deadheading reminder
    # (DEADHEADING_CARE_STYLES), which a per-species override should restore.
    "Asteraceae": CareStyleType.OUTDOOR_ANNUAL_VEG,
    "Boraginaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,  # phacelia, green manure
    "Brassicaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,  # 8/9
    # Rule 2. humulus_lupulus.md (the only doc with a style) says `mediterranean`,
    # but the family record says `typical_nutrient_demand: heavy` and the second
    # seeded species is Cannabis sativa (indoor, heavy feeder) — a 30-day feeding
    # interval contradicts both.
    "Cannabaceae": CareStyleType.HERB_TROPICAL,
    "Cucurbitaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,  # rule 2: 3/3 tie, all six are outdoor veg
    "Fabaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,  # 6/8
    "Poaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,  # cereals 6/6
    "Solanaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,  # tomato, pepper, potato … 5/6
    "Tropaeolaceae": CareStyleType.OUTDOOR_ANNUAL_VEG,  # tropaeolum_majus.md
    # ── Outdoor ornamental, perennial and woody families ──────────────
    "Violaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
    "Primulaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
    "Geraniaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
    "Balsaminaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
    "Adoxaceae": CareStyleType.OUTDOOR_PERENNIAL,  # sambucus, viburnum 2/2
    "Buxaceae": CareStyleType.MEDITERRANEAN,  # buxus_sempervirens.md
    "Caprifoliaceae": CareStyleType.MEDITERRANEAN,  # weigela_florida.md
    "Cornaceae": CareStyleType.MEDITERRANEAN,  # cornus_mas.md
    # Rule 2/3. All three docs say `custom`. Vaccinium corymbosum *is* a berry
    # shrub, and BERRY_SHRUB's numbers (7-day water, 30-day feed Mar-Jun) fit the
    # ericaceous acid-soil, low-feed regime the Rhododendron docs describe too. The
    # lime-free water the family needs has no home in a shared preset yet.
    "Ericaceae": CareStyleType.BERRY_SHRUB,
    # Rule 2/3. Both docs say `custom`; currant and gooseberry are literally the
    # plants BERRY_SHRUB was written for.
    "Grossulariaceae": CareStyleType.BERRY_SHRUB,
    # Rule 2. hydrangea_macrophylla.md says `temperate`, which is not a
    # CareStyleType. Hardy outdoor shrub with a high water demand → the 5-day
    # OUTDOOR_PERENNIAL interval.
    "Hydrangeaceae": CareStyleType.OUTDOOR_PERENNIAL,
    # Rule 2. tigridia_pavonia.md says `mediterranean`; the seeds say
    # plant_category=bulb_tuber, frost-sensitive geophyte — which is exactly what
    # FROST_TENDER_TUBER ("dug up and stored frost-free") describes.
    "Iridaceae": CareStyleType.FROST_TENDER_TUBER,
    "Nymphaeaceae": CareStyleType.AQUATIC,  # rule 2: the doc asks for this preset by name
    "Paeoniaceae": CareStyleType.OUTDOOR_PERENNIAL,  # paeonia_lactiflora.md
    "Polemoniaceae": CareStyleType.OUTDOOR_PERENNIAL,  # phlox_paniculata.md
    "Polygonaceae": CareStyleType.OUTDOOR_PERENNIAL,  # rule 3: rhubarb, hardy perennial vegetable
    # Rule 2. mediterranean 2 (clematis, helleborus) / outdoor_perennial 1 / custom
    # 1, but all four are hardy outdoor perennials and Clematis and Delphinium are
    # thirsty — a 10-day drench-and-drain interval is the wrong direction.
    "Ranunculaceae": CareStyleType.OUTDOOR_PERENNIAL,
    # Rule 2/3. Six of eight docs say `custom`; four of the eight seeded species
    # are the fruit trees FRUIT_TREE names ("Apple, pear, cherry, plum"). Rosa spp.
    # and the Rubus berries deserve their own styles (ROSE, BERRY_SHRUB) — a
    # family map cannot give them one.
    "Rosaceae": CareStyleType.FRUIT_TREE,
    "Saxifragaceae": CareStyleType.OUTDOOR_PERENNIAL,  # astilbe_chinensis.md
    # Rule 2. The doc says `mediterranean`; the one seeded species, Verbena x
    # hybrida, is a frost-tender balcony bedder — the use case
    # OUTDOOR_ANNUAL_ORNAMENTAL was written for ("Pansy, primrose, geranium,
    # lobelia").
    "Verbenaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
    # Rule 2. The doc says `mediterranean`, whose 36-month repotting interval would
    # put a repotting reminder on a grapevine in the ground; FRUIT_TREE caps it at
    # 60 and feeds once in spring, which is how an established vine is handled.
    "Vitaceae": CareStyleType.FRUIT_TREE,
    # ── Entries naming no seeded family ───────────────────────────────
    # Harmless: they cost one dict entry and serve a user-created or imported
    # species. The issue counted 11 of these; measured over every seed file it is
    # one — the other ten (Cactaceae, Crassulaceae, Marantaceae, Moraceae, Oleaceae,
    # Orchidaceae, Polypodiaceae, Primulaceae, Asphodelaceae, Balsaminaceae) are
    # seeded, just by a `plant_info_*.yaml` rather than by botanical_families.yaml.
    "Campanulaceae": CareStyleType.OUTDOOR_ANNUAL_ORNAMENTAL,
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
        return today_utc()

    def calculate_urgency(self, due_date: date | None) -> str:
        """Determine urgency level from due date."""
        if due_date is None:
            return "not_due"
        today = today_utc()
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
        winter_quarter_temp_violation: bool | None = None,
        season_phase: SeasonPhase | None = None,
        irrigation_demand_capped_mm: float | None = None,
    ) -> bool:
        """Check whether a reminder should be generated.

        ``season_phase`` is the REQ-047 SeasonState phase of the plant's site when
        one exists. It is the *primary* trigger for the winter-protection reminders:
        given a phase, they fire on the season transition (``pre_winter`` /
        ``pre_spring``) rather than on a fixed calendar month. ``None`` means the
        site has no SeasonState, so the month-based calendar fallback applies.

        ``irrigation_demand_capped_mm`` is the REQ-037 net irrigation demand (mm)
        materialised for the plant's outdoor/greenhouse site. When it is exactly
        ``0`` — rain has already covered the crop's demand — the watering reminder
        is suppressed. ``None`` (indoor sites, no ET data) leaves the interval-based
        logic untouched.
        """
        if month is None:
            month = today_utc().month

        # REQ-037 ET suppression: an outdoor/greenhouse plant whose net demand is
        # zero (rain covered it) needs no watering reminder today.
        if (
            reminder_type == ReminderType.WATERING
            and irrigation_demand_capped_mm is not None
            and irrigation_demand_capped_mm <= 0
        ):
            return False

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
            if not profile.dormancy_care_mode:
                return False
            # AC-22 (event-driven, REQ-047 §3.7.3) — once a caller has actually
            # compared the quarter's live temperature against winter_quarter_temp_
            # min/max, ``winter_quarter_temp_violation`` decides: fire only on a real
            # violation (heating failure → too cold; overheating → premature budding).
            if winter_quarter_temp_violation is not None:
                return winter_quarter_temp_violation
            # AC-13 fallback (periodic) — no violation signal computed yet: fire
            # periodically while the quarter merely *has* live data (sensor/HA).
            return winter_quarter_has_livedata

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
        *,
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

        Tier 1 became true in production with #1481 — until then no caller passed a
        guide and the ranking described a parameter nothing filled. It is now
        resolved with the family in ``resolve_care_inputs`` (the cultivar's
        ``watering_guide_override`` ahead of the species' own, the precedence
        ``WateringService`` already used), and
        ``tests/unit/domain/services/test_care_profile_watering_guide.py`` requires
        a production call site to exist, so this list cannot go back to being a
        claim about nothing.

        ``botanical_family`` is the family **NAME** (``"Cactaceae"``) — what
        :data:`FAMILY_CARE_MAP` is keyed by — never the ``_key`` of a
        ``botanical_families`` document. Handing it the key is a type error, and
        one this method used to answer with plausible tropical presets: every plant
        created since #1440 received the 7-day ``TROPICAL`` preset for good, because
        the profile is written once and read thereafter (#1489). A numeric value is
        therefore refused rather than silently missed.

        **Every parameter is keyword-only**, and that is a guard rather than a style
        choice: ``botanical_family`` is the second positional slot, so
        ``auto_generate_profile(name, species.family_key, key)`` would re-introduce
        #1489 in a spelling the AST guard (which reads keyword arguments) cannot see.
        Measured before the change: every caller in ``app/`` and ``tests/`` already
        used keywords, so the restriction costs nothing and closes the hole.

        ``species_name`` takes part in no decision here (measured 2026-09-17: the
        presets come from the family and the guide alone). It is kept because the
        applied v0048 backfill passes it, and removing a parameter a shipped
        migration names would be a bigger change than the dead argument is worth.
        """
        if botanical_family is not None and botanical_family.strip().isdigit():
            raise ValueError(
                "botanical_family must be the family NAME (e.g. 'Cactaceae'), not the "
                f"_key of a botanical_families document — got {botanical_family!r}. "
                "Resolve it through `resolve_care_inputs` (#1489)."
            )

        care_style = CareStyleType.TROPICAL  # default fallback

        if botanical_family and botanical_family in FAMILY_CARE_MAP:
            care_style = FAMILY_CARE_MAP[botanical_family]
        elif botanical_family:
            # A family the map does not cover is ordinary — the catalogue holds far
            # more families than the map does — but it is also exactly how #1489
            # looked from in here, so the fallback is stated instead of silent.
            logger.info(
                "care_profile_family_unmapped",
                botanical_family=botanical_family,
                plant_key=plant_key,
                care_style=care_style.value,
            )

        preset = dict(CARE_STYLE_PRESETS[care_style])

        # TIER 1 — the species/cultivar WateringGuide overrides the family preset's
        # watering fields (the comment said "Tier 2" and contradicted the docstring
        # three lines up; #1489 review, SCR-014). It overrides the *watering* fields
        # only: the care style and the fertilising/repotting/pest intervals stay the
        # family's.
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
        month = today_utc().month
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
