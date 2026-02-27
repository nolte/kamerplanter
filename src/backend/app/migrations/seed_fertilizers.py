"""Seed database with fertilizer products and cannabis nutrient plans."""

import structlog

from app.common.dependencies import get_fertilizer_repo, get_nutrient_plan_repo
from app.common.enums import (
    ApplicationMethod,
    Bioavailability,
    FertilizerType,
    PhaseName,
    PhEffect,
    SubstrateType,
)
from app.domain.models.fertilizer import Fertilizer
from app.domain.models.nutrient_plan import (
    FertilizerDosage,
    NutrientPlan,
    NutrientPlanPhaseEntry,
)

logger = structlog.get_logger()

# ── Product Catalog ───────────────────────────────────────────────────────────
# Sources — Advanced Nutrients:
#   https://www.advancednutrients.com/products/ph-perfect-sensi-grow-bloom/
#   https://greenlab.ge/en/product/advanced-nutrients-ph-perfect-sensi-grow-a/
#   https://greenlab.ge/en/product/advanced-nutrients-ph-perfect-sensi-grow-b/
#   https://www.advancednutrients.com/products/big-bud/
#   https://www.advancednutrients.com/products/b-52/
#   https://www.advancednutrients.com/products/voodoo-juice/
#   https://www.advancednutrients.com/de/products/ph-perfect-grow-micro-bloom/
# Sources — Third-Party Supplements:
#   spec/ref/products/hg-drip-clean.md
#   spec/ref/products/bn-free-flow.md

FERTILIZERS: list[Fertilizer] = [
    # ── Base Nutrients (GMB 3-Part) ──────────────────────────────────────
    Fertilizer(
        product_name="pH Perfect Grow",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BASE,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(1.0, 0.0, 4.0),
        ec_contribution_per_ml=0.10,
        mixing_priority=15,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes=(
            "3-Part-System: Stickstoff + Kalium. "
            "Nach Micro hinzufügen. 1-4 ml/L je nach Phase."
        ),
    ),
    Fertilizer(
        product_name="pH Perfect Micro",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BASE,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(2.0, 0.0, 0.0),
        ec_contribution_per_ml=0.15,
        mixing_priority=10,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes=(
            "3-Part-System: CalMag-Komponente. "
            "IMMER zuerst hinzufügen (vor Grow und Bloom). 1-4 ml/L je nach Phase."
        ),
    ),
    Fertilizer(
        product_name="pH Perfect Bloom",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BASE,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(1.0, 3.0, 4.0),
        ec_contribution_per_ml=0.10,
        mixing_priority=20,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes=(
            "3-Part-System: Phosphor + Kalium für Blüte. "
            "Nach Micro und Grow hinzufügen. 1-4 ml/L je nach Phase."
        ),
    ),
    # ── Base Nutrients (Sensi 2-Part, Grow Phase) ────────────────────────
    Fertilizer(
        product_name="pH Perfect Sensi Grow A",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BASE,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(3.0, 0.0, 0.0),
        ec_contribution_per_ml=0.15,
        mixing_priority=10,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes="CalMag-Komponente (3% Ca). Immer zuerst hinzufügen, vor Part B.",
    ),
    Fertilizer(
        product_name="pH Perfect Sensi Grow B",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BASE,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(1.0, 2.0, 6.0),
        ec_contribution_per_ml=0.15,
        mixing_priority=20,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes="PK-Komponente mit Schwefel (1.3% S). Nach Part A hinzufügen.",
    ),
    # ── Base Nutrients (Sensi 2-Part, Bloom Phase) ─────────────────────────
    Fertilizer(
        product_name="pH Perfect Sensi Bloom A",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BASE,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(3.0, 0.0, 0.0),
        ec_contribution_per_ml=0.15,
        mixing_priority=10,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes="CalMag-Komponente für Blüte. Immer zuerst hinzufügen.",
    ),
    Fertilizer(
        product_name="pH Perfect Sensi Bloom B",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BASE,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(2.0, 4.0, 8.0),
        ec_contribution_per_ml=0.20,
        mixing_priority=20,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes="Höherer PK-Anteil für Blütebildung. Nach Part A hinzufügen.",
    ),
    # ── Boosters ──────────────────────────────────────────────────────────
    Fertilizer(
        product_name="Big Bud",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BOOSTER,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(0.0, 1.0, 3.0),
        ec_contribution_per_ml=0.05,
        mixing_priority=30,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes="Bloom-Booster für größere, dichtere Blüten. Woche 2-4 der Blüte.",
    ),
    Fertilizer(
        product_name="Overdrive",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BOOSTER,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(1.0, 5.0, 4.0),
        ec_contribution_per_ml=0.10,
        mixing_priority=30,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes="Spätblüte-Booster. Letzte 3 Wochen vor dem Flush.",
    ),
    # ── Supplements ───────────────────────────────────────────────────────
    Fertilizer(
        product_name="B-52",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.SUPPLEMENT,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(2.0, 1.0, 4.0),
        ec_contribution_per_ml=0.05,
        mixing_priority=40,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes="B-Vitamin-Komplex + Kelp. Stärkt Photosynthese und Stressresistenz.",
    ),
    Fertilizer(
        product_name="Bud Candy",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.SUPPLEMENT,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(0.0, 0.0, 0.0),
        ec_contribution_per_ml=0.0,
        mixing_priority=40,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.IMMEDIATE,
        notes="Kohlenhydrat-Supplement mit Magnesium. Verbessert Aroma und Blütengewicht.",
    ),
    Fertilizer(
        product_name="Nirvana",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.ORGANIC,
        is_organic=True,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(0.0, 0.0, 1.0),
        ec_contribution_per_ml=0.01,
        mixing_priority=40,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.SLOW_RELEASE,
        notes="Organischer Blüte-Supplement. Enthält Guano, Alfalfa und Humate.",
    ),
    Fertilizer(
        product_name="Rhino Skin",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.SUPPLEMENT,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(0.0, 0.0, 0.0),
        ec_contribution_per_ml=0.0,
        mixing_priority=5,
        ph_effect=PhEffect.ALKALINE,
        bioavailability=Bioavailability.IMMEDIATE,
        notes="Kaliumsilikat — stärkt Zellwände. VOR allen anderen Düngern hinzufügen!",
    ),
    # ── Biologicals ───────────────────────────────────────────────────────
    Fertilizer(
        product_name="Voodoo Juice",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BIOLOGICAL,
        is_organic=True,
        tank_safe=False,
        recommended_application=ApplicationMethod.DRENCH,
        npk_ratio=(0.0, 0.0, 0.0),
        ec_contribution_per_ml=0.0,
        mixing_priority=50,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.MICROBIAL_DEPENDENT,
        notes="4 Bacillus-Stämme für Wurzelmasse. Woche 1-2 von Wachstum und Blüte.",
    ),
    Fertilizer(
        product_name="Piranha",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BIOLOGICAL,
        is_organic=True,
        tank_safe=False,
        recommended_application=ApplicationMethod.DRENCH,
        npk_ratio=(0.0, 0.0, 0.0),
        ec_contribution_per_ml=0.0,
        mixing_priority=50,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.MICROBIAL_DEPENDENT,
        notes="Mykorrhiza-Pilze für Nährstoffaufnahme. Woche 1-2.",
    ),
    Fertilizer(
        product_name="Tarantula",
        brand="Advanced Nutrients",
        fertilizer_type=FertilizerType.BIOLOGICAL,
        is_organic=True,
        tank_safe=False,
        recommended_application=ApplicationMethod.DRENCH,
        npk_ratio=(0.0, 0.0, 0.0),
        ec_contribution_per_ml=0.0,
        mixing_priority=50,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.MICROBIAL_DEPENDENT,
        notes="10 Mio. CFU/g Bacillus + Streptomyces. Woche 1-2.",
    ),
    # ── Third-Party Supplements ──────────────────────────────────────────
    Fertilizer(
        product_name="Drip Clean",
        brand="House & Garden",
        fertilizer_type=FertilizerType.SUPPLEMENT,
        is_organic=False,
        tank_safe=True,
        recommended_application=ApplicationMethod.FERTIGATION,
        npk_ratio=(0.0, 18.0, 6.0),
        ec_contribution_per_ml=0.5,
        mixing_priority=8,
        ph_effect=PhEffect.ACIDIC,
        bioavailability=Bioavailability.IMMEDIATE,
        shelf_life_days=730,
        storage_temp_min=5.0,
        storage_temp_max=25.0,
        notes=(
            "Mineralischer Systemreiniger (P₂O₅ 18%, K₂O 6%). Löst Salzablagerungen "
            "in Leitungen und Substrat. 0.1 ml/L bei jeder Bewässerung. "
            "IMMER vor den Basisdüngern zugeben."
        ),
    ),
    Fertilizer(
        product_name="Free Flow",
        brand="Bio Nova",
        fertilizer_type=FertilizerType.BIOLOGICAL,
        is_organic=True,
        tank_safe=False,
        recommended_application=ApplicationMethod.DRENCH,
        npk_ratio=(0.0, 0.0, 0.0),
        ec_contribution_per_ml=0.0,
        mixing_priority=50,
        ph_effect=PhEffect.NEUTRAL,
        bioavailability=Bioavailability.MICROBIAL_DEPENDENT,
        shelf_life_days=365,
        storage_temp_min=5.0,
        storage_temp_max=25.0,
        notes=(
            "Organisches Enzympräparat (Cellulasen, Proteasen, Lipasen). "
            "Baut abgestorbene Wurzelmasse und organische Rückstände ab. "
            "0.3-0.5 ml/L per Gießkanne, nicht im Tank (Biofilm-Gefahr)."
        ),
    ),
]

# ── Nutrient Plan: Advanced Nutrients pH Perfect Sensi — Cannabis ─────────────
# Based on: https://www.advancednutrients.com/feeding/
#           https://www.growbarato.net/blog/en/advanced-nutrients-feeding-chart/

PLAN = NutrientPlan(
    name="Advanced Nutrients pH Perfect Sensi — Cannabis",
    description=(
        "Vollständiges Düngeprogramm für Cannabis mit der pH Perfect Sensi-Serie "
        "von Advanced Nutrients. Enthält Basis A+B, Booster (Big Bud, Overdrive), "
        "Supplements (B-52, Bud Candy, Nirvana, Rhino Skin) und Biologicals "
        "(Voodoo Juice, Piranha, Tarantula). Ergänzt durch H&G Drip Clean "
        "(Systemreiniger) und Bio Nova Free Flow (Enzympräparat). "
        "Für Coco/Hydro optimiert."
    ),
    recommended_substrate_type=SubstrateType.COCO,
    author="Advanced Nutrients",
    is_template=True,
    version="2025.1",
    tags=["advanced-nutrients", "ph-perfect", "sensi", "cannabis", "coco", "hydro"],
)


def _build_phase_entries(
    fert_keys: dict[str, str],
) -> list[tuple[NutrientPlanPhaseEntry, list[FertilizerDosage]]]:
    """Build phase entries with fertilizer dosages.

    Returns (entry, dosages) tuples. Dosages reference fertilizer keys
    obtained after creating the Fertilizer records.
    """
    grow_a = fert_keys["pH Perfect Sensi Grow A"]
    grow_b = fert_keys["pH Perfect Sensi Grow B"]
    bloom_a = fert_keys["pH Perfect Sensi Bloom A"]
    bloom_b = fert_keys["pH Perfect Sensi Bloom B"]
    big_bud = fert_keys["Big Bud"]
    overdrive = fert_keys["Overdrive"]
    b52 = fert_keys["B-52"]
    bud_candy = fert_keys["Bud Candy"]
    nirvana = fert_keys["Nirvana"]
    rhino = fert_keys["Rhino Skin"]
    voodoo = fert_keys["Voodoo Juice"]
    piranha = fert_keys["Piranha"]
    tarantula = fert_keys["Tarantula"]
    drip_clean = fert_keys["Drip Clean"]
    free_flow = fert_keys["Free Flow"]

    return [
        # ── 1. Keimung (Week 0–1) ────────────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",  # filled by caller
                phase_name=PhaseName.GERMINATION,
                sequence_order=1,
                week_start=1,
                week_end=2,
                npk_ratio=(0.0, 0.0, 0.0),
                target_ec_ms=0.2,
                target_ph=6.2,
                feeding_frequency_per_week=1,
                notes="Nur Wasser. Samen keimen in feuchtem Medium, kein Dünger.",
            ),
            [],
        ),
        # ── 2. Sämling (Week 1–3) ────────────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.SEEDLING,
                sequence_order=2,
                week_start=2,
                week_end=4,
                npk_ratio=(2.0, 1.0, 3.0),
                target_ec_ms=0.6,
                target_ph=5.9,
                feeding_frequency_per_week=2,
                volume_per_feeding_liters=0.3,
                notes=(
                    "¼ Dosis Sensi Grow. Voodoo Juice + Tarantula + Piranha "
                    "für Wurzelaufbau. B-52 gegen Umpflanz-Stress."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=rhino, ml_per_liter=0.5),
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(fertilizer_key=grow_a, ml_per_liter=1.0),
                FertilizerDosage(fertilizer_key=grow_b, ml_per_liter=1.0),
                FertilizerDosage(fertilizer_key=b52, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=voodoo, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=piranha, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=tarantula, ml_per_liter=2.0),
                FertilizerDosage(
                    fertilizer_key=free_flow, ml_per_liter=0.5, optional=True,
                ),
            ],
        ),
        # ── 3. Vegetativ (Week 3–7) ──────────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.VEGETATIVE,
                sequence_order=3,
                week_start=4,
                week_end=8,
                npk_ratio=(4.0, 2.0, 6.0),
                target_ec_ms=1.4,
                target_ph=5.9,
                feeding_frequency_per_week=3,
                volume_per_feeding_liters=0.5,
                notes=(
                    "Volle Dosis Sensi Grow A+B. Rhino Skin für starke Stängel. "
                    "B-52 durchgehend. Voodoo Juice in Woche 3-4."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=rhino, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(fertilizer_key=grow_a, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=grow_b, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=b52, ml_per_liter=2.0),
                FertilizerDosage(
                    fertilizer_key=voodoo, ml_per_liter=2.0, optional=True,
                ),
                FertilizerDosage(fertilizer_key=free_flow, ml_per_liter=0.5),
            ],
        ),
        # ── 4. Blüte — Früh (Week 7–10) ──────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.FLOWERING,
                sequence_order=4,
                week_start=8,
                week_end=11,
                npk_ratio=(5.0, 4.0, 8.0),
                target_ec_ms=1.6,
                target_ph=5.9,
                calcium_ppm=200.0,
                magnesium_ppm=60.0,
                feeding_frequency_per_week=3,
                volume_per_feeding_liters=0.8,
                notes=(
                    "Umstellung auf Sensi Bloom A+B. Big Bud für Blütenbildung. "
                    "Bud Candy + Nirvana für Aroma. Voodoo Juice in Woche 7-8."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=rhino, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(fertilizer_key=bloom_a, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=bloom_b, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=big_bud, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=b52, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=bud_candy, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=nirvana, ml_per_liter=2.0),
                FertilizerDosage(
                    fertilizer_key=voodoo, ml_per_liter=2.0, optional=True,
                ),
                FertilizerDosage(fertilizer_key=free_flow, ml_per_liter=0.5),
            ],
        ),
        # ── 5. Blüte — Spät (Week 10–14) ─────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.FLOWERING,
                sequence_order=5,
                week_start=11,
                week_end=15,
                npk_ratio=(6.0, 9.0, 12.0),
                target_ec_ms=1.8,
                target_ph=5.9,
                calcium_ppm=200.0,
                magnesium_ppm=60.0,
                feeding_frequency_per_week=3,
                volume_per_feeding_liters=1.0,
                notes=(
                    "Overdrive ersetzt Big Bud für maximale Blütendichte. "
                    "Sensi Bloom A+B volle Dosis. Bud Candy + Nirvana weiter."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=rhino, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(fertilizer_key=bloom_a, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=bloom_b, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=overdrive, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=b52, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=bud_candy, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=nirvana, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=free_flow, ml_per_liter=0.5),
            ],
        ),
        # ── 6. Ernte / Flush (Week 14–16) ────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.HARVEST,
                sequence_order=6,
                week_start=15,
                week_end=17,
                npk_ratio=(0.0, 0.0, 0.0),
                target_ec_ms=0.0,
                target_ph=6.0,
                feeding_frequency_per_week=7,
                volume_per_feeding_liters=1.0,
                notes=(
                    "10-14 Tage Flush mit reinem Wasser (Coco). "
                    "Drip Clean löst restliche Salzablagerungen. "
                    "Free Flow optional für Wurzelabbau. "
                    "Ziel: EC im Ablauf < 0.3 mS."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(
                    fertilizer_key=free_flow, ml_per_liter=0.3, optional=True,
                ),
            ],
        ),
    ]


# ── Nutrient Plan: Advanced Nutrients pH Perfect GMB — Cannabis ────────────────
# Based on: https://www.advancednutrients.com/de/products/ph-perfect-grow-micro-bloom/
#           https://www.advancednutrients.com/feeding/

GMB_PLAN = NutrientPlan(
    name="Advanced Nutrients pH Perfect GMB — Cannabis",
    description=(
        "Vollständiges Düngeprogramm für Cannabis mit der pH Perfect "
        "Grow-Micro-Bloom 3-Part-Serie von Advanced Nutrients. "
        "Enthält Basis Micro+Grow+Bloom, Booster (Big Bud, Overdrive), "
        "Supplements (B-52, Bud Candy, Nirvana, Rhino Skin) und Biologicals "
        "(Voodoo Juice, Piranha, Tarantula). Ergänzt durch H&G Drip Clean "
        "(Systemreiniger) und Bio Nova Free Flow (Enzympräparat). "
        "Für Coco/Hydro optimiert."
    ),
    recommended_substrate_type=SubstrateType.COCO,
    author="Advanced Nutrients",
    is_template=True,
    version="2025.1",
    tags=["advanced-nutrients", "ph-perfect", "gmb", "3-part", "cannabis", "coco", "hydro"],
)


def _build_gmb_phase_entries(
    fert_keys: dict[str, str],
) -> list[tuple[NutrientPlanPhaseEntry, list[FertilizerDosage]]]:
    """Build phase entries for the GMB 3-part plan.

    Same supplements/boosters/biologicals as the Sensi plan,
    but with Micro → Grow → Bloom as base nutrients.
    """
    micro = fert_keys["pH Perfect Micro"]
    grow = fert_keys["pH Perfect Grow"]
    bloom = fert_keys["pH Perfect Bloom"]
    big_bud = fert_keys["Big Bud"]
    overdrive = fert_keys["Overdrive"]
    b52 = fert_keys["B-52"]
    bud_candy = fert_keys["Bud Candy"]
    nirvana = fert_keys["Nirvana"]
    rhino = fert_keys["Rhino Skin"]
    voodoo = fert_keys["Voodoo Juice"]
    piranha = fert_keys["Piranha"]
    tarantula = fert_keys["Tarantula"]
    drip_clean = fert_keys["Drip Clean"]
    free_flow = fert_keys["Free Flow"]

    return [
        # ── 1. Keimung (Week 1–2) ──────────────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.GERMINATION,
                sequence_order=1,
                week_start=1,
                week_end=2,
                npk_ratio=(0.0, 0.0, 0.0),
                target_ec_ms=0.2,
                target_ph=6.2,
                feeding_frequency_per_week=1,
                notes="Nur Wasser. Samen keimen in feuchtem Medium, kein Dünger.",
            ),
            [],
        ),
        # ── 2. Sämling (Week 2–4) ──────────────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.SEEDLING,
                sequence_order=2,
                week_start=2,
                week_end=4,
                npk_ratio=(1.3, 1.0, 2.7),
                target_ec_ms=0.6,
                target_ph=5.9,
                feeding_frequency_per_week=2,
                volume_per_feeding_liters=0.3,
                notes=(
                    "¼ Dosis GMB (je 1 ml/L). Micro zuerst, dann Grow, dann Bloom. "
                    "Voodoo Juice + Tarantula + Piranha für Wurzelaufbau. "
                    "B-52 gegen Umpflanz-Stress."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=rhino, ml_per_liter=0.5),
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(fertilizer_key=micro, ml_per_liter=1.0),
                FertilizerDosage(fertilizer_key=grow, ml_per_liter=1.0),
                FertilizerDosage(fertilizer_key=bloom, ml_per_liter=1.0),
                FertilizerDosage(fertilizer_key=b52, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=voodoo, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=piranha, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=tarantula, ml_per_liter=2.0),
                FertilizerDosage(
                    fertilizer_key=free_flow, ml_per_liter=0.5, optional=True,
                ),
            ],
        ),
        # ── 3. Vegetativ (Week 4–8) ────────────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.VEGETATIVE,
                sequence_order=3,
                week_start=4,
                week_end=8,
                npk_ratio=(4.0, 3.0, 8.0),
                target_ec_ms=1.4,
                target_ph=5.9,
                feeding_frequency_per_week=3,
                volume_per_feeding_liters=0.5,
                notes=(
                    "Volle Dosis GMB (je 4 ml/L). Micro → Grow → Bloom. "
                    "Rhino Skin für starke Stängel. B-52 durchgehend."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=rhino, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(fertilizer_key=micro, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=grow, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=bloom, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=b52, ml_per_liter=2.0),
                FertilizerDosage(
                    fertilizer_key=voodoo, ml_per_liter=2.0, optional=True,
                ),
                FertilizerDosage(fertilizer_key=free_flow, ml_per_liter=0.5),
            ],
        ),
        # ── 4. Blüte — Früh (Week 8–11) ────────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.FLOWERING,
                sequence_order=4,
                week_start=8,
                week_end=11,
                npk_ratio=(4.0, 3.0, 8.0),
                target_ec_ms=1.6,
                target_ph=5.9,
                calcium_ppm=200.0,
                magnesium_ppm=60.0,
                feeding_frequency_per_week=3,
                volume_per_feeding_liters=0.8,
                notes=(
                    "GMB volle Dosis (je 4 ml/L). Alle drei Teile gleich dosiert. "
                    "Big Bud für Blütenbildung. Bud Candy + Nirvana für Aroma."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=rhino, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(fertilizer_key=micro, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=grow, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=bloom, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=big_bud, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=b52, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=bud_candy, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=nirvana, ml_per_liter=2.0),
                FertilizerDosage(
                    fertilizer_key=voodoo, ml_per_liter=2.0, optional=True,
                ),
                FertilizerDosage(fertilizer_key=free_flow, ml_per_liter=0.5),
            ],
        ),
        # ── 5. Blüte — Spät (Week 11–15) ───────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.FLOWERING,
                sequence_order=5,
                week_start=11,
                week_end=15,
                npk_ratio=(4.0, 3.0, 8.0),
                target_ec_ms=1.8,
                target_ph=5.9,
                calcium_ppm=200.0,
                magnesium_ppm=60.0,
                feeding_frequency_per_week=3,
                volume_per_feeding_liters=1.0,
                notes=(
                    "Overdrive ersetzt Big Bud für maximale Blütendichte. "
                    "GMB volle Dosis (je 4 ml/L). Bud Candy + Nirvana weiter."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=rhino, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(fertilizer_key=micro, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=grow, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=bloom, ml_per_liter=4.0),
                FertilizerDosage(fertilizer_key=overdrive, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=b52, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=bud_candy, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=nirvana, ml_per_liter=2.0),
                FertilizerDosage(fertilizer_key=free_flow, ml_per_liter=0.5),
            ],
        ),
        # ── 6. Ernte / Flush (Week 15–17) ──────────────────────────────────
        (
            NutrientPlanPhaseEntry(
                plan_key="",
                phase_name=PhaseName.HARVEST,
                sequence_order=6,
                week_start=15,
                week_end=17,
                npk_ratio=(0.0, 0.0, 0.0),
                target_ec_ms=0.0,
                target_ph=6.0,
                feeding_frequency_per_week=7,
                volume_per_feeding_liters=1.0,
                notes=(
                    "10-14 Tage Flush mit reinem Wasser (Coco). "
                    "Drip Clean löst restliche Salzablagerungen. "
                    "Free Flow optional für Wurzelabbau. "
                    "Ziel: EC im Ablauf < 0.3 mS."
                ),
            ),
            [
                FertilizerDosage(fertilizer_key=drip_clean, ml_per_liter=0.1),
                FertilizerDosage(
                    fertilizer_key=free_flow, ml_per_liter=0.3, optional=True,
                ),
            ],
        ),
    ]


def run_seed_fertilizers() -> None:
    """Create fertilizer products and nutrient plans."""
    fert_repo = get_fertilizer_repo()
    plan_repo = get_nutrient_plan_repo()

    # ── Create fertilizers ────────────────────────────────────────────────
    fert_keys: dict[str, str] = {}
    for fert in FERTILIZERS:
        existing, _ = fert_repo.get_all(offset=0, limit=1000)
        found = next(
            (f for f in existing if f.product_name == fert.product_name and f.brand == fert.brand),
            None,
        )
        if found:
            fert_keys[fert.product_name] = found.key or ""
            logger.info("fertilizer_exists", name=fert.product_name)
        else:
            created = fert_repo.create(fert)
            fert_keys[fert.product_name] = created.key or ""
            logger.info("fertilizer_created", name=fert.product_name)

    # ── Create nutrient plans ─────────────────────────────────────────────
    existing_plans, _ = plan_repo.get_all(offset=0, limit=100)
    existing_names = {p.name for p in existing_plans}

    plans = [
        (PLAN, _build_phase_entries),
        (GMB_PLAN, _build_gmb_phase_entries),
    ]
    for plan, builder in plans:
        if plan.name in existing_names:
            logger.info("plan_exists", name=plan.name)
            continue

        created_plan = plan_repo.create(plan)
        plan_key = created_plan.key or ""
        logger.info("plan_created", name=plan.name, key=plan_key)

        entries = builder(fert_keys)
        for entry, dosages in entries:
            entry.plan_key = plan_key
            entry.fertilizer_dosages = dosages
            created_entry = plan_repo.create_phase_entry(entry)
            logger.info(
                "phase_entry_created",
                plan=plan.name,
                phase=entry.phase_name,
                week=f"{entry.week_start}-{entry.week_end}",
                dosages=len(dosages),
                key=created_entry.key,
            )

    logger.info("seed_fertilizers_complete", fertilizers=len(fert_keys), plans=len(plans))


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed_fertilizers()
