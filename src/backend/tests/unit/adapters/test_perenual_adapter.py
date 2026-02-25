"""Unit tests for Perenual adapter with mocked HTTP responses."""

from unittest.mock import MagicMock, patch

import pytest

from app.common.exceptions import ExternalSourceError
from app.data_access.external.perenual_adapter import PerenualAdapter, _extract_genus, _parse_hardiness


@pytest.fixture
def adapter():
    a = PerenualAdapter()
    a._client = MagicMock()
    return a


PERENUAL_SEARCH_RESPONSE = {
    "data": [
        {
            "id": 100,
            "scientific_name": "Rosa canina",
            "common_name": "Dog Rose",
            "family": "Rosaceae",
            "type": "Shrub",
            "cycle": "Perennial",
            "watering": "Average",
            "sunlight": ["full sun", "part shade"],
            "hardiness": {"min": "5", "max": "9"},
            "default_image": {"regular_url": "https://example.com/rosa.jpg"},
            "description": "A thorny rose species.",
        },
    ],
    "total": 1,
}

PERENUAL_DETAILS_RESPONSE = {
    "id": 100,
    "scientific_name": "Rosa canina",
    "common_name": "Dog Rose",
    "family": "Rosaceae",
    "type": "Shrub",
    "cycle": "Perennial",
    "watering": "Average",
    "sunlight": ["full sun"],
    "hardiness": {"min": "5", "max": "9"},
    "default_image": None,
    "description": "Detailed description.",
}


class TestSearchSpecies:
    @patch("app.data_access.external.perenual_adapter.settings")
    def test_search_returns_mapped_results(self, mock_settings, adapter):
        mock_settings.perenual_api_key = "test_key"
        response = MagicMock()
        response.json.return_value = PERENUAL_SEARCH_RESPONSE
        response.raise_for_status.return_value = None
        adapter._client.get.return_value = response

        results = adapter.search_species("Rosa")

        assert len(results) == 1
        assert results[0].external_id == "100"
        assert results[0].scientific_name == "Rosa canina"
        assert results[0].common_names == ["Dog Rose"]
        assert results[0].genus == "Rosa"
        assert results[0].family_name == "Rosaceae"
        assert results[0].growth_habit == "Shrub"
        assert results[0].hardiness_zones == ["5", "9"]
        assert results[0].image_url == "https://example.com/rosa.jpg"
        assert results[0].sunlight == ["full sun", "part shade"]

    @patch("app.data_access.external.perenual_adapter.settings")
    def test_search_no_api_key(self, mock_settings, adapter):
        mock_settings.perenual_api_key = ""

        results = adapter.search_species("Rosa")

        assert results == []

    @patch("app.data_access.external.perenual_adapter.settings")
    def test_search_http_error(self, mock_settings, adapter):
        mock_settings.perenual_api_key = "test_key"
        from httpx import HTTPStatusError, Request, Response

        error_response = Response(status_code=429, request=Request("GET", "http://test"))
        error = HTTPStatusError("Rate limited", request=error_response.request, response=error_response)
        adapter._client.get.return_value = MagicMock(
            raise_for_status=MagicMock(side_effect=error)
        )

        with pytest.raises(ExternalSourceError):
            adapter.search_species("Rosa")


class TestGetSpeciesById:
    @patch("app.data_access.external.perenual_adapter.settings")
    def test_get_species_success(self, mock_settings, adapter):
        mock_settings.perenual_api_key = "test_key"
        response = MagicMock()
        response.json.return_value = PERENUAL_DETAILS_RESPONSE
        response.raise_for_status.return_value = None
        adapter._client.get.return_value = response

        result = adapter.get_species_by_id("100")

        assert result is not None
        assert result.external_id == "100"
        assert result.image_url == ""

    @patch("app.data_access.external.perenual_adapter.settings")
    def test_get_species_no_key(self, mock_settings, adapter):
        mock_settings.perenual_api_key = ""

        result = adapter.get_species_by_id("100")

        assert result is None


class TestGetSpeciesList:
    @patch("app.data_access.external.perenual_adapter.settings")
    def test_list_species(self, mock_settings, adapter):
        mock_settings.perenual_api_key = "test_key"
        response = MagicMock()
        response.json.return_value = PERENUAL_SEARCH_RESPONSE
        response.raise_for_status.return_value = None
        adapter._client.get.return_value = response

        results, total = adapter.get_species_list(page=1)

        assert len(results) == 1
        assert total == 1


class TestHealthCheck:
    @patch("app.data_access.external.perenual_adapter.settings")
    def test_healthy(self, mock_settings, adapter):
        mock_settings.perenual_api_key = "test_key"
        response = MagicMock()
        response.status_code = 200
        adapter._client.get.return_value = response

        assert adapter.health_check() is True

    @patch("app.data_access.external.perenual_adapter.settings")
    def test_no_api_key(self, mock_settings, adapter):
        mock_settings.perenual_api_key = ""

        assert adapter.health_check() is False


class TestHelpers:
    def test_extract_genus(self):
        assert _extract_genus("Rosa canina") == "Rosa"
        assert _extract_genus("Solanum") == "Solanum"
        assert _extract_genus("") == ""

    def test_parse_hardiness_with_data(self):
        assert _parse_hardiness({"min": "5", "max": "9"}) == ["5", "9"]

    def test_parse_hardiness_same_zone(self):
        assert _parse_hardiness({"min": "7", "max": "7"}) == ["7"]

    def test_parse_hardiness_empty(self):
        assert _parse_hardiness(None) == []
        assert _parse_hardiness({}) == []
