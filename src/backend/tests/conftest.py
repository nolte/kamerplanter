import pytest

from app.common.exceptions import NotFoundError


def wire_get_or_raise(mock, entity: str = "Entity"):
    """Make a ``MagicMock`` repository's ``get_or_raise`` mirror ``get_by_key``.

    AP-15 replaced the copied ``get_by_key`` + ``None`` check + ``NotFoundError``
    service blocks with the repository's ``get_or_raise``. Solitary service tests
    stub ``get_by_key``; this helper lets those existing stubs keep driving both
    the found and not-found paths without touching every assertion.
    """

    def _get_or_raise(key):
        value = mock.get_by_key(key)
        if value is None:
            raise NotFoundError(entity, key)
        return value

    mock.get_or_raise.side_effect = _get_or_raise
    return mock


@pytest.fixture
def sample_species_data():
    return {
        "scientific_name": "Solanum lycopersicum",
        "common_names": ["Tomato"],
        "genus": "Solanum",
        "growth_habit": "herb",
        "root_type": "fibrous",
        "allelopathy_score": 0.0,
        "base_temp": 10.0,
        "hardiness_zones": ["7a", "7b", "8a"],
    }


@pytest.fixture
def sample_site_data():
    return {
        "name": "Indoor Garden",
        "type": "indoor",
        "climate_zone": "8a",
        "total_area_m2": 20.0,
    }


@pytest.fixture
def sample_location_data():
    return {
        "name": "Grow Tent 1",
        "site_key": "site_1",
        "area_m2": 4.0,
        "light_type": "led",
        "irrigation_system": "drip",
        "dimensions": (2.0, 2.0, 2.0),
    }


@pytest.fixture
def sample_substrate_data():
    return {
        "type": "coco",
        "brand": "Canna",
        "ph_base": 6.0,
        "ec_base_ms": 0.3,
        "water_retention": "high",
        "air_porosity_percent": 30.0,
        "buffer_capacity": "medium",
        "reusable": True,
        "max_reuse_cycles": 3,
    }
