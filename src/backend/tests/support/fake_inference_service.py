"""An in-memory inference-service reference index behind an ``httpx.MockTransport``.

Issue #1753 — the backend erases a user's / tenant's ``user_contributed``
reference vectors through two inference-service endpoints. Tests that drive the
real :class:`InferenceServiceClient` need a counterpart that behaves like the
service does, not one that accepts anything:

* it serves only ``POST /reference/contributions/erase-by-contributor`` (body
  ``{"contributed_by", "tenant_key"}``) and ``POST
  /reference/contributions/erase-by-tenant`` (body ``{"tenant_key"}``); every
  other route is a 404 — in particular the retired key-in-path ``DELETE``
  routes, whose URLs carried the key into access logs (SEC-001);
* it refuses a request without the expected bearer token (401), as the
  service's app-level ``require_service_token`` does;
* it refuses a missing or blank key (422), as the service does;
* it deletes only rows with ``source == 'user_contributed'``, as the service's
  SQL does (the SQL itself is pinned in the inference-service's own suite).

``failure_status`` makes every request answer that status, to drive the
fail-loud paths. ``requests`` records what reached the service.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx

_USER_CONTRIBUTED = "user_contributed"
_BY_CONTRIBUTOR = "/reference/contributions/erase-by-contributor"
_BY_TENANT = "/reference/contributions/erase-by-tenant"


def _blank(value: object) -> bool:
    return not isinstance(value, str) or not value.strip()


@dataclass
class FakeInferenceService:
    token: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    requests: list[httpx.Request] = field(default_factory=list)
    failure_status: int | None = None

    def add(self, *, source: str, contributed_by: str | None, tenant_key: str | None, record: str) -> None:
        self.rows.append(
            {"source": source, "contributed_by": contributed_by, "tenant_key": tenant_key, "record": record}
        )

    def records(self) -> set[str]:
        return {row["record"] for row in self.rows}

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.failure_status is not None:
            return httpx.Response(self.failure_status, json={"detail": "unavailable"})
        if request.headers.get("Authorization") != f"Bearer {self.token}":
            return httpx.Response(401, json={"detail": "Invalid or missing service token."})
        path = request.url.path
        if path not in (_BY_CONTRIBUTOR, _BY_TENANT):
            return httpx.Response(404)
        if request.method != "POST":
            return httpx.Response(405)
        body = json.loads(request.content or b"{}")
        if path == _BY_CONTRIBUTOR:
            contributor = body.get("contributed_by")
            tenant_key = body.get("tenant_key")
            if _blank(contributor) or (tenant_key is not None and _blank(tenant_key)):
                return httpx.Response(422, json={"detail": "blank key"})
            return self._delete(
                lambda r: r["contributed_by"] == contributor and (tenant_key is None or r["tenant_key"] == tenant_key)
            )
        tenant = body.get("tenant_key")
        if _blank(tenant):
            return httpx.Response(422, json={"detail": "blank key"})
        return self._delete(lambda r: r["tenant_key"] == tenant)

    def _delete(self, matches) -> httpx.Response:  # type: ignore[no-untyped-def]
        before = len(self.rows)
        self.rows = [r for r in self.rows if not (r["source"] == _USER_CONTRIBUTED and matches(r))]
        return httpx.Response(200, json={"status": "ok", "deleted": before - len(self.rows)})


def route_httpx_post_to(monkeypatch, service: FakeInferenceService) -> None:  # type: ignore[no-untyped-def]
    """Send the client module's ``httpx.post`` through *service*'s transport.

    The client calls the module-level ``httpx.post``; this swaps exactly that
    function for one that issues the same request through an ``httpx.Client``
    on the mock transport, so URL building, headers, body encoding,
    ``raise_for_status``, the JSON decode — and httpx's own request log line —
    are the real ones.
    """
    from app.data_access.external import inference_service_client as module

    def _post(url: str, **kwargs: Any) -> httpx.Response:
        with httpx.Client(transport=service.transport()) as client:
            return client.post(url, **kwargs)

    monkeypatch.setattr(module.httpx, "post", _post)
