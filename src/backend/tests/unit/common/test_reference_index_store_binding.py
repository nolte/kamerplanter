"""Issue #1753 — ``get_reference_index_store`` binds the store the product writes to.

Contributions reach the reference index only while
``settings.inference_service_enabled`` is set (the router refuses otherwise), so
the erasure must bind the inference-service store in exactly that case. Before
#1753 the provider returned the no-op store unconditionally.
"""

from __future__ import annotations

from app.common import dependencies
from app.config.settings import settings
from app.data_access.vectordb.inference_reference_index_store import InferenceServiceReferenceIndexStore
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore


def test_enabled_inference_service_binds_the_real_store(monkeypatch):
    monkeypatch.setattr(settings, "inference_service_enabled", True)
    monkeypatch.setattr(settings, "inference_service_url", "http://recognition.test:8000")

    store = dependencies.get_reference_index_store()

    assert isinstance(store, InferenceServiceReferenceIndexStore)
    assert store.binding == "inference_service"
    assert store._client._base_url == "http://recognition.test:8000"


def test_disabled_inference_service_binds_the_noop_store(monkeypatch):
    monkeypatch.setattr(settings, "inference_service_enabled", False)

    store = dependencies.get_reference_index_store()

    assert isinstance(store, NoopReferenceIndexStore)
    assert store.binding == "noop"
