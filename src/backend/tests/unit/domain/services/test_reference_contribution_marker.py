"""GDPR-001 / GDPR-002 (#1753) — the no-op reference-index binding cannot stay silent.

The reference-index store is chosen per process from ``inference_service_enabled``.
A process without the flag — the celery-worker that runs the scheduled Art. 17
erasure, or any process after the flag was switched off — bound the no-op store
and reported ``completed`` while the subject's contributed vectors survived.

The repair is a persisted marker, written by the only writer of contributions
*before* its upsert: once contributions may exist, the no-op store refuses to
report "nothing to delete" and says what to configure instead. What is pinned:

* the contribution path records the marker before it writes, and refuses when it
  cannot record it;
* the no-op store raises with an operator-actionable message while the marker is
  set, stays a logged ``0`` without it, and a failed marker read is loud;
* the provider wires the marker into the no-op binding.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common import dependencies
from app.common.exceptions import FeatureNotConfiguredError
from app.config.settings import settings
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.services.reference_image_service import ReferenceImageService
from tests.support.fake_contribution_marker import FakeContributionMarker

SINCE = datetime(2026, 9, 1, tzinfo=UTC)


def _image() -> bytes:
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (64, 64), (10, 120, 60)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _contribution_service(marker, calls: list[str]) -> ReferenceImageService:
    from app.domain.engines.identification_engine import IdentificationEngine

    inference = MagicMock()
    inference.embed.return_value = [0.1] * 4

    def _upsert(**kwargs):
        calls.append("upsert")
        return {"status": "ok", "dim": 4}

    inference.upsert_reference.side_effect = _upsert
    species_repo = MagicMock()
    species_repo.get_or_raise.return_value = SimpleNamespace(key="sp", scientific_name="Genus species")
    if marker is not None:
        original = marker.record_reference_contributions

        def _record(now):
            calls.append("marker")
            return original(now)

        marker.record_reference_contributions = _record
    return ReferenceImageService(
        MagicMock(),
        MagicMock(),
        inference,
        MagicMock(),
        species_repo=species_repo,
        rate_limiter=MagicMock(),
        identification_engine=IdentificationEngine(species_repo=MagicMock(), identification_repo=MagicMock()),
        contribution_marker=marker,
    )


# -- the writer records the marker ------------------------------------------


def test_a_contribution_records_the_marker_before_it_writes():
    marker = FakeContributionMarker()
    calls: list[str] = []
    service = _contribution_service(marker, calls)

    service.contribute_user_reference("sp", _image(), user_key="u", tenant_key="t")

    assert calls == ["marker", "upsert"]
    assert marker.since is not None


def test_a_second_contribution_keeps_the_first_timestamp():
    marker = FakeContributionMarker(since=SINCE)
    service = _contribution_service(marker, [])

    service.contribute_user_reference("sp", _image(), user_key="u", tenant_key="t")

    assert marker.since == SINCE


def test_a_contribution_that_cannot_record_the_marker_writes_nothing():
    marker = FakeContributionMarker()
    marker.fail_writes = True
    calls: list[str] = []
    service = _contribution_service(marker, calls)

    with pytest.raises(ConnectionError):
        service.contribute_user_reference("sp", _image(), user_key="u", tenant_key="t")

    assert "upsert" not in calls


def test_a_contribution_without_a_wired_marker_is_refused():
    calls: list[str] = []
    service = _contribution_service(None, calls)

    with pytest.raises(RuntimeError):
        service.contribute_user_reference("sp", _image(), user_key="u", tenant_key="t")

    assert calls == []


# -- the no-op store reads the marker -------------------------------------------


async def test_noop_with_contributions_on_record_refuses_both_deletes():
    store = NoopReferenceIndexStore(marker=FakeContributionMarker(since=SINCE))

    with pytest.raises(FeatureNotConfiguredError) as user_error:
        await store.delete_user_contributions(tenant_key=None, user_key="user-a")
    with pytest.raises(FeatureNotConfiguredError) as tenant_error:
        await store.delete_tenant_contributions("t-1")

    for caught in (user_error, tenant_error):
        assert "INFERENCE_SERVICE_ENABLED" in str(caught.value)
        assert caught.value.status_code == 503
        assert "user-a" not in str(caught.value) and "t-1" not in str(caught.value)
    assert store.configuration_error() is not None


async def test_noop_without_contributions_on_record_removes_nothing_quietly():
    store = NoopReferenceIndexStore(marker=FakeContributionMarker())

    assert await store.delete_user_contributions(tenant_key=None, user_key="user-a") == 0
    assert await store.delete_tenant_contributions("t-1") == 0
    assert store.configuration_error() is None


async def test_a_failing_marker_read_is_loud():
    marker = FakeContributionMarker()
    marker.fail_reads = True
    store = NoopReferenceIndexStore(marker=marker)

    with pytest.raises(ConnectionError):
        await store.delete_user_contributions(tenant_key=None, user_key="user-a")
    with pytest.raises(ConnectionError):
        await store.delete_tenant_contributions("t-1")


def test_the_provider_wires_the_marker_into_the_noop_binding(monkeypatch):
    marker = FakeContributionMarker(since=SINCE)
    monkeypatch.setattr(settings, "inference_service_enabled", False)
    monkeypatch.setattr(dependencies, "get_system_settings_repo", lambda: marker)

    store = dependencies.get_reference_index_store()

    assert isinstance(store, NoopReferenceIndexStore)
    assert store.configuration_error() is not None
