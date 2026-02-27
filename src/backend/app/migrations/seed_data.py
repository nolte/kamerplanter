"""Seed database with botanical families, common species, cultivars, and default profiles."""

import structlog

from app.common.dependencies import (
    get_family_repo,
    get_graph_repo,
    get_harvest_repo,
    get_ipm_repo,
    get_lifecycle_repo,
    get_species_repo,
    get_task_repo,
)
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

# ── REQ-010 IPM Seed Data ───────────────────────────────────────────
from app.domain.models.ipm import Disease, Pest, Treatment  # noqa: E402

IPM_PESTS = [
    Pest(scientific_name="Tetranychus urticae", common_name="Spider Mites", pest_type="arachnid",
         lifecycle_days=21, optimal_temp_min=25.0, optimal_temp_max=30.0, detection_difficulty="medium"),
    Pest(scientific_name="Aphis gossypii", common_name="Aphids", pest_type="insect",
         lifecycle_days=14, optimal_temp_min=20.0, optimal_temp_max=25.0, detection_difficulty="easy"),
    Pest(scientific_name="Frankliniella occidentalis", common_name="Thrips", pest_type="insect",
         lifecycle_days=18, optimal_temp_min=20.0, optimal_temp_max=28.0, detection_difficulty="hard"),
    Pest(scientific_name="Bradysia spp.", common_name="Fungus Gnats", pest_type="insect",
         lifecycle_days=28, optimal_temp_min=20.0, optimal_temp_max=25.0, detection_difficulty="easy"),
    Pest(scientific_name="Trialeurodes vaporariorum", common_name="Whitefly", pest_type="insect",
         lifecycle_days=30, optimal_temp_min=22.0, optimal_temp_max=28.0, detection_difficulty="easy"),
    Pest(scientific_name="Trichoplusia ni", common_name="Caterpillar", pest_type="insect",
         lifecycle_days=35, optimal_temp_min=20.0, optimal_temp_max=28.0, detection_difficulty="medium"),
    Pest(scientific_name="Pseudococcus longispinus", common_name="Mealybug", pest_type="insect",
         lifecycle_days=40, optimal_temp_min=22.0, optimal_temp_max=30.0, detection_difficulty="medium"),
    Pest(scientific_name="Phyllotreta spp.", common_name="Flea Beetle", pest_type="insect",
         lifecycle_days=45, optimal_temp_min=20.0, optimal_temp_max=27.0, detection_difficulty="easy"),
    Pest(scientific_name="Arion vulgaris", common_name="Slug", pest_type="gastropod",
         lifecycle_days=365, optimal_temp_min=10.0, optimal_temp_max=20.0, detection_difficulty="easy"),
    Pest(scientific_name="Meloidogyne spp.", common_name="Nematode", pest_type="nematode",
         lifecycle_days=30, optimal_temp_min=20.0, optimal_temp_max=30.0, detection_difficulty="hard"),
]

IPM_DISEASES = [
    Disease(scientific_name="Erysiphe spp.", common_name="Powdery Mildew", pathogen_type="fungal",
            incubation_period_days=5, environmental_triggers=["high_humidity", "poor_ventilation"],
            affected_plant_parts=["leaf", "stem"]),
    Disease(scientific_name="Botrytis cinerea", common_name="Botrytis (Grey Mold)", pathogen_type="fungal",
            incubation_period_days=3, environmental_triggers=["high_humidity", "low_temperature"],
            affected_plant_parts=["flower", "fruit", "leaf"]),
    Disease(scientific_name="Fusarium oxysporum", common_name="Fusarium Wilt", pathogen_type="fungal",
            incubation_period_days=14, environmental_triggers=["warm_soil", "overwatering"],
            affected_plant_parts=["root", "stem"]),
    Disease(scientific_name="Peronospora spp.", common_name="Downy Mildew", pathogen_type="fungal",
            incubation_period_days=7, environmental_triggers=["cool_wet", "poor_ventilation"],
            affected_plant_parts=["leaf"]),
    Disease(scientific_name="Pythium spp.", common_name="Root Rot", pathogen_type="fungal",
            incubation_period_days=5, environmental_triggers=["overwatering", "poor_drainage"],
            affected_plant_parts=["root"]),
    Disease(scientific_name="Xanthomonas campestris", common_name="Bacterial Spot", pathogen_type="bacterial",
            incubation_period_days=5, environmental_triggers=["high_humidity", "warm_temperature"],
            affected_plant_parts=["leaf", "fruit"]),
    Disease(scientific_name="Tobacco mosaic virus", common_name="Tobacco Mosaic Virus", pathogen_type="viral",
            incubation_period_days=14, environmental_triggers=["mechanical_transmission"],
            affected_plant_parts=["leaf", "stem"]),
    Disease(scientific_name="Phytophthora infestans", common_name="Late Blight", pathogen_type="fungal",
            incubation_period_days=7, environmental_triggers=["cool_wet", "prolonged_moisture"],
            affected_plant_parts=["leaf", "stem", "fruit"]),
]

IPM_TREATMENTS = [
    # Cultural (4)
    Treatment(name="Crop Rotation", treatment_type="cultural", application_method="cultural",
              description="Rotate plant families to break pest/disease cycles"),
    Treatment(name="Sanitation", treatment_type="cultural", application_method="cultural",
              description="Remove dead plant material and debris"),
    Treatment(name="Resistant Varieties", treatment_type="cultural", application_method="cultural",
              description="Use disease-resistant cultivars"),
    Treatment(name="Environmental Control", treatment_type="cultural", application_method="cultural",
              description="Adjust temperature, humidity, and ventilation"),
    # Biological (3)
    Treatment(name="Phytoseiulus persimilis", treatment_type="biological", application_method="release",
              description="Predatory mite for spider mite control"),
    Treatment(name="Encarsia formosa", treatment_type="biological", application_method="release",
              description="Parasitic wasp for whitefly control"),
    Treatment(name="Bacillus thuringiensis (Bt)", treatment_type="biological", application_method="spray",
              description="Biological insecticide for caterpillar control"),
    # Mechanical (2)
    Treatment(name="Sticky Traps", treatment_type="mechanical", application_method="cultural",
              description="Yellow/blue sticky traps for flying insects"),
    Treatment(name="Hand Removal", treatment_type="mechanical", application_method="cultural",
              description="Manual removal of pests"),
    # Chemical (3)
    Treatment(name="Pyrethrin", treatment_type="chemical", active_ingredient="pyrethrin",
              application_method="spray", safety_interval_days=7, dosage_per_liter=1.0,
              protective_equipment=["gloves", "mask"]),
    Treatment(name="Neem Oil", treatment_type="chemical", active_ingredient="azadirachtin",
              application_method="spray", safety_interval_days=3, dosage_per_liter=5.0,
              protective_equipment=["gloves"]),
    Treatment(name="Spinosad", treatment_type="chemical", active_ingredient="spinosad",
              application_method="spray", safety_interval_days=14, dosage_per_liter=0.5,
              protective_equipment=["gloves", "mask", "goggles"]),
]

# Treatment → Pest targeting (treatment_name, pest_common_name)
IPM_TARGETS_PEST = [
    ("Phytoseiulus persimilis", "Spider Mites"),
    ("Pyrethrin", "Spider Mites"),
    ("Neem Oil", "Spider Mites"),
    ("Neem Oil", "Aphids"),
    ("Pyrethrin", "Aphids"),
    ("Sticky Traps", "Thrips"),
    ("Spinosad", "Thrips"),
    ("Sticky Traps", "Fungus Gnats"),
    ("Encarsia formosa", "Whitefly"),
    ("Sticky Traps", "Whitefly"),
    ("Bacillus thuringiensis (Bt)", "Caterpillar"),
    ("Neem Oil", "Mealybug"),
    ("Hand Removal", "Slug"),
]

# Treatment → Disease targeting (treatment_name, disease_common_name)
IPM_TARGETS_DISEASE = [
    ("Environmental Control", "Powdery Mildew"),
    ("Environmental Control", "Botrytis (Grey Mold)"),
    ("Environmental Control", "Downy Mildew"),
    ("Sanitation", "Botrytis (Grey Mold)"),
    ("Sanitation", "Fusarium Wilt"),
    ("Resistant Varieties", "Fusarium Wilt"),
    ("Resistant Varieties", "Tobacco Mosaic Virus"),
    ("Crop Rotation", "Late Blight"),
]

# Contraindicated pairs (treatment_a, treatment_b)
IPM_CONTRAINDICATED = [
    ("Phytoseiulus persimilis", "Pyrethrin"),
    ("Encarsia formosa", "Pyrethrin"),
    ("Phytoseiulus persimilis", "Spinosad"),
]

# ── REQ-007 Harvest Seed Data ───────────────────────────────────────
from app.domain.models.harvest import HarvestIndicator  # noqa: E402

# (indicator_type, measurement_unit, measurement_method, observation_frequency, reliability_score, species_group)
HARVEST_INDICATORS = [
    # Cannabis
    ("trichome", "percentage_milky", "magnification_60x", "daily", 0.9, "Cannabis sativa"),
    ("color", "pistil_brown_percent", "visual", "daily", 0.7, "Cannabis sativa"),
    ("aroma", "terpene_intensity", "olfactory", "daily", 0.5, "Cannabis sativa"),
    # Solanaceae
    ("color", "color_change_percent", "visual", "daily", 0.85, "Solanum lycopersicum"),
    ("brix", "brix_degrees", "refractometer", "weekly", 0.8, "Solanum lycopersicum"),
    ("size", "diameter_cm", "caliper", "weekly", 0.7, "Solanum lycopersicum"),
    ("texture", "firmness_kg", "penetrometer", "weekly", 0.6, "Solanum lycopersicum"),
    # Brassicaceae
    ("size", "head_diameter_cm", "caliper", "weekly", 0.8, "Brassica oleracea var. italica"),
    ("texture", "compactness_score", "manual", "weekly", 0.75, "Brassica oleracea var. italica"),
    ("days_since_flowering", "days", "calendar", "daily", 0.7, "Brassica oleracea var. italica"),
    # Asteraceae
    ("texture", "leaf_crispness", "manual", "daily", 0.8, "Lactuca sativa"),
    ("size", "head_weight_g", "scale", "weekly", 0.75, "Lactuca sativa"),
    ("color", "green_intensity", "visual", "daily", 0.6, "Lactuca sativa"),
]

# ── REQ-006 Task Seed Data ──────────────────────────────────────────
from app.domain.models.task import TaskTemplate, WorkflowTemplate  # noqa: E402

WORKFLOW_TEMPLATES = [
    WorkflowTemplate(
        name="Cannabis SOG", description="Sea of Green workflow for cannabis",
        created_by="system", version="1.0", species_compatible=["Cannabis sativa"],
        growth_system="indoor", difficulty_level="intermediate", category="harvest",
        tags=["cannabis", "sog", "indoor"], is_system=True,
    ),
    WorkflowTemplate(
        name="Tomato Standard", description="Standard tomato growing workflow",
        created_by="system", version="1.0", species_compatible=["Solanum lycopersicum"],
        growth_system="greenhouse", difficulty_level="beginner", category="maintenance",
        tags=["tomato", "standard"], is_system=True,
    ),
    WorkflowTemplate(
        name="General Maintenance", description="General recurring maintenance tasks",
        created_by="system", version="1.0", species_compatible=[],
        difficulty_level="beginner", category="maintenance",
        tags=["general", "maintenance"], is_system=True,
    ),
]

# (name, instruction, category, trigger_type, trigger_phase, days_offset, stress_level,
#  duration_min, requires_photo, skill_level, workflow_name, sequence_order)
TASK_TEMPLATES = [
    # Cannabis SOG
    ("Transplant to SOG", "Transplant rooted clones to SOG positions", "transplant",
     "days_after_planting", "vegetative", 14, "medium", 30, False, "beginner", "Cannabis SOG", 0),
    ("Defoliation", "Remove large fan leaves to improve light penetration", "pruning",
     "days_after_planting", "vegetative", 18, "high", 45, True, "intermediate", "Cannabis SOG", 1),
    ("Flip to 12/12", "Switch lighting to 12/12 to initiate flowering", "maintenance",
     "days_after_planting", "vegetative", 21, "none", 15, False, "beginner", "Cannabis SOG", 2),
    ("Lollipopping", "Remove lower growth for upper canopy focus", "pruning",
     "days_after_planting", "flowering", 35, "high", 60, True, "advanced", "Cannabis SOG", 3),
    ("Flushing", "Begin plain water flushing before harvest", "feeding",
     "days_after_planting", "flowering", 56, "none", 20, False, "beginner", "Cannabis SOG", 4),
    ("Harvest", "Harvest mature plants", "harvest",
     "days_after_planting", "flowering", 70, "none", 120, True, "intermediate", "Cannabis SOG", 5),
    # Tomato Standard
    ("Transplant Seedlings", "Move seedlings to final containers", "transplant",
     "phase_entry", "vegetative", 0, "medium", 30, False, "beginner", "Tomato Standard", 0),
    ("Install Stakes", "Set up stakes or cages for support", "maintenance",
     "days_after_phase", "vegetative", 7, "none", 20, False, "beginner", "Tomato Standard", 1),
    ("Prune Suckers", "Remove side shoots to maintain single stem", "pruning",
     "days_after_phase", "vegetative", 14, "medium", 30, True, "intermediate", "Tomato Standard", 2),
    ("Weekly Feeding", "Apply balanced fertilizer per nutrient plan", "feeding",
     "manual", None, 0, "none", 15, False, "beginner", "Tomato Standard", 3),
    ("Fruit Observation", "Check fruit development and ripeness indicators", "observation",
     "phase_entry", "flowering", 0, "none", 15, True, "beginner", "Tomato Standard", 4),
    ("Harvest Ripe Fruit", "Pick ripe tomatoes as they reach maturity", "harvest",
     "manual", None, 0, "none", 30, True, "beginner", "Tomato Standard", 5),
    # General Maintenance
    ("Weekly Inspection", "Perform general plant health inspection", "observation",
     "manual", None, 0, "none", 30, True, "beginner", "General Maintenance", 0),
    ("Monthly Feeding Review", "Review and adjust feeding schedule", "feeding",
     "manual", None, 0, "none", 20, False, "intermediate", "General Maintenance", 1),
    ("Substrate Check", "Check substrate pH, EC and moisture levels", "maintenance",
     "manual", None, 0, "none", 15, False, "beginner", "General Maintenance", 2),
    ("Equipment Maintenance", "Clean and check growing equipment", "maintenance",
     "manual", None, 0, "none", 45, False, "beginner", "General Maintenance", 3),
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

    # ── Seed IPM data (REQ-010) ─────────────────────────────────────
    ipm_repo = get_ipm_repo()
    pest_key_map: dict[str, str] = {}
    for pest in IPM_PESTS:
        existing_pests, _ = ipm_repo.get_all_pests(0, 200)
        if any(p.scientific_name == pest.scientific_name for p in existing_pests):
            for p in existing_pests:
                if p.scientific_name == pest.scientific_name:
                    pest_key_map[pest.common_name] = p.key or ""
            logger.info("pest_exists", name=pest.common_name)
            continue
        created = ipm_repo.create_pest(pest)
        pest_key_map[pest.common_name] = created.key or ""
        logger.info("pest_created", name=pest.common_name)

    disease_key_map: dict[str, str] = {}
    for disease in IPM_DISEASES:
        existing_diseases, _ = ipm_repo.get_all_diseases(0, 200)
        if any(d.scientific_name == disease.scientific_name for d in existing_diseases):
            for d in existing_diseases:
                if d.scientific_name == disease.scientific_name:
                    disease_key_map[d.common_name] = d.key or ""
            logger.info("disease_exists", name=disease.common_name)
            continue
        created = ipm_repo.create_disease(disease)
        disease_key_map[disease.common_name] = created.key or ""
        logger.info("disease_created", name=disease.common_name)

    treatment_key_map: dict[str, str] = {}
    for treatment in IPM_TREATMENTS:
        existing_treatments, _ = ipm_repo.get_all_treatments(0, 200)
        if any(t.name == treatment.name for t in existing_treatments):
            for t in existing_treatments:
                if t.name == treatment.name:
                    treatment_key_map[t.name] = t.key or ""
            logger.info("treatment_exists", name=treatment.name)
            continue
        created = ipm_repo.create_treatment(treatment)
        treatment_key_map[treatment.name] = created.key or ""
        logger.info("treatment_created", name=treatment.name)

    for treat_name, pest_name in IPM_TARGETS_PEST:
        t_key = treatment_key_map.get(treat_name, "")
        p_key = pest_key_map.get(pest_name, "")
        if t_key and p_key:
            try:
                ipm_repo.create_targets_pest_edge(t_key, p_key)
                logger.info("targets_pest_edge", treatment=treat_name, pest=pest_name)
            except Exception:
                logger.info("targets_pest_edge_exists", treatment=treat_name, pest=pest_name)

    for treat_name, disease_name in IPM_TARGETS_DISEASE:
        t_key = treatment_key_map.get(treat_name, "")
        d_key = disease_key_map.get(disease_name, "")
        if t_key and d_key:
            try:
                ipm_repo.create_targets_disease_edge(t_key, d_key)
                logger.info("targets_disease_edge", treatment=treat_name, disease=disease_name)
            except Exception:
                logger.info("targets_disease_edge_exists", treatment=treat_name, disease=disease_name)

    for a_name, b_name in IPM_CONTRAINDICATED:
        a_key = treatment_key_map.get(a_name, "")
        b_key = treatment_key_map.get(b_name, "")
        if a_key and b_key:
            try:
                ipm_repo.create_contraindicated_edge(a_key, b_key)
                logger.info("contraindicated_edge", a=a_name, b=b_name)
            except Exception:
                logger.info("contraindicated_edge_exists", a=a_name, b=b_name)

    # ── Seed Harvest indicators (REQ-007) ───────────────────────────
    harvest_repo = get_harvest_repo()
    for ind_type, unit, method, freq, reliability, sci_name in HARVEST_INDICATORS:
        sp_key = species_key_map.get(sci_name, "")
        indicator = HarvestIndicator(
            indicator_type=ind_type, measurement_unit=unit,
            measurement_method=method, observation_frequency=freq,
            reliability_score=reliability, species_key=sp_key or None,
        )
        try:
            harvest_repo.create_indicator(indicator)
            logger.info("harvest_indicator_created", type=ind_type, species=sci_name)
        except Exception:
            logger.info("harvest_indicator_exists", type=ind_type, species=sci_name)

    # ── Seed Workflow templates + Task templates (REQ-006) ──────────
    task_repo = get_task_repo()
    wf_key_map: dict[str, str] = {}
    for wt in WORKFLOW_TEMPLATES:
        existing_wfs, _ = task_repo.get_all_workflow_templates(0, 200)
        if any(w.name == wt.name for w in existing_wfs):
            for w in existing_wfs:
                if w.name == wt.name:
                    wf_key_map[w.name] = w.key or ""
            logger.info("workflow_template_exists", name=wt.name)
            continue
        created = task_repo.create_workflow_template(wt)
        wf_key_map[wt.name] = created.key or ""
        logger.info("workflow_template_created", name=wt.name)

    for (name, instruction, category, trigger_type, trigger_phase, days_offset,
         stress_level, duration_min, requires_photo, skill_level, wf_name, seq_order) in TASK_TEMPLATES:
        wf_key = wf_key_map.get(wf_name, "")
        if not wf_key:
            continue
        tt = TaskTemplate(
            name=name, instruction=instruction, category=category,
            trigger_type=trigger_type, trigger_phase=trigger_phase,
            days_offset=days_offset, stress_level=stress_level,
            estimated_duration_minutes=duration_min,
            requires_photo=requires_photo, skill_level=skill_level,
            workflow_template_key=wf_key, sequence_order=seq_order,
        )
        try:
            task_repo.create_task_template(tt)
            logger.info("task_template_created", name=name, workflow=wf_name)
        except Exception:
            logger.info("task_template_exists", name=name, workflow=wf_name)

    logger.info("seed_complete")


if __name__ == "__main__":
    from app.config.logging import setup_logging

    setup_logging()
    from app.migrations.arango_setup import run_setup

    run_setup()
    run_seed()
