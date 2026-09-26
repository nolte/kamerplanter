"""Issue #1753 — the inference-service-backed reference-index store.

The erasure pipeline (REQ-025 Phase 0.5) and the tenant deletion call this
store; before #1753 they were bound to a no-op and a user's contributed vectors
outlived the account. What is pinned:

* both deletes reach the inference-service and return its count;
* every failure raises (fail-loud) as an :class:`ExternalSourceError` whose text
  names neither the user key nor the tenant key — the erasure writes that text
  into its retained record and its log lines (#1700);
* the gallery-hook write path stays inert (REQ-034 §4 is not activated here).
"""

from __future__ import annotations

import json
import logging

import pytest
import structlog.testing

from app.common.exceptions import ExternalSourceError
from app.data_access.external.inference_service_client import InferenceServiceClient
from app.data_access.vectordb.inference_reference_index_store import InferenceServiceReferenceIndexStore
from app.data_access.vectordb.noop_reference_index_store import NoopReferenceIndexStore
from app.domain.interfaces.reference_index_store import IReferenceIndexStore
from tests.support.fake_inference_service import FakeInferenceService, route_httpx_post_to

TOKEN = "svc-token"
SUBJECT = "user-subject-4711"
TENANT = "tenant-0815"


@pytest.fixture
def service(monkeypatch) -> FakeInferenceService:
    fake = FakeInferenceService(token=TOKEN)
    fake.add(source="user_contributed", contributed_by=SUBJECT, tenant_key=TENANT, record="subject")
    fake.add(source="user_contributed", contributed_by="other", tenant_key=TENANT, record="other")
    fake.add(source="user_contributed", contributed_by="other", tenant_key="t-else", record="other-else")
    fake.add(source="wikimedia", contributed_by=SUBJECT, tenant_key=TENANT, record="curated")
    route_httpx_post_to(monkeypatch, fake)
    return fake


def _store() -> InferenceServiceReferenceIndexStore:
    return InferenceServiceReferenceIndexStore(InferenceServiceClient("http://inference:8000", service_token=TOKEN))


def test_bindings_are_named():
    assert IReferenceIndexStore.binding == "unbound"
    assert NoopReferenceIndexStore.binding == "noop"
    assert InferenceServiceReferenceIndexStore.binding == "inference_service"


async def test_user_delete_reaches_the_service(service):
    removed = await _store().delete_user_contributions(tenant_key=None, user_key=SUBJECT)

    assert removed == 1
    assert service.records() == {"other", "other-else", "curated"}


async def test_user_delete_scoped_to_a_tenant_passes_the_scope(service):
    removed = await _store().delete_user_contributions(tenant_key="t-else", user_key=SUBJECT)

    assert removed == 0
    assert json.loads(service.requests[0].content)["tenant_key"] == "t-else"
    assert "subject" in service.records()


async def test_tenant_delete_reaches_the_service(service):
    removed = await _store().delete_tenant_contributions(TENANT)

    assert removed == 2
    assert service.records() == {"other-else", "curated"}


@pytest.mark.parametrize("status", [401, 422, 500, 503])
async def test_a_failed_user_delete_raises_without_naming_the_subject(service, status):
    service.failure_status = status

    with pytest.raises(ExternalSourceError) as caught:
        await _store().delete_user_contributions(tenant_key=TENANT, user_key=SUBJECT)

    assert str(status) in str(caught.value)
    assert SUBJECT not in str(caught.value)
    assert TENANT not in str(caught.value)
    assert caught.value.status_code == 502


async def test_a_failed_tenant_delete_raises_without_naming_the_tenant(service):
    service.failure_status = 503

    with pytest.raises(ExternalSourceError) as caught:
        await _store().delete_tenant_contributions(TENANT)

    assert TENANT not in str(caught.value)


async def test_an_unreachable_service_raises(monkeypatch):
    import httpx

    from app.data_access.external import inference_service_client as module

    def _refuse(url, **kwargs):
        raise httpx.ConnectError(f"connection refused: {url}")

    monkeypatch.setattr(module.httpx, "post", _refuse)

    with pytest.raises(ExternalSourceError) as caught:
        await _store().delete_user_contributions(tenant_key=None, user_key=SUBJECT)
    assert SUBJECT not in str(caught.value)
    assert "ConnectError" in str(caught.value)


async def test_no_log_record_carries_the_keys(service, caplog):
    """SEC-001 — every hop's request log must be free of the user and tenant key.

    httpx logs each request line at INFO (``HTTP Request: POST <url> ...``);
    before SEC-001 the URL carried the key. Captured at DEBUG on the root
    logger, plus structlog, so a new log line anywhere on the path is covered.
    """
    caplog.set_level(logging.DEBUG)
    # ``setup_logging`` holds httpx at WARNING (#1795) and runs when ``app.main`` is
    # imported (#1832) — by any earlier test in the session. Lower it for this probe.
    caplog.set_level(logging.DEBUG, logger="httpx")
    store = _store()

    with structlog.testing.capture_logs() as events:
        await store.delete_user_contributions(tenant_key=TENANT, user_key=SUBJECT)
        await store.delete_user_contributions(tenant_key=None, user_key=SUBJECT)
        await store.delete_tenant_contributions(TENANT)

    assert any(record.name == "httpx" for record in caplog.records), "httpx request log not captured"
    for record in caplog.records:
        text = record.getMessage()
        assert SUBJECT not in text and TENANT not in text, text
    for event in events:
        assert not any(SUBJECT in str(v) or TENANT in str(v) for v in event.values()), event


def test_the_gallery_hook_stays_inert(service):
    """REQ-034 §4 is out of scope: the hook's write path must not start writing."""
    store = _store()

    assert store.count_pending_contributions(TENANT) == 0
    assert (
        store.add_user_contribution(
            species_key="sp",
            scientific_name="Genus species",
            image_data=b"\xff\xd8",
            tenant_key=TENANT,
            contributed_by=SUBJECT,
        )
        is False
    )
    assert service.requests == []
