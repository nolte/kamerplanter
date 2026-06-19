"""Tests for denormalized species/cultivar label resolution.

The PlantInstanceService resolves species and cultivar keys to their full
models so the API can embed human-readable labels in plant responses
(instead of forcing the frontend to issue N+1 lookups).
"""

from unittest.mock import MagicMock

from app.domain.models.species import Cultivar, Species
from app.domain.services.plant_instance_service import PlantInstanceService


def _make_species() -> Species:
    return Species(
        _key="basil",
        scientific_name="Ocimum basilicum",
        common_names=["Basilikum", "Basil"],
        genus="Ocimum",
    )


def _make_cultivar() -> Cultivar:
    return Cultivar(_key="genovese", name="Genovese", species_key="basil")


class TestResolveSpeciesAndCultivar:
    def setup_method(self):
        self.species_repo = MagicMock()
        self.service = PlantInstanceService(
            MagicMock(),  # plant_repo
            MagicMock(),  # site_repo
            MagicMock(),  # rotation
            MagicMock(),  # companion
            species_repo=self.species_repo,
        )

    def test_resolve_species_returns_model(self):
        species = _make_species()
        self.species_repo.get_by_key.return_value = species
        assert self.service.resolve_species("basil") is species
        self.species_repo.get_by_key.assert_called_once_with("basil")

    def test_resolve_species_empty_key_skips_lookup(self):
        assert self.service.resolve_species("") is None
        self.species_repo.get_by_key.assert_not_called()

    def test_resolve_cultivar_returns_model(self):
        cultivar = _make_cultivar()
        self.species_repo.get_cultivar_by_key.return_value = cultivar
        assert self.service.resolve_cultivar("genovese") is cultivar
        self.species_repo.get_cultivar_by_key.assert_called_once_with("genovese")

    def test_resolve_cultivar_none_key_skips_lookup(self):
        assert self.service.resolve_cultivar(None) is None
        self.species_repo.get_cultivar_by_key.assert_not_called()


class TestResolveWithoutSpeciesRepo:
    """When no species_repo is wired the resolvers degrade gracefully."""

    def setup_method(self):
        self.service = PlantInstanceService(
            MagicMock(),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

    def test_resolve_species_without_repo(self):
        assert self.service.resolve_species("basil") is None

    def test_resolve_cultivar_without_repo(self):
        assert self.service.resolve_cultivar("genovese") is None
