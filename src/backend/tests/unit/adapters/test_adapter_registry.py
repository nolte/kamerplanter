"""Unit tests for the adapter registry."""

from typing import TYPE_CHECKING

import pytest

from app.common.exceptions import AdapterNotFoundError
from app.domain.interfaces.external_source_adapter import ExternalSourceAdapter
from app.domain.services.adapter_registry import AdapterRegistry

if TYPE_CHECKING:
    from app.domain.models.enrichment import ExternalSpeciesData


class DummyAdapter(ExternalSourceAdapter):
    source_key = "dummy"
    rate_limit_per_minute = 10

    def search_species(self, query: str) -> list[ExternalSpeciesData]:
        return []

    def get_species_by_id(self, external_id: str) -> ExternalSpeciesData | None:
        return None

    def get_species_list(self, page: int = 1, per_page: int = 30) -> tuple[list[ExternalSpeciesData], int]:
        return [], 0


class TestAdapterRegistry:
    def setup_method(self):
        self._original = AdapterRegistry._adapters.copy()
        AdapterRegistry.clear()

    def teardown_method(self):
        AdapterRegistry._adapters = self._original

    def test_register_and_get(self):
        AdapterRegistry.register(DummyAdapter)

        adapter = AdapterRegistry.get("dummy")
        assert adapter.source_key == "dummy"

    def test_get_not_found(self):
        with pytest.raises(AdapterNotFoundError):
            AdapterRegistry.get("nonexistent")

    def test_all_keys(self):
        AdapterRegistry.register(DummyAdapter)

        keys = AdapterRegistry.all_keys()
        assert "dummy" in keys

    def test_all_adapters(self):
        AdapterRegistry.register(DummyAdapter)

        adapters = AdapterRegistry.all_adapters()
        assert len(adapters) >= 1
        assert any(a.source_key == "dummy" for a in adapters)

    def test_clear(self):
        AdapterRegistry.register(DummyAdapter)
        AdapterRegistry.clear()

        assert AdapterRegistry.all_keys() == []
