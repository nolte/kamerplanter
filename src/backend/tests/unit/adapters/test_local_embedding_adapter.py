"""Unit tests for REQ-029-A §3.4 LocalEmbeddingAdapter.

Synchronous adapter against the REQ-029 PlantIdentificationAdapter interface,
registered with the shared IdentificationAdapterRegistry.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.external.local_embedding_adapter import LocalEmbeddingAdapter
from app.domain.interfaces.plant_identification_adapter import PlantOrgan


@pytest.fixture
def _enabled(monkeypatch):
    monkeypatch.setattr(
        "app.data_access.external.local_embedding_adapter.settings.inference_service_enabled",
        True,
    )


@pytest.fixture
def _disabled(monkeypatch):
    monkeypatch.setattr(
        "app.data_access.external.local_embedding_adapter.settings.inference_service_enabled",
        False,
    )


def test_metadata():
    assert LocalEmbeddingAdapter.adapter_key == "local_embedding"
    assert LocalEmbeddingAdapter.supports_health_assessment is False
    assert LocalEmbeddingAdapter.rate_limit_per_day is None


def test_is_configured_follows_enabled_flag(_enabled):
    assert LocalEmbeddingAdapter().is_configured() is True


def test_is_configured_false_when_disabled(_disabled):
    assert LocalEmbeddingAdapter().is_configured() is False


def test_identify_maps_match_response(_enabled):
    adapter = LocalEmbeddingAdapter()
    adapter._client.match = MagicMock(
        return_value={
            "suggestions": [
                {
                    "rank": 1,
                    "species_key": "species_monstera",
                    "scientific_name": "Monstera deliciosa",
                    "score": 0.91,
                    "confidence": 0.88,
                },
                {
                    "rank": 2,
                    "species_key": "species_ficus",
                    "scientific_name": "Ficus lyrata",
                    "score": 0.40,
                    "confidence": 0.35,
                },
            ],
            "is_plant": True,
            "model": "dinov2_vits14",
        }
    )

    result = adapter.identify(b"img", organ=PlantOrgan.LEAF, max_results=5)

    adapter._client.match.assert_called_once()
    assert result.is_plant is True
    assert len(result.suggestions) == 2
    top = result.suggestions[0]
    assert top.scientific_name == "Monstera deliciosa"
    assert top.confidence == 0.88
    assert top.external_id == "local:species_monstera"


def test_identify_empty_match_is_not_plant(_enabled):
    adapter = LocalEmbeddingAdapter()
    adapter._client.match = MagicMock(return_value={"suggestions": [], "is_plant": False})

    result = adapter.identify(b"img")

    assert result.suggestions == []
    assert result.is_plant is False


def test_diagnose_not_implemented(_enabled):
    adapter = LocalEmbeddingAdapter()
    with pytest.raises(NotImplementedError):
        adapter.diagnose(b"img")


def test_health_check_false_when_disabled(_disabled):
    adapter = LocalEmbeddingAdapter()
    adapter._client.is_ready = MagicMock(return_value=True)
    # Disabled short-circuits before the HTTP call.
    assert adapter.health_check() is False
    adapter._client.is_ready.assert_not_called()


def test_health_check_delegates_when_enabled(_enabled):
    adapter = LocalEmbeddingAdapter()
    adapter._client.is_ready = MagicMock(return_value=True)
    assert adapter.health_check() is True
    adapter._client.is_ready.assert_called_once()
