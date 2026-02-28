"""Seed data for REQ-020 Onboarding Starter Kits."""

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.starter_kit import StarterKit

STARTER_KITS: list[dict] = [
    {
        "kit_id": "fensterbank-kraeuter",
        "name_i18n": {"de": "Fensterbrett-Kräuter", "en": "Windowsill Herbs"},
        "description_i18n": {
            "de": "Basilikum, Petersilie und Schnittlauch auf dem Fensterbrett — perfekt für Anfänger.",
            "en": "Basil, parsley, and chives on the windowsill — perfect for beginners.",
        },
        "difficulty": "beginner",
        "icon": "herbs",
        "plant_count_suggestion": 3,
        "site_type": "windowsill",
        "species_keys": [],
        "toxicity_warning": False,
        "includes_nutrient_plan": False,
        "tags": ["herbs", "kitchen", "beginner"],
        "sort_order": 0,
    },
    {
        "kit_id": "zimmerpflanzen",
        "name_i18n": {"de": "Zimmerpflanzen-Starter", "en": "Houseplant Starter"},
        "description_i18n": {
            "de": "Monstera, Pothos und Sansevieria — pflegeleichte Klassiker für jedes Zuhause.",
            "en": "Monstera, Pothos, and Sansevieria — low-maintenance classics for any home.",
        },
        "difficulty": "beginner",
        "icon": "houseplant",
        "plant_count_suggestion": 3,
        "site_type": "indoor",
        "species_keys": [],
        "toxicity_warning": True,
        "includes_nutrient_plan": False,
        "tags": ["houseplants", "indoor", "low-maintenance"],
        "sort_order": 1,
    },
    {
        "kit_id": "zimmerpflanzen-haustierfreundlich",
        "name_i18n": {"de": "Haustierfreundliche Zimmerpflanzen", "en": "Pet-Friendly Houseplants"},
        "description_i18n": {
            "de": "Calathea, Grünlilie und Pilea — sicher für Katzen und Hunde.",
            "en": "Calathea, Spider Plant, and Pilea — safe for cats and dogs.",
        },
        "difficulty": "beginner",
        "icon": "pet_friendly",
        "plant_count_suggestion": 3,
        "site_type": "indoor",
        "species_keys": [],
        "toxicity_warning": False,
        "includes_nutrient_plan": False,
        "tags": ["houseplants", "pet-friendly", "safe"],
        "sort_order": 2,
    },
    {
        "kit_id": "balkon-tomaten",
        "name_i18n": {"de": "Balkon-Tomaten", "en": "Balcony Tomatoes"},
        "description_i18n": {
            "de": "Buschtomaten und Kirschtomaten für den Balkon — erntefreudig und kompakt.",
            "en": "Bush and cherry tomatoes for the balcony — productive and compact.",
        },
        "difficulty": "intermediate",
        "icon": "tomato",
        "plant_count_suggestion": 4,
        "site_type": "balcony",
        "species_keys": [],
        "toxicity_warning": False,
        "includes_nutrient_plan": True,
        "tags": ["vegetables", "balcony", "tomatoes"],
        "sort_order": 3,
    },
    {
        "kit_id": "kleines-gemusebeet",
        "name_i18n": {"de": "Kleines Gemüsebeet", "en": "Small Vegetable Garden"},
        "description_i18n": {
            "de": "Salat, Radieschen und Karotten — das perfekte Einsteiger-Beet.",
            "en": "Lettuce, radishes, and carrots — the perfect starter garden bed.",
        },
        "difficulty": "intermediate",
        "icon": "vegetable",
        "plant_count_suggestion": 6,
        "site_type": "outdoor",
        "species_keys": [],
        "toxicity_warning": False,
        "includes_nutrient_plan": True,
        "tags": ["vegetables", "outdoor", "garden"],
        "sort_order": 4,
    },
    {
        "kit_id": "chili-zucht",
        "name_i18n": {"de": "Chili-Zucht", "en": "Chili Growing"},
        "description_i18n": {
            "de": "Jalapeño, Habanero und Cayenne — von mild bis scharf.",
            "en": "Jalapeño, Habanero, and Cayenne — from mild to hot.",
        },
        "difficulty": "intermediate",
        "icon": "chili",
        "plant_count_suggestion": 3,
        "site_type": "windowsill",
        "species_keys": [],
        "toxicity_warning": False,
        "includes_nutrient_plan": True,
        "tags": ["chili", "spicy", "indoor"],
        "sort_order": 5,
    },
    {
        "kit_id": "indoor-growzelt",
        "name_i18n": {"de": "Indoor-Growzelt", "en": "Indoor Grow Tent"},
        "description_i18n": {
            "de": "Komplette Growzelt-Einrichtung für kontrollierte Bedingungen.",
            "en": "Complete grow tent setup for controlled conditions.",
        },
        "difficulty": "advanced",
        "icon": "grow_tent",
        "plant_count_suggestion": 4,
        "site_type": "grow_tent",
        "species_keys": [],
        "toxicity_warning": False,
        "includes_nutrient_plan": True,
        "tags": ["indoor", "grow-tent", "controlled"],
        "sort_order": 6,
    },
    {
        "kit_id": "superhot-chili",
        "name_i18n": {"de": "Superhot-Chili", "en": "Superhot Chili"},
        "description_i18n": {
            "de": "Carolina Reaper, Trinidad Scorpion — für Chili-Enthusiasten.",
            "en": "Carolina Reaper, Trinidad Scorpion — for chili enthusiasts.",
        },
        "difficulty": "advanced",
        "icon": "fire",
        "plant_count_suggestion": 3,
        "site_type": "grow_tent",
        "species_keys": [],
        "toxicity_warning": False,
        "includes_nutrient_plan": True,
        "tags": ["chili", "superhot", "advanced"],
        "sort_order": 7,
    },
    {
        "kit_id": "microgreens",
        "name_i18n": {"de": "Microgreens", "en": "Microgreens"},
        "description_i18n": {
            "de": "Sonnenblume, Erbse und Radieschen als Microgreens — schnelle Ernte in 7–14 Tagen.",
            "en": "Sunflower, pea, and radish microgreens — quick harvest in 7–14 days.",
        },
        "difficulty": "beginner",
        "icon": "sprout",
        "plant_count_suggestion": 3,
        "site_type": "windowsill",
        "species_keys": [],
        "toxicity_warning": False,
        "includes_nutrient_plan": False,
        "tags": ["microgreens", "quick", "windowsill"],
        "sort_order": 8,
    },
]


def seed_starter_kits(db) -> int:
    """Seed starter kits into the database. Returns count of kits created."""
    repo = BaseArangoRepository(db, col.STARTER_KITS)
    created = 0
    for kit_data in STARTER_KITS:
        existing = repo.find_by_field("kit_id", kit_data["kit_id"])
        if not existing:
            kit = StarterKit(**kit_data)
            repo.create(kit)
            created += 1
    return created
