"""Test calculation endpoints that don't require database."""

from unittest.mock import patch

from fastapi.testclient import TestClient


def _get_client():
    """Create test client, mocking DB connection."""
    with patch("app.main.get_connection"), patch("app.main.ensure_collections"):
        from app.main import app

        return TestClient(app)


class TestVPDCalculation:
    def test_vpd_calculation(self):
        client = _get_client()
        response = client.post(
            "/api/v1/calculations/vpd",
            json={
                "temp_c": 25.0,
                "humidity_percent": 60.0,
                "phase": "vegetative",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "vpd_kpa" in data
        assert "status" in data
        assert "recommendation" in data
        assert data["vpd_kpa"] > 0

    def test_vpd_high_humidity(self):
        client = _get_client()
        response = client.post(
            "/api/v1/calculations/vpd",
            json={
                "temp_c": 25.0,
                "humidity_percent": 95.0,
                "phase": "seedling",
            },
        )
        data = response.json()
        assert data["vpd_kpa"] < 0.5


class TestGDDCalculation:
    def test_gdd_calculation(self):
        client = _get_client()
        response = client.post(
            "/api/v1/calculations/gdd",
            json={
                "daily_temps": [[30.0, 20.0], [28.0, 18.0]],
                "base_temp_c": 10.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accumulated_gdd"] == 28.0
        assert data["days_counted"] == 2


class TestSlotCapacity:
    def test_slot_capacity(self):
        client = _get_client()
        response = client.post(
            "/api/v1/calculations/slot-capacity",
            json={
                "area_m2": 4.0,
                "plant_spacing_cm": 50.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["max_capacity"] == 16
        assert len(data["optimal_range"]) == 2
        assert data["plants_per_m2"] > 0


class TestPhotoperiodTransition:
    def test_transition(self):
        client = _get_client()
        response = client.post(
            "/api/v1/calculations/photoperiod-transition",
            json={
                "current_hours": 18.0,
                "target_hours": 12.0,
                "transition_days": 7,
                "ppfd": 400,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["schedule"]) == 7
        assert data["schedule"][-1]["photoperiod_hours"] == 12.0


class TestHealthEndpoints:
    def test_liveness(self):
        client = _get_client()
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "alive"
