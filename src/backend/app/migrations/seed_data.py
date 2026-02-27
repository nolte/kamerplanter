"""Seed database with botanical families, common species, cultivars, and default profiles."""

import structlog

from app.common.dependencies import get_family_repo, get_graph_repo, get_lifecycle_repo, get_species_repo
from app.common.enums import (
    CycleType,
    FrostTolerance,
    GrowthHabit,
    NutrientDemand,
    PhotoperiodType,
    PollinationType,
    RootDepth,
    RootType,
    StressTolerance,
)
from app.domain.engines.resource_profile_generator import ResourceProfileGenerator
from app.domain.models.botanical_family import BotanicalFamily, PhRange
from app.domain.models.lifecycle import GrowthPhase, LifecycleConfig
from app.domain.models.species import Cultivar, Species

logger = structlog.get_logger()

FAMILIES = [
    BotanicalFamily(
        name="Solanaceae", common_name_de="Nachtschattengewächse",
        common_name_en="Nightshade family",
        order="Solanales", typical_nutrient_demand=NutrientDemand.HEAVY,
        frost_tolerance=FrostTolerance.SENSITIVE,
        typical_root_depth=RootDepth.MEDIUM,
        typical_growth_forms=[GrowthHabit.HERB, GrowthHabit.SHRUB],
        common_pests=["aphids", "whitefly", "hornworm"],
        common_diseases=["Kraut- und Braunfäule", "Fusarium", "Verticillium"],
        pollination_type=[PollinationType.INSECT, PollinationType.SELF],
        soil_ph_preference=PhRange(min_ph=5.5, max_ph=7.0),
        description="Große Familie mit vielen Nutzpflanzen wie Tomate, Paprika, Kartoffel und Aubergine.",
        rotation_category="fruit",
    ),
    BotanicalFamily(
        name="Cannabaceae", common_name_de="Hanfgewächse",
        common_name_en="Hemp family",
        order="Rosales", typical_nutrient_demand=NutrientDemand.HEAVY,
        frost_tolerance=FrostTolerance.SENSITIVE,
        typical_root_depth=RootDepth.DEEP,
        typical_growth_forms=[GrowthHabit.HERB, GrowthHabit.VINE],
        common_pests=["spider_mites", "fungus_gnats", "thrips"],
        common_diseases=["Botrytis", "Mehltau", "Fusarium"],
        pollination_type=[PollinationType.WIND],
        soil_ph_preference=PhRange(min_ph=6.0, max_ph=7.0),
        description="Enthält Cannabis und Hopfen. Meist windbestäubt, hoher Nährstoffbedarf.",
        rotation_category="fiber",
    ),
    BotanicalFamily(
        name="Lamiaceae", common_name_de="Lippenblütler",
        common_name_en="Mint family",
        order="Lamiales", typical_nutrient_demand=NutrientDemand.LIGHT,
        frost_tolerance=FrostTolerance.MODERATE,
        typical_root_depth=RootDepth.SHALLOW,
        typical_growth_forms=[GrowthHabit.HERB, GrowthHabit.SHRUB],
        common_pests=["aphids", "spider_mites"],
        common_diseases=["Mehltau", "Rost"],
        pollination_type=[PollinationType.INSECT],
        soil_ph_preference=PhRange(min_ph=6.0, max_ph=7.5),
        description="Aromatische Kräuter wie Basilikum, Minze, Thymian und Rosmarin. Ätherische Öle.",
        rotation_category="herb",
    ),
    BotanicalFamily(
        name="Apiaceae", common_name_de="Doldenblütler",
        common_name_en="Carrot family",
        order="Apiales", typical_nutrient_demand=NutrientDemand.MEDIUM,
        frost_tolerance=FrostTolerance.MODERATE,
        typical_root_depth=RootDepth.DEEP,
        typical_growth_forms=[GrowthHabit.HERB],
        common_pests=["carrot_fly", "aphids"],
        common_diseases=["Mehltau", "Alternaria"],
        pollination_type=[PollinationType.INSECT],
        soil_ph_preference=PhRange(min_ph=6.0, max_ph=7.0),
        description="Doldenblütler mit Karotten, Fenchel, Dill, Petersilie und Sellerie.",
        rotation_category="root",
    ),
    BotanicalFamily(
        name="Brassicaceae", common_name_de="Kreuzblütler",
        common_name_en="Cabbage family",
        order="Brassicales", typical_nutrient_demand=NutrientDemand.HEAVY,
        frost_tolerance=FrostTolerance.HARDY,
        typical_root_depth=RootDepth.MEDIUM,
        typical_growth_forms=[GrowthHabit.HERB],
        common_pests=["cabbage_white", "flea_beetle", "clubroot"],
        common_diseases=["Kohlhernie", "Mehltau", "Schwarzbeinigkeit"],
        pollination_type=[PollinationType.INSECT, PollinationType.SELF],
        soil_ph_preference=PhRange(min_ph=6.0, max_ph=7.5),
        description="Kreuzblütler mit Kohl, Brokkoli, Rettich und Rucola. Biofumigations-Potential.",
        rotation_category="brassica",
    ),
    BotanicalFamily(
        name="Fabaceae", common_name_de="Hülsenfrüchtler",
        common_name_en="Legume family",
        order="Fabales", typical_nutrient_demand=NutrientDemand.LIGHT,
        nitrogen_fixing=True,
        frost_tolerance=FrostTolerance.MODERATE,
        typical_root_depth=RootDepth.DEEP,
        typical_growth_forms=[GrowthHabit.HERB, GrowthHabit.VINE],
        common_pests=["aphids", "bean_beetle"],
        common_diseases=["Rost", "Fusarium", "Botrytis"],
        pollination_type=[PollinationType.INSECT, PollinationType.SELF],
        soil_ph_preference=PhRange(min_ph=6.0, max_ph=7.5),
        description="Stickstofffixierende Hülsenfrüchtler. Wichtige Gründünger und Vorfrüchte.",
        rotation_category="legume",
    ),
    BotanicalFamily(
        name="Cucurbitaceae", common_name_de="Kürbisgewächse",
        common_name_en="Gourd family",
        order="Cucurbitales", typical_nutrient_demand=NutrientDemand.HEAVY,
        frost_tolerance=FrostTolerance.SENSITIVE,
        typical_root_depth=RootDepth.MEDIUM,
        typical_growth_forms=[GrowthHabit.VINE],
        common_pests=["powdery_mildew", "cucumber_beetle", "squash_bug"],
        common_diseases=["Mehltau", "Falscher Mehltau", "Fusarium"],
        pollination_type=[PollinationType.INSECT],
        soil_ph_preference=PhRange(min_ph=6.0, max_ph=7.0),
        description="Kürbisgewächse wie Gurke, Zucchini, Kürbis und Melone. Insektenbestäubt.",
        rotation_category="cucurbit",
    ),
    BotanicalFamily(
        name="Asteraceae", common_name_de="Korbblütler",
        common_name_en="Daisy family",
        order="Asterales", typical_nutrient_demand=NutrientDemand.MEDIUM,
        frost_tolerance=FrostTolerance.MODERATE,
        typical_root_depth=RootDepth.SHALLOW,
        typical_growth_forms=[GrowthHabit.HERB],
        common_pests=["aphids", "slugs"],
        common_diseases=["Mehltau", "Grauschimmel", "Rost"],
        pollination_type=[PollinationType.INSECT, PollinationType.SELF],
        soil_ph_preference=PhRange(min_ph=6.0, max_ph=7.0),
        description="Größte Pflanzenfamilie. Salat, Sonnenblume, Tagetes und Kamille.",
        rotation_category="composite",
    ),
    BotanicalFamily(
        name="Poaceae", common_name_de="Süßgräser",
        common_name_en="Grass family",
        order="Poales", typical_nutrient_demand=NutrientDemand.MEDIUM,
        frost_tolerance=FrostTolerance.HARDY,
        typical_root_depth=RootDepth.DEEP,
        typical_growth_forms=[GrowthHabit.HERB],
        common_pests=["aphids", "rust", "stem_borer"],
        common_diseases=["Rost", "Fusarium", "Brandkrankheiten"],
        pollination_type=[PollinationType.WIND],
        soil_ph_preference=PhRange(min_ph=5.5, max_ph=7.0),
        description="Gräser und Getreide wie Mais, Weizen und Reis. Windbestäubt, tiefwurzelnd.",
        rotation_category="grain",
    ),
]

# Rotation edges: (from_family, to_family, wait_years, benefit_score, benefit_reason)
ROTATION_EDGES = [
    ("Fabaceae", "Solanaceae", 2, 0.95, "nitrogen_fixation"),
    ("Fabaceae", "Brassicaceae", 2, 0.90, "nitrogen_fixation"),
    ("Fabaceae", "Cucurbitaceae", 2, 0.90, "nitrogen_fixation"),
    ("Fabaceae", "Cannabaceae", 2, 0.90, "nitrogen_fixation"),
    ("Brassicaceae", "Fabaceae", 2, 0.85, "soil_structure"),
    ("Apiaceae", "Brassicaceae", 2, 0.80, "pest_break"),
    ("Solanaceae", "Fabaceae", 3, 0.85, "nitrogen_fixation"),
    ("Cucurbitaceae", "Fabaceae", 3, 0.85, "nitrogen_fixation"),
    ("Cannabaceae", "Fabaceae", 3, 0.85, "nitrogen_fixation"),
    ("Asteraceae", "Solanaceae", 2, 0.75, "pest_break"),
    ("Lamiaceae", "Solanaceae", 2, 0.70, "pest_break"),
    ("Poaceae", "Brassicaceae", 2, 0.80, "soil_structure"),
    ("Brassicaceae", "Poaceae", 2, 0.75, "biofumigation"),
    ("Apiaceae", "Cucurbitaceae", 2, 0.70, "pest_break"),
    ("Cucurbitaceae", "Poaceae", 2, 0.75, "soil_structure"),
    ("Asteraceae", "Cucurbitaceae", 2, 0.70, "pest_break"),
]

SPECIES = [
    # ── Solanaceae (6) ─────────────────────────────────────────────────
    Species(
        scientific_name="Solanum lycopersicum", common_names=["Tomato", "Tomate"],
        genus="Solanum", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=10.0,
        hardiness_zones=["9a", "10a", "11a"], native_habitat="South America", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Capsicum annuum", common_names=["Pepper", "Paprika", "Chili"],
        genus="Capsicum", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=12.0,
        hardiness_zones=["9a", "10a", "11a"], native_habitat="Central America", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Solanum melongena", common_names=["Eggplant", "Aubergine"],
        genus="Solanum", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=12.0,
        hardiness_zones=["9a", "10a"], native_habitat="South Asia", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Solanum tuberosum", common_names=["Potato", "Kartoffel"],
        genus="Solanum", growth_habit=GrowthHabit.HERB, root_type=RootType.TUBEROUS, base_temp=7.0,
        hardiness_zones=["3a", "10a"], native_habitat="South America", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Physalis peruviana", common_names=["Cape Gooseberry", "Physalis", "Andenbeere"],
        genus="Physalis", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=10.0,
        hardiness_zones=["8a", "11a"], native_habitat="South America", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Nicotiana tabacum", common_names=["Tobacco", "Tabak"],
        genus="Nicotiana", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=13.0,
        hardiness_zones=["8a", "11a"], native_habitat="Americas", allelopathy_score=0.3,
    ),
    # ── Cannabaceae (2) ────────────────────────────────────────────────
    Species(
        scientific_name="Cannabis sativa", common_names=["Hemp", "Cannabis", "Hanf"],
        genus="Cannabis", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=12.0,
        hardiness_zones=["6a", "10a"], native_habitat="Central Asia", allelopathy_score=0.2,
    ),
    Species(
        scientific_name="Humulus lupulus", common_names=["Hops", "Hopfen"],
        genus="Humulus", growth_habit=GrowthHabit.VINE, root_type=RootType.FIBROUS, base_temp=6.0,
        hardiness_zones=["3a", "8a"], native_habitat="Europe", allelopathy_score=0.1,
    ),
    # ── Lamiaceae (6) ──────────────────────────────────────────────────
    Species(
        scientific_name="Ocimum basilicum", common_names=["Basil", "Basilikum"],
        genus="Ocimum", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=10.0,
        hardiness_zones=["10a", "11a"], native_habitat="South Asia", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Mentha piperita", common_names=["Peppermint", "Pfefferminze"],
        genus="Mentha", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=5.0,
        hardiness_zones=["3a", "9a"], native_habitat="Europe", allelopathy_score=0.3,
    ),
    Species(
        scientific_name="Thymus vulgaris", common_names=["Thyme", "Thymian"],
        genus="Thymus", growth_habit=GrowthHabit.SHRUB, root_type=RootType.FIBROUS, base_temp=5.0,
        hardiness_zones=["5a", "9a"], native_habitat="Mediterranean", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Salvia rosmarinus", common_names=["Rosemary", "Rosmarin"],
        genus="Salvia", growth_habit=GrowthHabit.SHRUB, root_type=RootType.TAPROOT, base_temp=5.0,
        hardiness_zones=["7a", "10a"], native_habitat="Mediterranean", allelopathy_score=0.2,
    ),
    Species(
        scientific_name="Salvia officinalis", common_names=["Sage", "Salbei"],
        genus="Salvia", growth_habit=GrowthHabit.SHRUB, root_type=RootType.TAPROOT, base_temp=5.0,
        hardiness_zones=["4a", "9a"], native_habitat="Mediterranean", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Lavandula angustifolia", common_names=["Lavender", "Lavendel"],
        genus="Lavandula", growth_habit=GrowthHabit.SHRUB, root_type=RootType.TAPROOT, base_temp=5.0,
        hardiness_zones=["5a", "9a"], native_habitat="Mediterranean", allelopathy_score=0.2,
    ),
    # ── Apiaceae (6) ───────────────────────────────────────────────────
    Species(
        scientific_name="Daucus carota", common_names=["Carrot", "Karotte", "Möhre"],
        genus="Daucus", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=4.0,
        hardiness_zones=["3a", "10a"], native_habitat="Europe", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Foeniculum vulgare", common_names=["Fennel", "Fenchel"],
        genus="Foeniculum", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=8.0,
        hardiness_zones=["6a", "10a"], native_habitat="Mediterranean", allelopathy_score=0.5,
    ),
    Species(
        scientific_name="Anethum graveolens", common_names=["Dill"],
        genus="Anethum", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=7.0,
        hardiness_zones=["3a", "9a"], native_habitat="Mediterranean", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Coriandrum sativum", common_names=["Coriander", "Koriander"],
        genus="Coriandrum", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=7.0,
        hardiness_zones=["3a", "10a"], native_habitat="Mediterranean", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Apium graveolens", common_names=["Celery", "Sellerie"],
        genus="Apium", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=7.0,
        hardiness_zones=["2a", "10a"], native_habitat="Mediterranean", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Petroselinum crispum", common_names=["Parsley", "Petersilie"],
        genus="Petroselinum", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=5.0,
        hardiness_zones=["5a", "9a"], native_habitat="Mediterranean", allelopathy_score=0.0,
    ),
    # ── Brassicaceae (6) ───────────────────────────────────────────────
    Species(
        scientific_name="Brassica oleracea var. italica", common_names=["Broccoli", "Brokkoli"],
        genus="Brassica", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=5.0,
        hardiness_zones=["3a", "10a"], native_habitat="Mediterranean", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Brassica oleracea var. botrytis", common_names=["Cauliflower", "Blumenkohl"],
        genus="Brassica", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=5.0,
        hardiness_zones=["3a", "10a"], native_habitat="Mediterranean", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Brassica oleracea var. gongylodes", common_names=["Kohlrabi"],
        genus="Brassica", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=5.0,
        hardiness_zones=["3a", "10a"], native_habitat="Europe", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Raphanus sativus", common_names=["Radish", "Rettich", "Radieschen"],
        genus="Raphanus", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=4.0,
        hardiness_zones=["2a", "10a"], native_habitat="Asia", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Eruca vesicaria", common_names=["Arugula", "Rucola"],
        genus="Eruca", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=5.0,
        hardiness_zones=["3a", "10a"], native_habitat="Mediterranean", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Brassica oleracea var. capitata", common_names=["Cabbage", "Weißkohl"],
        genus="Brassica", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=5.0,
        hardiness_zones=["2a", "10a"], native_habitat="Europe", allelopathy_score=0.1,
    ),
    # ── Fabaceae (6) ───────────────────────────────────────────────────
    Species(
        scientific_name="Phaseolus vulgaris", common_names=["Common Bean", "Buschbohne", "Gartenbohne"],
        genus="Phaseolus", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=10.0,
        hardiness_zones=["3a", "10a"], native_habitat="Central America", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Pisum sativum", common_names=["Pea", "Erbse"],
        genus="Pisum", growth_habit=GrowthHabit.VINE, root_type=RootType.TAPROOT, base_temp=4.0,
        hardiness_zones=["3a", "10a"], native_habitat="Mediterranean", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Vicia faba", common_names=["Broad Bean", "Ackerbohne", "Dicke Bohne"],
        genus="Vicia", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=3.0,
        hardiness_zones=["2a", "9a"], native_habitat="Mediterranean", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Glycine max", common_names=["Soybean", "Sojabohne"],
        genus="Glycine", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=10.0,
        hardiness_zones=["3a", "9a"], native_habitat="East Asia", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Lens culinaris", common_names=["Lentil", "Linse"],
        genus="Lens", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=5.0,
        hardiness_zones=["4a", "9a"], native_habitat="Near East", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Trifolium pratense", common_names=["Red Clover", "Rotklee"],
        genus="Trifolium", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=4.0,
        hardiness_zones=["3a", "8a"], native_habitat="Europe", allelopathy_score=0.0,
    ),
    # ── Cucurbitaceae (6) ──────────────────────────────────────────────
    Species(
        scientific_name="Cucumis sativus", common_names=["Cucumber", "Gurke"],
        genus="Cucumis", growth_habit=GrowthHabit.VINE, root_type=RootType.FIBROUS, base_temp=12.0,
        hardiness_zones=["4a", "11a"], native_habitat="South Asia", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Cucumis melo", common_names=["Melon", "Melone", "Honigmelone"],
        genus="Cucumis", growth_habit=GrowthHabit.VINE, root_type=RootType.FIBROUS, base_temp=12.0,
        hardiness_zones=["4a", "11a"], native_habitat="Africa", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Cucurbita pepo", common_names=["Zucchini", "Squash"],
        genus="Cucurbita", growth_habit=GrowthHabit.VINE, root_type=RootType.FIBROUS, base_temp=10.0,
        hardiness_zones=["3a", "10a"], native_habitat="Americas", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Cucurbita maxima", common_names=["Pumpkin", "Kürbis", "Riesenkürbis"],
        genus="Cucurbita", growth_habit=GrowthHabit.VINE, root_type=RootType.FIBROUS, base_temp=10.0,
        hardiness_zones=["3a", "10a"], native_habitat="South America", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Citrullus lanatus", common_names=["Watermelon", "Wassermelone"],
        genus="Citrullus", growth_habit=GrowthHabit.VINE, root_type=RootType.TAPROOT, base_temp=15.0,
        hardiness_zones=["5a", "11a"], native_habitat="Africa", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Luffa aegyptiaca", common_names=["Luffa", "Schwammgurke"],
        genus="Luffa", growth_habit=GrowthHabit.VINE, root_type=RootType.FIBROUS, base_temp=15.0,
        hardiness_zones=["7a", "11a"], native_habitat="South Asia", allelopathy_score=0.0,
    ),
    # ── Asteraceae (6) ─────────────────────────────────────────────────
    Species(
        scientific_name="Lactuca sativa", common_names=["Lettuce", "Salat"],
        genus="Lactuca", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=4.0,
        hardiness_zones=["2a", "10a"], native_habitat="Mediterranean", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Cichorium intybus", common_names=["Chicory", "Chicorée", "Wegwarte"],
        genus="Cichorium", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=5.0,
        hardiness_zones=["3a", "9a"], native_habitat="Europe", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Helianthus annuus", common_names=["Sunflower", "Sonnenblume"],
        genus="Helianthus", growth_habit=GrowthHabit.HERB, root_type=RootType.TAPROOT, base_temp=8.0,
        hardiness_zones=["2a", "11a"], native_habitat="North America", allelopathy_score=0.4,
    ),
    Species(
        scientific_name="Tagetes erecta", common_names=["Marigold", "Tagetes", "Studentenblume"],
        genus="Tagetes", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=10.0,
        hardiness_zones=["2a", "11a"], native_habitat="Americas", allelopathy_score=0.3,
    ),
    Species(
        scientific_name="Matricaria chamomilla", common_names=["Chamomile", "Kamille"],
        genus="Matricaria", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=5.0,
        hardiness_zones=["3a", "9a"], native_habitat="Europe", allelopathy_score=0.0,
    ),
    Species(
        scientific_name="Artemisia dracunculus", common_names=["Tarragon", "Estragon"],
        genus="Artemisia", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=5.0,
        hardiness_zones=["4a", "8a"], native_habitat="Central Asia", allelopathy_score=0.2,
    ),
    # ── Poaceae (6) ────────────────────────────────────────────────────
    Species(
        scientific_name="Zea mays", common_names=["Corn", "Mais"],
        genus="Zea", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=10.0,
        hardiness_zones=["3a", "10a"], native_habitat="Central America", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Triticum aestivum", common_names=["Wheat", "Weizen"],
        genus="Triticum", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=4.0,
        hardiness_zones=["3a", "9a"], native_habitat="Near East", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Hordeum vulgare", common_names=["Barley", "Gerste"],
        genus="Hordeum", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=3.0,
        hardiness_zones=["3a", "9a"], native_habitat="Near East", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Avena sativa", common_names=["Oat", "Hafer"],
        genus="Avena", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=3.0,
        hardiness_zones=["3a", "9a"], native_habitat="Near East", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Oryza sativa", common_names=["Rice", "Reis"],
        genus="Oryza", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=12.0,
        hardiness_zones=["8a", "11a"], native_habitat="East Asia", allelopathy_score=0.1,
    ),
    Species(
        scientific_name="Sorghum bicolor", common_names=["Sorghum", "Hirse"],
        genus="Sorghum", growth_habit=GrowthHabit.HERB, root_type=RootType.FIBROUS, base_temp=10.0,
        hardiness_zones=["5a", "10a"], native_habitat="Africa", allelopathy_score=0.3,
    ),
]

# Cultivars: {scientific_name: [(name, breeder, days_to_maturity, traits), ...]}
CULTIVARS: dict[str, list[tuple[str, str | None, int | None, list[str]]]] = {
    "Solanum lycopersicum": [
        ("San Marzano", None, 80, ["heirloom"]),
        ("Cherry Tomato Sweet 100", None, 65, ["high_yield"]),
        ("Beefsteak", None, 85, ["heirloom", "high_yield"]),
    ],
    "Capsicum annuum": [
        ("California Wonder", None, 75, ["high_yield"]),
        ("Jalapeño", None, 70, ["heat_tolerant"]),
        ("Habanero", None, 90, ["heat_tolerant"]),
    ],
    "Lactuca sativa": [
        ("Butterhead", None, 55, ["early_maturing"]),
        ("Romaine", None, 70, []),
        ("Lollo Rossa", None, 50, ["ornamental"]),
    ],
    "Cannabis sativa": [
        ("Northern Lights", "Sensi Seeds", 65, ["compact"]),
        ("White Widow", "Green House Seeds", 60, ["high_yield"]),
        ("OG Kush", None, 56, ["high_yield"]),
    ],
    "Cucumis sativus": [
        ("Marketmore 76", None, 65, ["disease_resistant"]),
        ("Lemon Cucumber", None, 60, ["heirloom"]),
        ("Persian", None, 55, ["compact"]),
    ],
    "Brassica oleracea var. italica": [
        ("Calabrese", None, 65, ["high_yield"]),
        ("Marathon", None, 70, ["disease_resistant"]),
        ("De Cicco", None, 50, ["heirloom", "early_maturing"]),
    ],
    "Daucus carota": [
        ("Nantes", None, 70, []),
        ("Danvers 126", None, 75, ["drought_tolerant"]),
        ("Purple Haze", None, 70, ["ornamental"]),
    ],
    "Phaseolus vulgaris": [
        ("Provider", None, 50, ["early_maturing", "cold_hardy"]),
        ("Blue Lake 274", None, 58, ["high_yield"]),
        ("Kentucky Wonder", None, 65, ["heirloom"]),
    ],
}

# Companion planting pairs (species-level)
COMPANION_COMPATIBLE = [
    ("Solanum lycopersicum", "Ocimum basilicum", 0.9),
    ("Solanum lycopersicum", "Daucus carota", 0.75),
    ("Solanum lycopersicum", "Tagetes erecta", 0.8),
    ("Capsicum annuum", "Ocimum basilicum", 0.85),
    ("Cucumis sativus", "Anethum graveolens", 0.8),
    ("Cucumis sativus", "Phaseolus vulgaris", 0.75),
    ("Lactuca sativa", "Raphanus sativus", 0.8),
    ("Zea mays", "Phaseolus vulgaris", 0.9),
    ("Zea mays", "Cucurbita pepo", 0.85),
    ("Phaseolus vulgaris", "Cucurbita pepo", 0.8),
    ("Cannabis sativa", "Ocimum basilicum", 0.8),
    ("Cannabis sativa", "Lavandula angustifolia", 0.75),
    ("Mentha piperita", "Brassica oleracea var. capitata", 0.7),
    ("Thymus vulgaris", "Brassica oleracea var. capitata", 0.7),
    ("Daucus carota", "Pisum sativum", 0.8),
]

COMPANION_INCOMPATIBLE = [
    ("Foeniculum vulgare", "Solanum lycopersicum", "Strong allelopathy — fennel inhibits nightshades"),
    ("Foeniculum vulgare", "Phaseolus vulgaris", "Allelopathy — fennel inhibits legumes"),
    ("Solanum lycopersicum", "Brassica oleracea var. capitata", "Nutrient competition — both heavy feeders"),
    ("Cannabis sativa", "Cucumis sativus", "Shared pests (spider mites)"),
    ("Solanum lycopersicum", "Solanum tuberosum", "Same family, shared diseases (Phytophthora)"),
]

# Family-level edge data: shares_pest_risk
PEST_RISK_EDGES = [
    ("Solanaceae", "Cucurbitaceae", ["Blattläuse", "Weiße Fliege"], [], "medium"),
    ("Solanaceae", "Solanaceae", ["Kartoffelkäfer", "Blattläuse"], ["Kraut- und Braunfäule", "Fusarium"], "high"),
    ("Brassicaceae", "Brassicaceae", ["Kohlweißling", "Erdflöhe"], ["Kohlhernie", "Mehltau"], "high"),
    ("Cucurbitaceae", "Cucurbitaceae", ["Spinnmilben", "Blattläuse"], ["Mehltau", "Falscher Mehltau"], "high"),
    ("Brassicaceae", "Apiaceae", ["Blattläuse"], ["Mehltau"], "low"),
    ("Cannabaceae", "Cannabaceae",
     ["Spinnmilben", "Thripse", "Trauermücken"], ["Botrytis", "Mehltau", "Fusarium"], "high"),
    ("Cannabaceae", "Cucurbitaceae", ["Spinnmilben", "Blattläuse"], ["Mehltau"], "medium"),
]

# Family-level edge data: family_compatible_with
FAMILY_COMPATIBLE_EDGES = [
    ("Fabaceae", "Solanaceae", "nitrogen_fixation", 0.85, "N-Fixierung verbessert Starkzehrer-Versorgung"),
    ("Fabaceae", "Brassicaceae", "nitrogen_fixation", 0.80, "N-Fixierung nach Starkzehrer"),
    ("Fabaceae", "Cannabaceae", "nitrogen_fixation", 0.85, "N-Fixierung verbessert Starkzehrer-Versorgung"),
    ("Lamiaceae", "Solanaceae", "pest_deterrent", 0.75, "Ätherische Öle wirken abschreckend"),
    ("Lamiaceae", "Brassicaceae", "pest_deterrent", 0.70, "Basilikum/Minze gegen Kohlweißling"),
    ("Lamiaceae", "Cannabaceae", "pest_deterrent", 0.70, "Ätherische Öle gegen Spinnmilben und Thripse"),
    ("Asteraceae", "Cucurbitaceae", "pollinator_attraction", 0.65, "Blüten locken Bestäuber an"),
    ("Apiaceae", "Asteraceae", "pollinator_attraction", 0.60, "Komplementäre Blütenbesucher"),
]

# Family-level edge data: family_incompatible_with
FAMILY_INCOMPATIBLE_EDGES = [
    ("Solanaceae", "Solanaceae", "Selbstinkompatibilität: gemeinsame Krankheiten und Schädlinge", "severe"),
    ("Brassicaceae", "Brassicaceae", "Kohlhernie-Risiko bei wiederholtem Anbau", "severe"),
    ("Cucurbitaceae", "Cucurbitaceae", "Fusarium-Akkumulation im Boden", "moderate"),
]

DEFAULT_PHASES = [
    ("seedling", "Seedling", 14, 0, False, False, StressTolerance.LOW),
    ("vegetative", "Vegetative", 28, 1, False, False, StressTolerance.MEDIUM),
    ("flowering", "Flowering", 56, 2, False, False, StressTolerance.MEDIUM),
    ("ripening", "Ripening", 14, 3, False, True, StressTolerance.HIGH),
]


def run_seed() -> None:  # noqa: C901, PLR0912, PLR0915
    family_repo = get_family_repo()
    species_repo = get_species_repo()
    lifecycle_repo = get_lifecycle_repo()
    graph_repo = get_graph_repo()
    profile_gen = ResourceProfileGenerator()

    # ── Seed families (upsert) ─────────────────────────────────────────
    family_map: dict[str, str] = {}
    for family in FAMILIES:
        existing = family_repo.get_by_name(family.name)
        if existing:
            family_map[family.name] = existing.key or ""
            family_repo.update_family(existing.key or "", family)
            logger.info("family_updated", name=family.name)
        else:
            created = family_repo.create_family(family)
            family_map[family.name] = created.key or ""
            logger.info("family_created", name=family.name)

    # ── Seed rotation edges ────────────────────────────────────────────
    for from_name, to_name, wait_years, benefit_score, benefit_reason in ROTATION_EDGES:
        from_key = family_map.get(from_name, "")
        to_key = family_map.get(to_name, "")
        if from_key and to_key:
            try:
                graph_repo.set_rotation_successor(
                    from_key, to_key, wait_years,
                    benefit_score=benefit_score, benefit_reason=benefit_reason,
                )
                logger.info("rotation_edge_created", from_family=from_name, to_family=to_name)
            except Exception:
                logger.info("rotation_edge_exists", from_family=from_name, to_family=to_name)

    # ── Seed family-level edges ────────────────────────────────────────
    for a_name, b_name, shared_pests, shared_diseases, risk_level in PEST_RISK_EDGES:
        a_key = family_map.get(a_name, "")
        b_key = family_map.get(b_name, "")
        if a_key and b_key:
            try:
                graph_repo.set_pest_risk(a_key, b_key, shared_pests, shared_diseases, risk_level)
                logger.info("pest_risk_edge_created", a=a_name, b=b_name)
            except Exception:
                logger.info("pest_risk_edge_exists", a=a_name, b=b_name)

    for a_name, b_name, benefit_type, score, notes in FAMILY_COMPATIBLE_EDGES:
        a_key = family_map.get(a_name, "")
        b_key = family_map.get(b_name, "")
        if a_key and b_key:
            try:
                graph_repo.set_family_compatible(a_key, b_key, benefit_type, score, notes)
                logger.info("family_compatible_edge_created", a=a_name, b=b_name)
            except Exception:
                logger.info("family_compatible_edge_exists", a=a_name, b=b_name)

    for a_name, b_name, reason, severity in FAMILY_INCOMPATIBLE_EDGES:
        a_key = family_map.get(a_name, "")
        b_key = family_map.get(b_name, "")
        if a_key and b_key:
            try:
                graph_repo.set_family_incompatible(a_key, b_key, reason, severity)
                logger.info("family_incompatible_edge_created", a=a_name, b=b_name)
            except Exception:
                logger.info("family_incompatible_edge_exists", a=a_name, b=b_name)

    # ── Seed species ───────────────────────────────────────────────────
    family_species_map = {
        # Solanaceae
        "Solanum lycopersicum": "Solanaceae",
        "Capsicum annuum": "Solanaceae",
        "Solanum melongena": "Solanaceae",
        "Solanum tuberosum": "Solanaceae",
        "Physalis peruviana": "Solanaceae",
        "Nicotiana tabacum": "Solanaceae",
        # Cannabaceae
        "Cannabis sativa": "Cannabaceae",
        "Humulus lupulus": "Cannabaceae",
        # Lamiaceae
        "Ocimum basilicum": "Lamiaceae",
        "Mentha piperita": "Lamiaceae",
        "Thymus vulgaris": "Lamiaceae",
        "Salvia rosmarinus": "Lamiaceae",
        "Salvia officinalis": "Lamiaceae",
        "Lavandula angustifolia": "Lamiaceae",
        # Apiaceae
        "Daucus carota": "Apiaceae",
        "Foeniculum vulgare": "Apiaceae",
        "Anethum graveolens": "Apiaceae",
        "Coriandrum sativum": "Apiaceae",
        "Apium graveolens": "Apiaceae",
        "Petroselinum crispum": "Apiaceae",
        # Brassicaceae
        "Brassica oleracea var. italica": "Brassicaceae",
        "Brassica oleracea var. botrytis": "Brassicaceae",
        "Brassica oleracea var. gongylodes": "Brassicaceae",
        "Raphanus sativus": "Brassicaceae",
        "Eruca vesicaria": "Brassicaceae",
        "Brassica oleracea var. capitata": "Brassicaceae",
        # Fabaceae
        "Phaseolus vulgaris": "Fabaceae",
        "Pisum sativum": "Fabaceae",
        "Vicia faba": "Fabaceae",
        "Glycine max": "Fabaceae",
        "Lens culinaris": "Fabaceae",
        "Trifolium pratense": "Fabaceae",
        # Cucurbitaceae
        "Cucumis sativus": "Cucurbitaceae",
        "Cucumis melo": "Cucurbitaceae",
        "Cucurbita pepo": "Cucurbitaceae",
        "Cucurbita maxima": "Cucurbitaceae",
        "Citrullus lanatus": "Cucurbitaceae",
        "Luffa aegyptiaca": "Cucurbitaceae",
        # Asteraceae
        "Lactuca sativa": "Asteraceae",
        "Cichorium intybus": "Asteraceae",
        "Helianthus annuus": "Asteraceae",
        "Tagetes erecta": "Asteraceae",
        "Matricaria chamomilla": "Asteraceae",
        "Artemisia dracunculus": "Asteraceae",
        # Poaceae
        "Zea mays": "Poaceae",
        "Triticum aestivum": "Poaceae",
        "Hordeum vulgare": "Poaceae",
        "Avena sativa": "Poaceae",
        "Oryza sativa": "Poaceae",
        "Sorghum bicolor": "Poaceae",
    }

    species_key_map: dict[str, str] = {}  # scientific_name -> key

    for sp in SPECIES:
        existing = species_repo.get_by_scientific_name(sp.scientific_name)
        if existing:
            species_key_map[sp.scientific_name] = existing.key or ""
            logger.info("species_exists", name=sp.scientific_name)
            continue

        family_name = family_species_map.get(sp.scientific_name, "")
        sp.family_key = family_map.get(family_name, "")
        created_sp = species_repo.create(sp)
        species_key = created_sp.key or ""
        species_key_map[sp.scientific_name] = species_key
        logger.info("species_created", name=sp.scientific_name, key=species_key)

        # Create lifecycle
        lc = LifecycleConfig(
            species_key=species_key,
            cycle_type=CycleType.ANNUAL,
            photoperiod_type=PhotoperiodType.DAY_NEUTRAL,
        )
        created_lc = lifecycle_repo.create_lifecycle(lc)
        lc_key = created_lc.key or ""

        # Create default phases with profiles
        for name, display, duration, order, terminal, harvest, stress in DEFAULT_PHASES:
            phase = GrowthPhase(
                name=name,
                display_name=display,
                lifecycle_key=lc_key,
                typical_duration_days=duration,
                sequence_order=order,
                is_terminal=terminal,
                allows_harvest=harvest,
                stress_tolerance=stress,
            )
            created_phase = lifecycle_repo.create_phase(phase)
            phase_key = created_phase.key or ""

            req = profile_gen.generate_requirement_profile(name, phase_key)
            lifecycle_repo.create_requirement_profile(req)

            nut = profile_gen.generate_nutrient_profile(name, phase_key)
            lifecycle_repo.create_nutrient_profile(nut)

            logger.info("phase_created", species=sp.scientific_name, phase=name)

    # ── Seed cultivars ─────────────────────────────────────────────────
    for sci_name, cultivar_list in CULTIVARS.items():
        sp_key = species_key_map.get(sci_name, "")
        if not sp_key:
            logger.info("cultivar_species_not_found", species=sci_name)
            continue
        for cv_name, breeder, days, traits in cultivar_list:
            existing_cultivars = species_repo.get_cultivars(sp_key)
            if any(c.name == cv_name for c in existing_cultivars):
                logger.info("cultivar_exists", species=sci_name, cultivar=cv_name)
                continue
            from app.common.enums import PlantTrait

            cultivar = Cultivar(
                name=cv_name,
                species_key=sp_key,
                breeder=breeder,
                days_to_maturity=days,
                traits=[PlantTrait(t) for t in traits],
            )
            species_repo.create_cultivar(cultivar)
            logger.info("cultivar_created", species=sci_name, cultivar=cv_name)

    # ── Seed companion planting edges (species-level) ──────────────────
    for a_sci, b_sci, score in COMPANION_COMPATIBLE:
        a_key = species_key_map.get(a_sci, "")
        b_key = species_key_map.get(b_sci, "")
        if a_key and b_key:
            try:
                graph_repo.set_compatibility(a_key, b_key, score)
                logger.info("companion_compatible_created", a=a_sci, b=b_sci)
            except Exception:
                logger.info("companion_compatible_exists", a=a_sci, b=b_sci)

    for a_sci, b_sci, reason in COMPANION_INCOMPATIBLE:
        a_key = species_key_map.get(a_sci, "")
        b_key = species_key_map.get(b_sci, "")
        if a_key and b_key:
            try:
                graph_repo.set_incompatibility(a_key, b_key, reason)
                logger.info("companion_incompatible_created", a=a_sci, b=b_sci)
            except Exception:
                logger.info("companion_incompatible_exists", a=a_sci, b=b_sci)

    logger.info("seed_complete")


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed()
