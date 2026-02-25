import pytest
from pydantic import ValidationError

from app.domain.models.species import Cultivar, Species


class TestSpeciesValidation:
    def test_valid_species(self):
        s = Species(scientific_name="Solanum lycopersicum", genus="Solanum")
        assert s.scientific_name == "Solanum lycopersicum"

    def test_binomial_validation_fails(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Tomato", genus="Solanum")

    def test_allelopathy_range(self):
        s = Species(scientific_name="Genus species", allelopathy_score=0.5)
        assert s.allelopathy_score == 0.5

    def test_allelopathy_too_high(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", allelopathy_score=1.5)

    def test_allelopathy_too_low(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", allelopathy_score=-1.5)

    def test_valid_hardiness_zones(self):
        s = Species(scientific_name="Genus species", hardiness_zones=["7a", "7b", "8a"])
        assert len(s.hardiness_zones) == 3

    def test_invalid_hardiness_zone(self):
        with pytest.raises(ValidationError):
            Species(scientific_name="Genus species", hardiness_zones=["invalid"])


class TestCultivarValidation:
    def test_valid_cultivar(self):
        c = Cultivar(name="San Marzano", species_key="sp1")
        assert c.name == "San Marzano"

    def test_days_to_maturity_range(self):
        c = Cultivar(name="Test", species_key="sp1", days_to_maturity=90)
        assert c.days_to_maturity == 90

    def test_days_to_maturity_too_high(self):
        with pytest.raises(ValidationError):
            Cultivar(name="Test", species_key="sp1", days_to_maturity=400)

    def test_days_to_maturity_too_low(self):
        with pytest.raises(ValidationError):
            Cultivar(name="Test", species_key="sp1", days_to_maturity=0)
