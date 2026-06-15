"""REQ-029-A §0.1.1 point 1 — config-driven adapter priority resolution."""

import pytest

from app.config.settings import settings
from app.domain.interfaces.plant_identification_adapter import (
    HealthAssessment,
    IdentificationResult,
    PlantIdentificationAdapter,
    PlantOrgan,
)
from app.domain.services.identification_registry import IdentificationAdapterRegistry


class _FakeAdapter(PlantIdentificationAdapter):
    adapter_key = "fake"
    supports_health_assessment = False
    rate_limit_per_day = 100

    def __init__(self, configured: bool = True) -> None:
        self._configured = configured

    def is_configured(self) -> bool:
        return self._configured

    def identify(
        self,
        image_data: bytes,
        *,
        organ: PlantOrgan = PlantOrgan.AUTO,
        max_results: int = 5,
        include_health: bool = False,
        language: str = "de",
    ) -> IdentificationResult:
        return IdentificationResult()

    def diagnose(self, image_data: bytes, *, language: str = "de") -> HealthAssessment:
        raise NotImplementedError


def _make(key: str, configured: bool = True) -> _FakeAdapter:
    adapter = _FakeAdapter(configured=configured)
    adapter.adapter_key = key
    return adapter


@pytest.fixture(autouse=True)
def _isolate_registry():
    original = dict(IdentificationAdapterRegistry._adapters)
    original_primary = settings.identification_primary_adapter
    IdentificationAdapterRegistry.clear()
    yield
    IdentificationAdapterRegistry._adapters = original
    settings.identification_primary_adapter = original_primary


def _put(adapter: _FakeAdapter) -> None:
    IdentificationAdapterRegistry._adapters[adapter.adapter_key] = adapter


def test_get_preferred_returns_configured_primary():
    _put(_make("plantnet"))
    _put(_make("local_embedding"))
    settings.identification_primary_adapter = "plantnet"

    preferred = IdentificationAdapterRegistry.get_preferred()
    assert preferred is not None
    assert preferred.adapter_key == "plantnet"


def test_get_preferred_switching_primary_is_pure_config():
    # Phase-2 bridge: registering another adapter + flipping the setting suffices.
    _put(_make("plantnet"))
    _put(_make("local_embedding"))

    settings.identification_primary_adapter = "local_embedding"
    assert IdentificationAdapterRegistry.get_preferred().adapter_key == "local_embedding"

    settings.identification_primary_adapter = "plantnet"
    assert IdentificationAdapterRegistry.get_preferred().adapter_key == "plantnet"


def test_get_preferred_falls_back_when_primary_unconfigured():
    _put(_make("plantnet", configured=False))
    _put(_make("local_embedding", configured=True))
    settings.identification_primary_adapter = "plantnet"

    preferred = IdentificationAdapterRegistry.get_preferred()
    assert preferred is not None
    assert preferred.adapter_key == "local_embedding"


def test_get_preferred_none_when_nothing_configured():
    _put(_make("plantnet", configured=False))
    settings.identification_primary_adapter = "plantnet"

    assert IdentificationAdapterRegistry.get_preferred() is None
    assert IdentificationAdapterRegistry.get_available() == []


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        IdentificationAdapterRegistry.get("does-not-exist")
