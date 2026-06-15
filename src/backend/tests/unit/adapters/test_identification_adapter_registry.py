"""Unit tests for REQ-029 §3.4 IdentificationAdapterRegistry."""

import pytest

from app.domain.interfaces.plant_identification_adapter import PlantIdentificationAdapter
from app.domain.models.identification import IdentificationResult
from app.domain.services.identification_adapter_registry import IdentificationAdapterRegistry


class _BaseStub(PlantIdentificationAdapter):
    adapter_key = "base"
    supports_health_assessment = False
    rate_limit_per_day = 100

    async def identify(self, image_data, **kwargs):  # noqa: ANN001, ANN003
        return IdentificationResult()

    async def diagnose(self, image_data, *, language="de"):  # noqa: ANN001
        raise NotImplementedError

    async def health_check(self) -> bool:
        return True


class _LocalStub(_BaseStub):
    """Self-hosted adapter — no API key required, always available."""

    adapter_key = "local_embedding"
    rate_limit_per_day = None

    def __init__(self) -> None:
        pass  # no _api_key attribute → always available


class _KeyedStub(_BaseStub):
    """External adapter — available only when the key is set."""

    adapter_key = "plantnet"

    def __init__(self) -> None:
        self._api_key = "set"


class _UnconfiguredStub(_BaseStub):
    adapter_key = "unconfigured"

    def __init__(self) -> None:
        self._api_key = ""


@pytest.fixture(autouse=True)
def _clean_registry():
    IdentificationAdapterRegistry.clear()
    yield
    IdentificationAdapterRegistry.clear()


def test_register_and_get():
    IdentificationAdapterRegistry.register(_KeyedStub)
    adapter = IdentificationAdapterRegistry.get("plantnet")
    assert adapter.adapter_key == "plantnet"


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        IdentificationAdapterRegistry.get("nope")


def test_get_available_excludes_unconfigured():
    IdentificationAdapterRegistry.register(_KeyedStub)
    IdentificationAdapterRegistry.register(_UnconfiguredStub)
    keys = {a.adapter_key for a in IdentificationAdapterRegistry.get_available()}
    assert keys == {"plantnet"}


def test_local_adapter_available_without_key():
    IdentificationAdapterRegistry.register(_LocalStub)
    keys = {a.adapter_key for a in IdentificationAdapterRegistry.get_available()}
    assert keys == {"local_embedding"}


def test_get_preferred_respects_primary_setting(monkeypatch):
    IdentificationAdapterRegistry.register(_KeyedStub)
    IdentificationAdapterRegistry.register(_LocalStub)
    monkeypatch.setattr(
        "app.domain.services.identification_adapter_registry.settings.identification_primary_adapter",
        "local_embedding",
    )
    preferred = IdentificationAdapterRegistry.get_preferred()
    assert preferred is not None
    assert preferred.adapter_key == "local_embedding"


def test_get_preferred_falls_back_to_first_when_primary_unavailable(monkeypatch):
    # Primary set to a not-registered adapter → first available wins.
    IdentificationAdapterRegistry.register(_KeyedStub)
    monkeypatch.setattr(
        "app.domain.services.identification_adapter_registry.settings.identification_primary_adapter",
        "local_embedding",
    )
    preferred = IdentificationAdapterRegistry.get_preferred()
    assert preferred is not None
    assert preferred.adapter_key == "plantnet"


def test_get_preferred_none_when_nothing_available():
    IdentificationAdapterRegistry.register(_UnconfiguredStub)
    assert IdentificationAdapterRegistry.get_preferred() is None


def test_fallback_chain_orders_preferred_first(monkeypatch):
    IdentificationAdapterRegistry.register(_KeyedStub)
    IdentificationAdapterRegistry.register(_LocalStub)
    monkeypatch.setattr(
        "app.domain.services.identification_adapter_registry.settings.identification_primary_adapter",
        "local_embedding",
    )
    chain = [a.adapter_key for a in IdentificationAdapterRegistry.get_fallback_chain()]
    assert chain[0] == "local_embedding"
    assert set(chain) == {"local_embedding", "plantnet"}
