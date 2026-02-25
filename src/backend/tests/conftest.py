import pytest


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
