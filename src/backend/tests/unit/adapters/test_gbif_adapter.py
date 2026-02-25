"""Unit tests for GBIF adapter with mocked HTTP responses."""

from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ExternalSourceError, RateLimitError
from app.data_access.external.gbif_adapter import GBIFAdapter


@pytest.fixture
def adapter():
    a = GBIFAdapter()
    a._client = MagicMock()
    return a


GBIF_SEARCH_RESPONSE = {
    "results": [
        {
            "key": 12345,
            "scientificName": "Rosa canina L.",
            "canonicalName": "Rosa canina",
            "vernacularName": "Dog Rose",
            "genus": "Rosa",
            "family": "Rosaceae",
            "habitat": "Hedgerows",
            "authorship": "L.",
            "taxonomicStatus": "ACCEPTED",
        },
        {
            "key": 67890,
            "scientificName": "Rosa rugosa Thunb.",
            "canonicalName": "Rosa rugosa",
            "genus": "Rosa",
            "family": "Rosaceae",
            "authorship": "Thunb.",
            "taxonomicStatus": "ACCEPTED",
        },
    ],
    "count": 2,
}

GBIF_SPECIES_RESPONSE = {
    "key": 12345,
    "scientificName": "Rosa canina L.",
    "canonicalName": "Rosa canina",
    "vernacularName": "Dog Rose",
    "genus": "Rosa",
    "family": "Rosaceae",
    "habitat": "Hedgerows",
    "authorship": "L.",
    "taxonomicStatus": "ACCEPTED",
}

GBIF_MATCH_EXACT_RESPONSE = {
    "usageKey": 5361880,
    "scientificName": "Cannabis sativa L.",
    "canonicalName": "Cannabis sativa",
    "confidence": 99,
    "matchType": "EXACT",
    "status": "ACCEPTED",
    "kingdom": "Plantae",
    "family": "Cannabaceae",
    "genus": "Cannabis",
    "authorship": "L.",
    "rank": "SPECIES",
}

GBIF_MATCH_FUZZY_RESPONSE = {
    "usageKey": 5361880,
    "scientificName": "Cannabis sativa L.",
    "canonicalName": "Cannabis sativa",
    "confidence": 92,
    "matchType": "FUZZY",
    "status": "ACCEPTED",
    "kingdom": "Plantae",
    "family": "Cannabaceae",
    "genus": "Cannabis",
    "authorship": "L.",
    "rank": "SPECIES",
}

GBIF_MATCH_NONE_RESPONSE = {
    "confidence": 0,
    "matchType": "NONE",
}

GBIF_MATCH_SYNONYM_RESPONSE = {
    "usageKey": 9999999,
    "scientificName": "Cannabis indica Lam.",
    "canonicalName": "Cannabis indica",
    "confidence": 98,
    "matchType": "EXACT",
    "status": "SYNONYM",
    "kingdom": "Plantae",
    "family": "Cannabaceae",
    "genus": "Cannabis",
    "authorship": "Lam.",
    "rank": "SPECIES",
    "acceptedUsageKey": 5361880,
    "accepted": "Cannabis sativa L.",
}

GBIF_MATCH_HIGHERRANK_RESPONSE = {
    "usageKey": 2,
    "scientificName": "Cannabis",
    "canonicalName": "Cannabis",
    "confidence": 97,
    "matchType": "HIGHERRANK",
    "status": "ACCEPTED",
    "kingdom": "Plantae",
    "family": "Cannabaceae",
    "genus": "Cannabis",
    "rank": "GENUS",
}

GBIF_SYNONYMS_RESPONSE = {
    "results": [
        {"canonicalName": "Cannabis indica", "scientificName": "Cannabis indica Lam."},
        {"canonicalName": "Cannabis ruderalis", "scientificName": "Cannabis ruderalis Janisch."},
        {"canonicalName": "Cannabis indica", "scientificName": "Cannabis indica var. kafiristanica"},
    ],
}

GBIF_VERNACULAR_RESPONSE = {
    "results": [
        {"vernacularName": "Hanf", "language": "deu"},
        {"vernacularName": "Hemp", "language": "eng"},
        {"vernacularName": "Canapa", "language": "ita"},
        {"vernacularName": "Hanf", "language": "deu"},
    ],
}

GBIF_DESCRIPTIONS_RESPONSE = {
    "results": [
        {"type": "", "description": "Annual herb growing to 3m tall."},
        {"type": "", "description": "Short description."},
        {"type": "native range", "description": "Central Asia"},
        {"type": "native range", "description": "South Asia"},
        {"type": "eunis habitat", "description": "I1.5"},
    ],
}


def _mock_response(data, status_code=200):
    response = MagicMock()
    response.json.return_value = data
    response.status_code = status_code
    response.raise_for_status.return_value = None
    return response


class TestSearchSpecies:
    def test_search_returns_mapped_results(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_SEARCH_RESPONSE)

        results = adapter.search_species("Rosa")

        assert len(results) == 2
        assert results[0].external_id == "12345"
        assert results[0].scientific_name == "Rosa canina"
        assert results[0].common_names == ["Dog Rose"]
        assert results[0].genus == "Rosa"
        assert results[0].family_name == "Rosaceae"
        assert results[0].taxonomic_authority == "L."
        assert results[0].taxonomic_status == "ACCEPTED"

    def test_search_sends_rank_and_dataset_params(self, adapter):
        adapter._client.get.return_value = _mock_response({"results": [], "count": 0})

        adapter.search_species("Rosa")

        call_kwargs = adapter._client.get.call_args
        params = call_kwargs.kwargs.get("params", call_kwargs[1].get("params", {}))
        assert params["rank"] == "SPECIES"
        assert "datasetKey" in params

    def test_search_empty_results(self, adapter):
        adapter._client.get.return_value = _mock_response({"results": [], "count": 0})

        results = adapter.search_species("Nonexistent")

        assert results == []

    def test_search_filters_no_scientific_name(self, adapter):
        adapter._client.get.return_value = _mock_response({
            "results": [{"key": 1}, {"key": 2, "scientificName": "Valid sp"}],
            "count": 2,
        })

        results = adapter.search_species("test")

        assert len(results) == 1

    def test_search_http_error(self, adapter):
        from httpx import HTTPStatusError, Request, Response

        error_response = Response(status_code=500, request=Request("GET", "http://test"))
        error = HTTPStatusError("Server Error", request=error_response.request, response=error_response)
        adapter._client.get.return_value = MagicMock(
            raise_for_status=MagicMock(side_effect=error)
        )

        with pytest.raises(ExternalSourceError):
            adapter.search_species("Rosa")


class TestGetSpeciesById:
    def test_get_species_success(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_SPECIES_RESPONSE)

        result = adapter.get_species_by_id("12345")

        assert result is not None
        assert result.external_id == "12345"
        assert result.scientific_name == "Rosa canina"

    def test_get_species_no_scientific_name(self, adapter):
        adapter._client.get.return_value = _mock_response({"key": 12345})

        result = adapter.get_species_by_id("12345")

        assert result is None

    def test_get_species_404(self, adapter):
        adapter._client.get.return_value = _mock_response({}, status_code=404)

        result = adapter.get_species_by_id("99999")

        assert result is None


class TestGetSpeciesList:
    def test_list_species(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_SEARCH_RESPONSE)

        results, total = adapter.get_species_list(page=1, per_page=30)

        assert len(results) == 2
        assert total == 2

    def test_list_sends_filter_params(self, adapter):
        adapter._client.get.return_value = _mock_response({"results": [], "count": 0})

        adapter.get_species_list(page=1, per_page=30)

        call_kwargs = adapter._client.get.call_args
        params = call_kwargs.kwargs.get("params", call_kwargs[1].get("params", {}))
        assert params["rank"] == "SPECIES"
        assert params["status"] == "ACCEPTED"
        assert "datasetKey" in params
        assert "highertaxonKey" in params


class TestHealthCheck:
    def test_healthy(self, adapter):
        response = MagicMock()
        response.status_code = 200
        adapter._client.get.return_value = response

        assert adapter.health_check() is True

        call_args = adapter._client.get.call_args
        assert "/species/match" in call_args[0][0]

    def test_unhealthy(self, adapter):
        from httpx import Request, RequestError

        adapter._client.get.side_effect = RequestError("Connection failed", request=Request("GET", "http://test"))

        assert adapter.health_check() is False


class TestMatchSpecies:
    def test_exact_match(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_MATCH_EXACT_RESPONSE)

        result = adapter.match_species("Cannabis sativa")

        assert result is not None
        assert result.usage_key == 5361880
        assert result.scientific_name == "Cannabis sativa L."
        assert result.canonical_name == "Cannabis sativa"
        assert result.confidence == 99
        assert result.match_type == "EXACT"
        assert result.taxonomic_status == "ACCEPTED"
        assert result.family == "Cannabaceae"
        assert result.authorship == "L."

    def test_fuzzy_match(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_MATCH_FUZZY_RESPONSE)

        result = adapter.match_species("Canabis sativa")

        assert result is not None
        assert result.match_type == "FUZZY"
        assert result.confidence == 92

    def test_none_match(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_MATCH_NONE_RESPONSE)

        result = adapter.match_species("Fiktivus nonexistens")

        assert result is None

    def test_synonym_detection(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_MATCH_SYNONYM_RESPONSE)

        result = adapter.match_species("Cannabis indica")

        assert result is not None
        assert result.taxonomic_status == "SYNONYM"
        assert result.accepted_key == 5361880
        assert result.accepted_name == "Cannabis sativa L."

    def test_rate_limit_429(self, adapter):
        response = MagicMock()
        response.status_code = 429
        adapter._client.get.return_value = response

        with pytest.raises(RateLimitError) as exc_info:
            adapter.match_species("Cannabis sativa")

        assert exc_info.value.retry_after == 60


class TestResolveSynonyms:
    def test_returns_deduplicated_names(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_SYNONYMS_RESPONSE)

        result = adapter.resolve_synonyms(5361880)

        assert result == ["Cannabis indica", "Cannabis ruderalis"]

    def test_empty_results(self, adapter):
        adapter._client.get.return_value = _mock_response({"results": []})

        result = adapter.resolve_synonyms(5361880)

        assert result == []

    def test_api_error_graceful(self, adapter):
        from httpx import Request, RequestError

        adapter._client.get.side_effect = RequestError("Timeout", request=Request("GET", "http://test"))

        result = adapter.resolve_synonyms(5361880)

        assert result == []


class TestGetVernacularNames:
    def test_filters_by_language(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_VERNACULAR_RESPONSE)

        result = adapter.get_vernacular_names(5361880)

        assert "Hanf" in result
        assert "Hemp" in result
        assert "Canapa" not in result

    def test_deduplication(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_VERNACULAR_RESPONSE)

        result = adapter.get_vernacular_names(5361880)

        assert result.count("Hanf") == 1

    def test_empty_results(self, adapter):
        adapter._client.get.return_value = _mock_response({"results": []})

        result = adapter.get_vernacular_names(5361880)

        assert result == []

    def test_api_error_graceful(self, adapter):
        from httpx import Request, RequestError

        adapter._client.get.side_effect = RequestError("Timeout", request=Request("GET", "http://test"))

        result = adapter.get_vernacular_names(5361880)

        assert result == []


class TestGetDescriptions:
    def test_categorization(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_DESCRIPTIONS_RESPONSE)

        description, native_habitat = adapter.get_descriptions(5361880)

        assert description == "Annual herb growing to 3m tall."
        assert "Central Asia" in native_habitat
        assert "South Asia" in native_habitat

    def test_html_to_markdown(self, adapter):
        adapter._client.get.return_value = _mock_response({
            "results": [
                {"type": "", "description": "<p>A <strong>tall</strong> herb.</p>"},
            ]
        })

        description, _ = adapter.get_descriptions(5361880)

        assert "<p>" not in description
        assert "<strong>" not in description

    def test_length_limit(self, adapter):
        long_text = "A" * 3000
        adapter._client.get.return_value = _mock_response({
            "results": [
                {"type": "", "description": long_text},
            ]
        })

        description, _ = adapter.get_descriptions(5361880)

        assert len(description) <= 2000
        assert description.endswith("...")

    def test_graceful_degradation(self, adapter):
        from httpx import Request, RequestError

        adapter._client.get.side_effect = RequestError("Timeout", request=Request("GET", "http://test"))

        description, native_habitat = adapter.get_descriptions(5361880)

        assert description == ""
        assert native_habitat == ""

    def test_ignores_eunis_habitat(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_DESCRIPTIONS_RESPONSE)

        description, native_habitat = adapter.get_descriptions(5361880)

        assert "I1.5" not in description
        assert "I1.5" not in native_habitat


class TestEnrichSpecies:
    def test_full_flow(self, adapter):
        """Test complete enrichment: match → synonyms → vernacular → descriptions."""
        call_count = 0

        def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "/species/match" in url:
                return _mock_response(GBIF_MATCH_EXACT_RESPONSE)
            elif "/synonyms" in url:
                return _mock_response(GBIF_SYNONYMS_RESPONSE)
            elif "/vernacularNames" in url:
                return _mock_response(GBIF_VERNACULAR_RESPONSE)
            elif "/descriptions" in url:
                return _mock_response(GBIF_DESCRIPTIONS_RESPONSE)
            return _mock_response({})

        adapter._client.get.side_effect = mock_get

        result = adapter.enrich_species("Cannabis sativa")

        assert result is not None
        assert result.external_id == "5361880"
        assert result.genus == "Cannabis"
        assert result.family_name == "Cannabaceae"
        assert result.taxonomic_authority == "L."
        assert result.taxonomic_status == "ACCEPTED"
        assert "Cannabis indica" in result.synonyms
        assert "Hanf" in result.common_names
        assert "Hemp" in result.common_names
        assert "Annual herb" in result.description
        assert "Central Asia" in result.native_habitat

    def test_none_match_returns_none(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_MATCH_NONE_RESPONSE)

        result = adapter.enrich_species("Fiktivus nonexistens")

        assert result is None

    def test_higherrank_returns_none(self, adapter):
        adapter._client.get.return_value = _mock_response(GBIF_MATCH_HIGHERRANK_RESPONSE)

        result = adapter.enrich_species("Cannabis")

        assert result is None

    def test_synonym_redirect(self, adapter):
        """When match is SYNONYM, usage_key should redirect to accepted taxon."""
        empty_response = _mock_response({"results": []})

        def mock_get(url, **kwargs):
            if "/species/match" in url:
                return _mock_response(GBIF_MATCH_SYNONYM_RESPONSE)
            if "/synonyms" in url or "/vernacularNames" in url or "/descriptions" in url:
                return empty_response
            return _mock_response({})

        adapter._client.get.side_effect = mock_get

        result = adapter.enrich_species("Cannabis indica")

        assert result is not None
        # usage_key should be the accepted key (5361880), not the synonym key (9999999)
        assert result.external_id == "5361880"
        assert result.taxonomic_status == "SYNONYM"

    def test_incremental_rejects_low_fuzzy(self, adapter):
        """Incremental sync rejects FUZZY match below 95."""
        adapter._client.get.return_value = _mock_response(GBIF_MATCH_FUZZY_RESPONSE)  # confidence=92

        result = adapter.enrich_species("Canabis sativa", full_sync=False)

        assert result is None

    def test_full_sync_accepts_lower_fuzzy(self, adapter):
        """Full sync accepts FUZZY match at 92 (>=90 threshold)."""
        empty_response = _mock_response({"results": []})

        def mock_get(url, **kwargs):
            if "/species/match" in url:
                return _mock_response(GBIF_MATCH_FUZZY_RESPONSE)  # confidence=92
            if "/synonyms" in url or "/vernacularNames" in url or "/descriptions" in url:
                return empty_response
            return _mock_response({})

        adapter._client.get.side_effect = mock_get

        result = adapter.enrich_species("Canabis sativa", full_sync=True)

        assert result is not None
