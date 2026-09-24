"""Issue #1753 — the inference-service client's contribution-erasure calls.

Driven through the real client over an ``httpx.MockTransport`` that behaves like
the service (auth, blank-key refusal, ``source`` bound), so URL encoding,
headers, ``raise_for_status`` and the response decode are the production ones.
"""

from __future__ import annotations

import httpx
import pytest

from app.data_access.external.inference_service_client import InferenceServiceClient
from tests.support.fake_inference_service import FakeInferenceService, route_httpx_delete_to

TOKEN = "svc-token"


@pytest.fixture
def service(monkeypatch) -> FakeInferenceService:
    fake = FakeInferenceService(token=TOKEN)
    fake.add(source="user_contributed", contributed_by="user-a", tenant_key="t-1", record="a-t1")
    fake.add(source="user_contributed", contributed_by="user-a", tenant_key="t-2", record="a-t2")
    fake.add(source="user_contributed", contributed_by="user-b", tenant_key="t-1", record="b-t1")
    fake.add(source="gbif", contributed_by="user-a", tenant_key="t-1", record="curated")
    route_httpx_delete_to(monkeypatch, fake)
    return fake


def _client() -> InferenceServiceClient:
    return InferenceServiceClient("http://inference:8000/", service_token=TOKEN)


def test_delete_user_contributions_removes_the_users_rows_and_returns_the_count(service):
    assert _client().delete_user_contributions("user-a") == 2
    assert service.records() == {"b-t1", "curated"}
    (request,) = service.requests
    assert request.method == "DELETE"
    assert request.url.path == "/reference/contributions/by-contributor/user-a"
    assert "tenant_key" not in request.url.params
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"


def test_delete_user_contributions_scoped_to_a_tenant(service):
    assert _client().delete_user_contributions("user-a", tenant_key="t-2") == 1
    assert service.records() == {"a-t1", "b-t1", "curated"}
    assert service.requests[0].url.params["tenant_key"] == "t-2"


def test_delete_tenant_contributions(service):
    assert _client().delete_tenant_contributions("t-1") == 2
    assert service.records() == {"a-t2", "curated"}
    assert service.requests[0].url.path == "/reference/contributions/by-tenant/t-1"


def test_a_key_is_one_encoded_path_segment(service):
    service.add(source="user_contributed", contributed_by="odd/key ?#", tenant_key="t-9", record="odd")

    assert _client().delete_user_contributions("odd/key ?#") == 1
    assert "odd" not in service.records()
    assert (
        service.requests[-1]
        .url.raw_path.decode()
        .startswith("/reference/contributions/by-contributor/odd%2Fkey%20%3F%23")
    )


@pytest.mark.parametrize("status", [401, 422, 500, 503])
def test_a_failed_delete_raises(service, status):
    service.failure_status = status

    with pytest.raises(httpx.HTTPStatusError):
        _client().delete_user_contributions("user-a")
    with pytest.raises(httpx.HTTPStatusError):
        _client().delete_tenant_contributions("t-1")
    assert len(service.rows) == 4


def test_a_wrong_token_is_refused_by_the_service_and_raises(service):
    client = InferenceServiceClient("http://inference:8000", service_token="wrong")

    with pytest.raises(httpx.HTTPStatusError) as caught:
        client.delete_user_contributions("user-a")
    assert caught.value.response.status_code == 401
    assert len(service.rows) == 4


@pytest.mark.parametrize("blank", ["", "  "])
def test_blank_keys_are_refused_before_any_request(service, blank):
    with pytest.raises(ValueError):
        _client().delete_user_contributions(blank)
    with pytest.raises(ValueError):
        _client().delete_user_contributions("user-a", tenant_key=blank)
    with pytest.raises(ValueError):
        _client().delete_tenant_contributions(blank)
    assert service.requests == []
