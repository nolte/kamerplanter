from app.common.enums import SiteType, StarterKitDifficulty
from app.domain.engines.onboarding_engine import OnboardingEngine
from app.domain.models.starter_kit import StarterKit


def _make_kit(**overrides) -> StarterKit:
    defaults = {
        "kit_id": "test-kit",
        "name_i18n": {"de": "Test-Kit", "en": "Test Kit"},
        "description_i18n": {"de": "Beschreibung", "en": "Description"},
        "difficulty": StarterKitDifficulty.BEGINNER,
        "plant_count_suggestion": 3,
        "site_type": SiteType.INDOOR,
        "species_keys": ["species1", "species2", "species3"],
    }
    defaults.update(overrides)
    return StarterKit(**defaults)


class TestValidateKitApplication:
    engine = OnboardingEngine()

    def test_valid_application(self):
        kit = _make_kit()
        errors = self.engine.validate_kit_application(kit, "My Garden", 3)
        assert errors == []

    def test_empty_site_name(self):
        kit = _make_kit()
        errors = self.engine.validate_kit_application(kit, "", 3)
        assert any("Site name" in e for e in errors)

    def test_zero_plants(self):
        kit = _make_kit()
        errors = self.engine.validate_kit_application(kit, "Garden", 0)
        assert any("At least one" in e for e in errors)

    def test_excessive_plant_count(self):
        kit = _make_kit(plant_count_suggestion=3)
        errors = self.engine.validate_kit_application(kit, "Garden", 10)
        assert any("exceeds 3x" in e for e in errors)

    def test_no_species_configured(self):
        kit = _make_kit(species_keys=[])
        errors = self.engine.validate_kit_application(kit, "Garden", 3)
        assert any("no species" in e for e in errors)


class TestBuildEntityPlan:
    engine = OnboardingEngine()

    def test_basic_plan(self):
        kit = _make_kit(species_keys=["s1", "s2"])
        plan = self.engine.build_entity_plan(kit, "My Garden", 4)
        assert plan["site_name"] == "My Garden"
        assert plan["total_plants"] == 4
        assert len(plan["plant_assignments"]) == 2

    def test_even_distribution(self):
        kit = _make_kit(species_keys=["s1", "s2"])
        plan = self.engine.build_entity_plan(kit, "Garden", 6)
        counts = [a["count"] for a in plan["plant_assignments"]]
        assert sum(counts) == 6
        assert all(c == 3 for c in counts)

    def test_uneven_distribution(self):
        kit = _make_kit(species_keys=["s1", "s2", "s3"])
        plan = self.engine.build_entity_plan(kit, "Garden", 5)
        counts = [a["count"] for a in plan["plant_assignments"]]
        assert sum(counts) == 5
        # 5 / 3 = 1 remainder 2 → first two get 2, last gets 1
        assert sorted(counts, reverse=True) == [2, 2, 1]

    def test_empty_species_returns_zero_plan(self):
        kit = _make_kit(species_keys=[])
        plan = self.engine.build_entity_plan(kit, "Garden", 3)
        assert plan["plants"] == 0

    def test_single_species(self):
        kit = _make_kit(species_keys=["s1"])
        plan = self.engine.build_entity_plan(kit, "Garden", 5)
        assert plan["plant_assignments"][0]["count"] == 5

    def test_site_type_propagated(self):
        kit = _make_kit(site_type=SiteType.BALCONY)
        plan = self.engine.build_entity_plan(kit, "Garden", 3)
        assert plan["site_type"] == "balcony"
