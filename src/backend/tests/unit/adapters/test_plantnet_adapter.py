"""Unit tests for REQ-029 §3.3 PlantNetAdapter (mocked HTTP)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.data_access.external.plantnet_adapter import PlantNetAdapter
from app.domain.models.identification import PlantOrgan

PLANTNET_RESPONSE = {
    "results": [
        {
            "score": 0.93,
            "species": {
                "scientificNameWithoutAuthor": "Monstera deliciosa",
                "commonNames": ["Swiss Cheese Plant"],
                "family": {"scientificNameWithoutAuthor": "Araceae"},
                "genus": {"scientificNameWithoutAuthor": "Monstera"},
                "gbif": {"id": 2868258},
            },
            "images": [{"url": {"m": "https://example.org/m.jpg"}}],
        },
        {
            "score": 0.04,
            "species": {
                "scientificNameWithoutAuthor": "Monstera adansonii",
                "commonNames": ["Monkey Mask"],
                "family": {"scientificNameWithoutAuthor": "Araceae"},
                "genus": {"scientificNameWithoutAuthor": "Monstera"},
                "gbif": {"id": 2868260},
            },
            "images": [],
        },
    ]
}


@pytest.fixture
def adapter(monkeypatch):
    monkeypatch.setattr("app.data_access.external.plantnet_adapter.settings.plantnet_api_key", "test-key")
    monkeypatch.setattr("app.data_access.external.plantnet_adapter.settings.plantnet_enabled", True)
    # Reset the class-level daily counter between tests.
    PlantNetAdapter._request_date = None
    PlantNetAdapter._request_count = 0
    return PlantNetAdapter()


def _mock_client(response_json: dict) -> MagicMock:
    response = MagicMock()
    response.json.return_value = response_json
    response.raise_for_status = MagicMock()

    client = MagicMock()
    client.post = AsyncMock(return_value=response)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=client)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx


async def test_identify_maps_suggestions(adapter):
    with patch(
        "app.data_access.external.plantnet_adapter.httpx.AsyncClient",
        return_value=_mock_client(PLANTNET_RESPONSE),
    ):
        result = await adapter.identify(b"\xff\xd8jpegbytes", organ=PlantOrgan.LEAF)

    assert result.is_plant is True
    assert len(result.suggestions) == 2
    top = result.suggestions[0]
    assert top.rank == 1
    assert top.scientific_name == "Monstera deliciosa"
    assert top.confidence == pytest.approx(0.93)
    assert top.family == "Araceae"
    assert top.genus == "Monstera"
    assert top.gbif_id == 2868258
    assert top.image_url == "https://example.org/m.jpg"


async def test_identify_increments_daily_counter(adapter):
    with patch(
        "app.data_access.external.plantnet_adapter.httpx.AsyncClient",
        return_value=_mock_client(PLANTNET_RESPONSE),
    ):
        await adapter.identify(b"\xff\xd8jpegbytes")
    assert PlantNetAdapter._remaining_today() == PlantNetAdapter.rate_limit_per_day - 1


async def test_identify_no_results_is_not_plant(adapter):
    with patch(
        "app.data_access.external.plantnet_adapter.httpx.AsyncClient",
        return_value=_mock_client({"results": []}),
    ):
        result = await adapter.identify(b"\xff\xd8jpegbytes")
    assert result.is_plant is False
    assert result.suggestions == []


async def test_diagnose_not_implemented(adapter):
    with pytest.raises(NotImplementedError):
        await adapter.diagnose(b"\xff\xd8jpegbytes")


async def test_health_check_false_without_key(monkeypatch):
    monkeypatch.setattr("app.data_access.external.plantnet_adapter.settings.plantnet_api_key", "")
    monkeypatch.setattr("app.data_access.external.plantnet_adapter.settings.plantnet_enabled", True)
    a = PlantNetAdapter()
    assert await a.health_check() is False


async def test_health_check_true_with_key(adapter):
    assert await adapter.health_check() is True


async def test_disabled_adapter_reports_no_key(monkeypatch):
    monkeypatch.setattr("app.data_access.external.plantnet_adapter.settings.plantnet_api_key", "test-key")
    monkeypatch.setattr("app.data_access.external.plantnet_adapter.settings.plantnet_enabled", False)
    a = PlantNetAdapter()
    assert a._api_key == ""
    assert await a.health_check() is False
