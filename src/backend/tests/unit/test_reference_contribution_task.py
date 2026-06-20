"""REQ-034 §4 — guards of the DINOv2 user-reference contribution hook.

Tests the pure guard logic in ``_evaluate`` against patched DI providers, so no
broker / inference service / DB is needed. The Celery wrapper itself is a thin
retry shell around ``_evaluate``.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import app.tasks.reference_contribution_tasks as task_mod
from app.domain.models.plant_instance import PlantInstance
from app.domain.models.privacy import ConsentRecord

ATT = "att1"
PLANT = "plant1"
TENANT = "tenant_anna"
USER = "user_anna"


def _plant(species_key: str = "species1") -> PlantInstance:
    return PlantInstance(
        _key=PLANT,
        tenant_key=TENANT,
        instance_id="P-1",
        species_key=species_key,
        planted_on=date(2026, 6, 1),
    )


def _consent(granted: bool) -> ConsentRecord:
    return ConsentRecord(
        _key="c1",
        user_key=USER,
        purpose="reference_contribution",
        granted=granted,
    )


def _wire(
    monkeypatch,
    *,
    inference_enabled: bool = True,
    mode: str = "full",
    consent: ConsentRecord | None = None,
    plant: PlantInstance | None = None,
    species=MagicMock(scientific_name="Monstera deliciosa"),
    pending: int = 0,
    pending_limit: int = 100,
    store=None,
):
    settings = MagicMock()
    settings.inference_service_enabled = inference_enabled
    settings.kamerplanter_mode = mode
    settings.reference_contribution_pending_limit = pending_limit
    monkeypatch.setattr(task_mod, "settings", settings)

    consent_repo = MagicMock()
    consent_repo.get_by_user_and_purpose.return_value = consent
    monkeypatch.setattr(task_mod, "get_consent_repo", lambda: consent_repo)

    # Real ConsentEngine — exercises the actual is_processing_allowed logic.
    from app.domain.engines.consent_engine import ConsentEngine

    monkeypatch.setattr(task_mod, "get_consent_engine", ConsentEngine)

    plant_repo = MagicMock()
    plant_repo.get_by_key.return_value = plant if plant is not None else _plant()
    monkeypatch.setattr(task_mod, "get_plant_repo", lambda: plant_repo)

    species_repo = MagicMock()
    species_repo.get_by_key.return_value = species
    monkeypatch.setattr(task_mod, "get_species_repo", lambda: species_repo)

    if store is None:
        store = MagicMock()
        store.count_pending_contributions.return_value = pending
        store.add_user_contribution.return_value = True
    monkeypatch.setattr(task_mod, "get_reference_index_store", lambda: store)

    att_service = MagicMock()
    att_service.get_attachment.return_value = MagicMock()

    async def _open_stream(_att):
        async def _gen():
            yield b"imagebytes"

        return _gen()

    att_service.open_stream.side_effect = _open_stream
    monkeypatch.setattr(task_mod, "get_attachment_service", lambda: att_service)
    return store


def _run(monkeypatch, **kw):
    store = _wire(monkeypatch, **kw)
    outcome = task_mod._evaluate(ATT, PLANT, TENANT, USER)
    return outcome, store


class TestGuards:
    def test_guard1_inference_disabled_is_noop(self, monkeypatch):
        outcome, store = _run(monkeypatch, inference_enabled=False)
        assert outcome["status"] == "noop"
        assert outcome["reason"] == "inference_service_disabled"
        store.add_user_contribution.assert_not_called()

    def test_guard2_light_mode_aborts(self, monkeypatch):
        outcome, store = _run(monkeypatch, mode="light", consent=_consent(True))
        assert outcome["status"] == "abort"
        assert outcome["reason"] == "light_mode"
        store.add_user_contribution.assert_not_called()

    def test_guard3_no_consent_aborts(self, monkeypatch):
        outcome, store = _run(monkeypatch, consent=None)
        assert outcome == {"status": "abort", "reason": "no_consent"}
        store.add_user_contribution.assert_not_called()

    def test_guard3_revoked_consent_aborts(self, monkeypatch):
        outcome, _store = _run(monkeypatch, consent=_consent(False))
        assert outcome["reason"] == "no_consent"

    def test_guard4_missing_species_aborts(self, monkeypatch):
        outcome, _store = _run(monkeypatch, consent=_consent(True), plant=_plant(species_key=""))
        assert outcome["reason"] == "no_species"

    def test_guard4_unknown_species_aborts(self, monkeypatch):
        outcome, _store = _run(monkeypatch, consent=_consent(True), species=None)
        assert outcome["reason"] == "species_not_found"

    def test_guard5_backlog_full_aborts(self, monkeypatch):
        outcome, store = _run(monkeypatch, consent=_consent(True), pending=100, pending_limit=100)
        assert outcome["reason"] == "pending_backlog_full"
        store.add_user_contribution.assert_not_called()

    def test_happy_path_stores_contribution(self, monkeypatch):
        outcome, store = _run(monkeypatch, consent=_consent(True), pending=3)
        assert outcome["status"] == "stored"
        store.add_user_contribution.assert_called_once()
        _, kwargs = store.add_user_contribution.call_args
        assert kwargs["tenant_key"] == TENANT
        assert kwargs["contributed_by"] == USER
        assert kwargs["species_key"] == "species1"
        assert kwargs["image_data"] == b"imagebytes"

    def test_noop_store_reports_noop(self, monkeypatch):
        # A wired-but-no-op store (Phase 1) returns False → status noop.
        store = MagicMock()
        store.count_pending_contributions.return_value = 0
        store.add_user_contribution.return_value = False
        outcome, _store = _run(monkeypatch, consent=_consent(True), store=store)
        assert outcome == {"status": "noop", "reason": "reference_store_noop"}


class TestNoopStoreIntegration:
    def test_real_noop_store_full_path(self, monkeypatch):
        from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore

        outcome, _store = _run(monkeypatch, consent=_consent(True), store=NoopReferenceIndexStore())
        # is_active=False curation gate is honoured by the real no-op store: it
        # persists nothing and reports a clean no-op.
        assert outcome == {"status": "noop", "reason": "reference_store_noop"}
