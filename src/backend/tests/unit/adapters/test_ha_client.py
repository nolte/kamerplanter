from unittest.mock import MagicMock, patch

import pytest

from app.data_access.external.ha_client import HomeAssistantClient


@pytest.fixture
def client():
    return HomeAssistantClient("http://ha.local:8123", "test-token", timeout=5)


class TestGetState:
    @patch("app.data_access.external.ha_client.httpx.get")
    def test_success(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "entity_id": "sensor.tank_ec",
            "state": "1.45",
            "last_changed": "2026-03-01T10:00:00+00:00",
            "attributes": {
                "unit_of_measurement": "mS/cm",
                "friendly_name": "Tank EC",
            },
        }
        mock_get.return_value = mock_response

        result = client.get_state("sensor.tank_ec")

        assert result is not None
        assert result["value"] == 1.45
        assert result["entity_id"] == "sensor.tank_ec"
        assert result["last_changed"] == "2026-03-01T10:00:00+00:00"
        assert result["unit"] == "mS/cm"
        mock_get.assert_called_once_with(
            "http://ha.local:8123/api/states/sensor.tank_ec",
            headers={"Authorization": "Bearer test-token"},
            timeout=5,
        )

    @patch("app.data_access.external.ha_client.httpx.get")
    def test_not_found(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = client.get_state("sensor.nonexistent")
        assert result is None

    @patch("app.data_access.external.ha_client.httpx.get")
    def test_unavailable_entity(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "entity_id": "sensor.tank_ec",
            "state": "unavailable",
            "last_changed": "2026-03-01T09:00:00+00:00",
            "attributes": {},
        }
        mock_get.return_value = mock_response

        result = client.get_state("sensor.tank_ec")
        assert result is not None
        assert result["value"] is None

    @patch("app.data_access.external.ha_client.httpx.get")
    def test_unknown_entity(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "entity_id": "sensor.tank_ec",
            "state": "unknown",
            "last_changed": "2026-03-01T09:00:00+00:00",
            "attributes": {},
        }
        mock_get.return_value = mock_response

        result = client.get_state("sensor.tank_ec")
        assert result is not None
        assert result["value"] is None

    @patch("app.data_access.external.ha_client.httpx.get")
    def test_trailing_slash_stripped(self, mock_get, client):
        client_with_slash = HomeAssistantClient("http://ha.local:8123/", "token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "state": "6.5",
            "last_changed": "2026-03-01T10:00:00+00:00",
            "attributes": {"unit_of_measurement": "pH"},
        }
        mock_get.return_value = mock_response

        client_with_slash.get_state("sensor.ph")
        call_url = mock_get.call_args[0][0]
        assert "//" not in call_url.replace("http://", "")

    @patch("app.data_access.external.ha_client.httpx.get")
    def test_non_numeric_state(self, mock_get, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "state": "on",
            "last_changed": "2026-03-01T10:00:00+00:00",
            "attributes": {},
        }
        mock_get.return_value = mock_response

        result = client.get_state("sensor.something")
        assert result is not None
        assert result["value"] is None
