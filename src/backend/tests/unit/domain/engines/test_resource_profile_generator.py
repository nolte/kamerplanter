from app.domain.engines.resource_profile_generator import ResourceProfileGenerator


class TestRequirementProfileGeneration:
    def setup_method(self):
        self.gen = ResourceProfileGenerator()

    def test_seedling_profile(self):
        p = self.gen.generate_requirement_profile("seedling")
        assert p.light_ppfd_target == 200
        assert p.humidity_day_percent == 70
        assert p.temperature_day_c == 24.0

    def test_vegetative_profile(self):
        p = self.gen.generate_requirement_profile("vegetative")
        assert p.light_ppfd_target == 400
        assert p.photoperiod_hours == 18.0

    def test_flowering_profile(self):
        p = self.gen.generate_requirement_profile("flowering")
        assert p.light_ppfd_target == 600
        assert p.photoperiod_hours == 12.0
        assert p.humidity_day_percent == 50

    def test_night_lt_day(self):
        for phase in ["seedling", "vegetative", "flowering", "ripening"]:
            p = self.gen.generate_requirement_profile(phase)
            assert p.temperature_night_c < p.temperature_day_c

    def test_phase_key_set(self):
        p = self.gen.generate_requirement_profile("seedling", "my_key")
        assert p.phase_key == "my_key"


class TestNutrientProfileGeneration:
    def setup_method(self):
        self.gen = ResourceProfileGenerator()

    def test_vegetative_npk(self):
        p = self.gen.generate_nutrient_profile("vegetative")
        assert p.npk_ratio == (3, 1, 2)

    def test_flowering_npk(self):
        p = self.gen.generate_nutrient_profile("flowering")
        assert p.npk_ratio == (1, 3, 2)

    def test_flushing_zero_npk(self):
        p = self.gen.generate_nutrient_profile("flushing")
        assert p.npk_ratio == (0, 0, 0)
        assert p.target_ec_ms == 0.0
