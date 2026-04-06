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


class TestFromYamlPhases:
    def test_from_yaml_phases(self):
        yaml_data = [
            {
                "name": "seedling",
                "display_name": "Seedling",
                "typical_duration_days": 14,
                "sequence_order": 0,
                "is_terminal": False,
                "allows_harvest": False,
                "stress_tolerance": "low",
                "requirement_profile": {
                    "light_ppfd_target": 150,
                    "photoperiod_hours": 20.0,
                    "temperature_day_c": 22.0,
                    "temperature_night_c": 18.0,
                    "humidity_day_percent": 80,
                    "humidity_night_percent": 85,
                    "vpd_range": [0.3, 0.6],
                },
                "nutrient_profile": {
                    "npk_ratio": [2, 2, 2],
                    "target_ec_ms": 0.5,
                    "target_ph": 5.8,
                },
            },
        ]
        gen = ResourceProfileGenerator.from_yaml_phases(yaml_data)
        req = gen.generate_requirement_profile("seedling")
        assert req.light_ppfd_target == 150
        assert req.photoperiod_hours == 20.0
        assert req.humidity_day_percent == 80

        nut = gen.generate_nutrient_profile("seedling")
        assert nut.npk_ratio == (2, 2, 2)
        assert nut.target_ec_ms == 0.5

    def test_unknown_phase_uses_defaults(self):
        gen = ResourceProfileGenerator.from_yaml_phases([])
        req = gen.generate_requirement_profile("unknown_phase")
        assert req.light_ppfd_target == 400  # fallback default
        assert req.photoperiod_hours == 18.0


class TestGetVpdRanges:
    def test_vpd_ranges_from_defaults(self):
        gen = ResourceProfileGenerator()
        ranges = gen.get_vpd_ranges()
        assert ranges["seedling"] == (0.4, 0.8)
        assert ranges["flowering"] == (1.0, 1.5)
        assert "vegetative" in ranges
