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
    from tests.support.fake_contribution_marker import FakeContributionMarker

    monkeypatch.setattr(settings, "inference_service_enabled", False)
    monkeypatch.setattr(dependencies, "get_system_settings_repo", FakeContributionMarker)

    store = dependencies.get_reference_index_store()

    assert isinstance(store, NoopReferenceIndexStore)
    assert store.binding == "noop"


def test_the_noop_contribution_line_names_no_contributor() -> None:
    """#1989: ``reference_contribution_noop`` logged ``contributed_by=<account key>`` beside ``tenant_key``.

    ``contributed_by`` is the contributor's plaintext account key (the task passes
    ``user_key``), so the line named the subject in clear text next to the raw
    tenant. It now carries neither; the tenant alone names no subject.
    """
    import structlog.testing

    user_key = "contributor-3e8d51"
    with structlog.testing.capture_logs() as logs:
        stored = NoopReferenceIndexStore().add_user_contribution(
            species_key="sp-1",
            scientific_name="Solanum lycopersicum",
            image_data=b"\x89PNG",
            tenant_key="tenant-1",
            contributed_by=user_key,
        )

    assert stored is False
    (line,) = [e for e in logs if e["event"] == "reference_contribution_noop"]
    assert "contributed_by" not in line
    assert user_key not in repr(logs)
