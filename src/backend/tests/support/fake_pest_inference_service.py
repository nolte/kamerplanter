"""An in-memory inference-service ``pest_embeddings`` behind an ``httpx.MockTransport``.

Issue #1759 — the erasure deletes contributed pest prototypes through the
inference-service. The fake serves what the service serves for this table and
behaves like it:

* ``POST /pest/reference/contributions/erase`` (``{"contribution_keys"}``) and
  ``POST /pest/reference/contributions/erase-by-tenant`` (``{"tenant_key"}``)
  delete ``source == 'user_contributed'`` rows only — active or deactivated —
  by ``source_record_id`` / by the ``contribution://<tenant>/`` prefix of
  ``source_url``; an empty list, a blank key or a tenant key with ``/`` is 422;
* ``GET /pest/reference/{label}`` and ``PATCH /pest/reference/{label}/{id}``,
  the curation routes the erasure used before #1759 (list + deactivate), so
  the pre-#1759 code path can be measured against the same rows;
* a request without the service token is 401; ``failure_status`` makes every
  request answer that status.

Rows are written the way ``app/tasks/pest_image_tasks.py`` writes them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import httpx

_USER_CONTRIBUTED = "user_contributed"
_ERASE = "/pest/reference/contributions/erase"
_ERASE_BY_TENANT = "/pest/reference/contributions/erase-by-tenant"


def _blank(value: object) -> bool:
    return not isinstance(value, str) or not value.strip()


@dataclass
class FakePestInferenceService:
    token: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    requests: list[httpx.Request] = field(default_factory=list)
    failure_status: int | None = None

    def add_contribution(self, *, label: str, tenant_key: str, contribution_key: str, active: bool = True) -> None:
        """A prototype as the promotion index task writes it."""
        self.rows.append(
            {
                "id": len(self.rows) + 1,
                "label": label,
                "source": _USER_CONTRIBUTED,
                "source_record_id": contribution_key,
                "source_url": f"contribution://{tenant_key}/{contribution_key}",
                "is_active": active,
            }
        )

    def add_curated(self, *, label: str, record: str) -> None:
        self.rows.append(
            {
                "id": len(self.rows) + 1,
                "label": label,
                "source": "gbif",
                "source_record_id": record,
                "source_url": f"https://gbif.test/{record}",
                "is_active": True,
            }
        )

    def records(self) -> set[str]:
        return {row["source_record_id"] for row in self.rows}

    def handles(self, url: str) -> bool:
        return httpx.URL(url).path.startswith("/pest/")

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.failure_status is not None:
            return httpx.Response(self.failure_status, json={"detail": "unavailable"})
        if request.headers.get("Authorization") != f"Bearer {self.token}":
            return httpx.Response(401, json={"detail": "Invalid or missing service token."})
        path = request.url.path
        if request.method == "POST" and path == _ERASE:
            keys = json.loads(request.content or b"{}").get("contribution_keys")
            if not keys or any(_blank(k) for k in keys):
                return httpx.Response(422, json={"detail": "blank key"})
            return self._delete(lambda r: r["source_record_id"] in set(keys))
        if request.method == "POST" and path == _ERASE_BY_TENANT:
            tenant = json.loads(request.content or b"{}").get("tenant_key")
            if _blank(tenant) or "/" in tenant:
                return httpx.Response(422, json={"detail": "blank key"})
            return self._delete(lambda r: r["source_url"].startswith(f"contribution://{tenant}/"))
        parts = path.strip("/").split("/")
        if request.method == "GET" and len(parts) == 3 and parts[:2] == ["pest", "reference"]:
            images = [dict(r) for r in self.rows if r["label"] == parts[2]]
            return httpx.Response(200, json={"label": parts[2], "images": images})
        if request.method == "PATCH" and len(parts) == 4 and parts[:2] == ["pest", "reference"]:
            body = json.loads(request.content or b"{}")
            for row in self.rows:
                if row["label"] == parts[2] and str(row["id"]) == parts[3]:
                    row["is_active"] = bool(body.get("is_active"))
                    return httpx.Response(200, json={"status": "ok"})
            return httpx.Response(404)
        return httpx.Response(404)

    def _delete(self, matches) -> httpx.Response:  # type: ignore[no-untyped-def]
        before = len(self.rows)
        self.rows = [r for r in self.rows if not (r["source"] == _USER_CONTRIBUTED and matches(r))]
        return httpx.Response(200, json={"status": "ok", "deleted": before - len(self.rows)})


def route_pest_requests_to(monkeypatch, service: FakePestInferenceService) -> None:  # type: ignore[no-untyped-def]
    """Send ``httpx.get/post/patch`` for ``/pest/...`` URLs through *service*.

    Other URLs go to whatever the functions were before (another fake, or the
    real network function), so this composes with ``route_httpx_post_to``.
    URL building, headers, body encoding and ``raise_for_status`` stay real.
    """
    for method in ("get", "post", "patch"):
        previous = getattr(httpx, method)

        def _call(url: str, _method: str = method, _previous: Any = previous, **kwargs: Any) -> httpx.Response:
            if not service.handles(url):
                return _previous(url, **kwargs)
            with httpx.Client(transport=service.transport()) as client:
                return getattr(client, _method)(url, **kwargs)

        monkeypatch.setattr(httpx, method, _call)
