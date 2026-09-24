"""An in-memory inference-service reference index behind an ``httpx.MockTransport``.

Issue #1753 — the backend erases a user's / tenant's ``user_contributed``
reference vectors through two inference-service endpoints. Tests that drive the
real :class:`InferenceServiceClient` need a counterpart that behaves like the
service does, not one that accepts anything:

* it serves only ``DELETE /reference/contributions/by-contributor/{key}``
  (optional ``tenant_key`` query) and ``DELETE
  /reference/contributions/by-tenant/{key}``; every other route is a 404;
* it refuses a request without the expected bearer token (401), as the
  service's app-level ``require_service_token`` does;
* it refuses a blank key (422), as the service's repository does;
* it deletes only rows with ``source == 'user_contributed'``, as the service's
  SQL does (the SQL itself is pinned in the inference-service's own suite).

``failure_status`` makes every request answer that status, to drive the
fail-loud paths. ``requests`` records what reached the service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import unquote

import httpx

_USER_CONTRIBUTED = "user_contributed"
_BY_CONTRIBUTOR = "/reference/contributions/by-contributor/"
_BY_TENANT = "/reference/contributions/by-tenant/"


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
        if request.method != "DELETE":
            return httpx.Response(405)
        # ``raw_path`` keeps the percent-encoding, so one encoded segment stays one
        # segment — the way the service's router splits it.
        path = request.url.raw_path.decode("ascii").split("?", 1)[0]
        if path.startswith(_BY_CONTRIBUTOR):
            contributor = self._segment(path[len(_BY_CONTRIBUTOR) :])
            tenant_key = request.url.params.get("tenant_key")
            if contributor is None or (tenant_key is not None and not tenant_key.strip()):
                return httpx.Response(422, json={"detail": "blank key"})
            return self._delete(
                lambda r: r["contributed_by"] == contributor and (tenant_key is None or r["tenant_key"] == tenant_key)
            )
        if path.startswith(_BY_TENANT):
            tenant = self._segment(path[len(_BY_TENANT) :])
            if tenant is None:
                return httpx.Response(422, json={"detail": "blank key"})
            return self._delete(lambda r: r["tenant_key"] == tenant)
        return httpx.Response(404)

    @staticmethod
    def _segment(raw: str) -> str | None:
        if not raw or "/" in raw:
            return None
        value = unquote(raw)
        return value if value.strip() else None

    def _delete(self, matches) -> httpx.Response:  # type: ignore[no-untyped-def]
        before = len(self.rows)
        self.rows = [r for r in self.rows if not (r["source"] == _USER_CONTRIBUTED and matches(r))]
        return httpx.Response(200, json={"status": "ok", "deleted": before - len(self.rows)})


def route_httpx_delete_to(monkeypatch, service: FakeInferenceService) -> None:  # type: ignore[no-untyped-def]
    """Send the client module's ``httpx.delete`` through *service*'s transport.

    The client calls the module-level ``httpx.delete``; this swaps exactly that
    function for one that issues the same request through an ``httpx.Client``
    on the mock transport, so URL building, headers, ``raise_for_status`` and
    the JSON decode are the real ones.
    """
    from app.data_access.external import inference_service_client as module

    def _delete(url: str, **kwargs: Any) -> httpx.Response:
        with httpx.Client(transport=service.transport()) as client:
            return client.delete(url, **kwargs)

    monkeypatch.setattr(module.httpx, "delete", _delete)
