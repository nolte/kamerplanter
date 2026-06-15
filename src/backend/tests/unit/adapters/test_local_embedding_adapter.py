"""Unit tests for REQ-029-A §3.4 LocalEmbeddingAdapter (WS-3)."""

from unittest.mock import AsyncMock

import pytest

from app.data_access.external.local_embedding_adapter import LocalEmbeddingAdapter
from app.domain.models.identification import PlantOrgan


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


def test_disabled_reports_unavailable(_disabled):
    adapter = LocalEmbeddingAdapter()
    # Registry availability convention: disabled → empty _api_key.
    assert adapter._api_key == ""


def test_enabled_has_no_key_attribute(_enabled):
    adapter = LocalEmbeddingAdapter()
    # No _api_key attribute → always available (self-hosted).
    assert not hasattr(adapter, "_api_key")


@pytest.mark.asyncio
async def test_identify_maps_match_response(_enabled):
    adapter = LocalEmbeddingAdapter()
    adapter._client.match = AsyncMock(
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

    result = await adapter.identify(b"img", organ=PlantOrgan.LEAF, max_results=5)

    adapter._client.match.assert_awaited_once()
    assert result.is_plant is True
    assert len(result.suggestions) == 2
    top = result.suggestions[0]
    assert top.scientific_name == "Monstera deliciosa"
    assert top.confidence == 0.88
    assert top.external_id == "local:species_monstera"


@pytest.mark.asyncio
async def test_identify_empty_match_is_not_plant(_enabled):
    adapter = LocalEmbeddingAdapter()
    adapter._client.match = AsyncMock(return_value={"suggestions": [], "is_plant": False})

    result = await adapter.identify(b"img")

    assert result.suggestions == []
    assert result.is_plant is False


@pytest.mark.asyncio
async def test_diagnose_not_implemented(_enabled):
    adapter = LocalEmbeddingAdapter()
    with pytest.raises(NotImplementedError):
        await adapter.diagnose(b"img")


@pytest.mark.asyncio
async def test_health_check_false_when_disabled(_disabled):
    adapter = LocalEmbeddingAdapter()
    adapter._client.is_ready = AsyncMock(return_value=True)
    # Disabled short-circuits before the HTTP call.
    assert await adapter.health_check() is False
    adapter._client.is_ready.assert_not_awaited()


@pytest.mark.asyncio
async def test_health_check_delegates_to_service_when_enabled(_enabled):
    adapter = LocalEmbeddingAdapter()
    adapter._client.is_ready = AsyncMock(return_value=True)
    assert await adapter.health_check() is True
    adapter._client.is_ready.assert_awaited_once()
