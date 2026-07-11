"""REQ-016 §3.3 — httpx-based REST implementation of the InvenTree adapter.

Talks to the InvenTree REST API (``/api/part/``, ``/api/stock/``,
``/api/stock/{action}/``, ``/api/part/category/``) with token auth.

Security (REQ-016 §4.1):

* **SSRF (IT-003/SEC):** the admin/tenant-supplied ``base_url`` is re-validated
  with :func:`validate_inventree_url` immediately before *every* request, so a
  stored-but-unsafe URL (or a DNS rebind) can never turn the adapter into an
  SSRF primitive. Link-local / cloud-metadata addresses are always blocked;
  private/LAN addresses only when the operator opted in.
* **Credentials (IT-001/IT-002):** the plaintext token lives only in this
  adapter's in-memory ``Authorization`` header — it is never logged (structlog
  calls carry status/detail only, never the header) and never serialized.
* **TLS (IT-003):** ``verify_ssl`` defaults to on; only disabled explicitly.
* **Timeouts (NFR-007):** every call carries an explicit connect+read timeout.
* **Redirects (IT-003/SEC):** the outbound httpx client is created with
  ``follow_redirects=False`` — a public InvenTree host must never be able to
  bounce the adapter onto an internal address via a 3xx ``Location``.
* **Rate limit (IT-005):** a Valkey/Redis-backed sliding window caps outbound
  requests at 60/min per connection. The window is keyed on a stable connection
  identifier and lives in the shared cache, so it survives adapter
  re-instantiation (a fresh adapter is built per request) instead of resetting.
  When no shared store / connection key is wired, or the store is transiently
  unavailable, it degrades to a best-effort per-instance window.

No InvenTree SDK is used — only httpx (project convention for external adapters).
"""

from __future__ import annotations

import contextlib
import hashlib
import time
import uuid
from typing import Any

import httpx
import structlog

from app.common.url_safety import validate_inventree_url
from app.domain.interfaces.inventree_adapter import (
    InvenTreeAdapter,
    InvenTreeCategoryData,
    InvenTreePartData,
    InvenTreeStockItemData,
    StockAdjustmentResult,
)

logger = structlog.get_logger(__name__)

#: IT-005 — client-side outbound cap (requests per rolling window).
_RATE_LIMIT_MAX_REQUESTS = 60
_RATE_LIMIT_WINDOW_SECONDS = 60.0
#: TTL for the shared sliding-window key (window + a small grace margin) so an
#: idle connection's counter self-expires from the cache.
_RATE_LIMIT_KEY_TTL_SECONDS = int(_RATE_LIMIT_WINDOW_SECONDS) + 1
#: Redis keyspace prefix for the per-connection sliding window.
_RATE_LIMIT_KEY_PREFIX = "inventree_ratelimit"


class InvenTreeRateLimitError(RuntimeError):
    """Raised when the client-side outbound rate limit (IT-005) is exceeded."""


class InvenTreeRestAdapter(InvenTreeAdapter):
    """REST implementation of :class:`InvenTreeAdapter` using httpx (async)."""

    def __init__(
        self,
        base_url: str,
        api_token: str,
        *,
        verify_ssl: bool = True,
        allow_private: bool = False,
        connection_key: str | None = None,
        redis_client: Any | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._verify_ssl = verify_ssl
        self._allow_private = allow_private
        self._headers = {
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json",
        }
        self._timeout = httpx.Timeout(10.0, connect=5.0)
        # IT-005 shared sliding window: a duck-typed Redis/Valkey client plus a
        # stable per-connection key. The raw connection key is hashed so it never
        # lands verbatim in the cache keyspace.
        self._redis = redis_client
        self._rate_limit_key = (
            f"{_RATE_LIMIT_KEY_PREFIX}:{hashlib.sha256(connection_key.encode()).hexdigest()}"
            if connection_key
            else None
        )
        # Best-effort fallback window when no shared store is wired.
        self._request_times: list[float] = []

    # ── Guards ───────────────────────────────────────────────────────────

    def _guard_url(self) -> None:
        """Re-validate the base URL against SSRF before dialing (IT-003/SEC)."""
        validate_inventree_url(self._base_url, allow_private=self._allow_private, field="base_url")

    def _guard_rate_limit(self) -> None:
        """Client-side rate limit (IT-005, 60 req/min).

        Uses the shared Valkey/Redis sliding window when a store and connection
        key are wired (so the cap persists across adapter re-instantiation), and
        degrades to a best-effort per-instance window when they are absent or the
        store is transiently unavailable (NFR-007 graceful degradation).
        """
        if self._redis is not None and self._rate_limit_key is not None:
            try:
                self._guard_rate_limit_shared()
                return
            except InvenTreeRateLimitError:
                raise
            except Exception as exc:  # noqa: BLE001 - store outage → in-memory fallback
                logger.warning("inventree_rate_limit_store_unavailable", error=type(exc).__name__)
        self._guard_rate_limit_in_memory()

    def _guard_rate_limit_shared(self) -> None:
        """Persistent per-connection sliding window backed by a Redis sorted set."""
        now = time.time()
        cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
        member = f"{now:.6f}:{uuid.uuid4().hex}"
        results = (
            self._redis.pipeline()
            .zremrangebyscore(self._rate_limit_key, 0, cutoff)
            .zadd(self._rate_limit_key, {member: now})
            .zcard(self._rate_limit_key)
            .expire(self._rate_limit_key, _RATE_LIMIT_KEY_TTL_SECONDS)
            .execute()
        )
        count = results[2]
        if count > _RATE_LIMIT_MAX_REQUESTS:
            # A rejected attempt must not keep occupying a slot in the window.
            with contextlib.suppress(Exception):  # cleanup is best-effort
                self._redis.zrem(self._rate_limit_key, member)
            raise InvenTreeRateLimitError("InvenTree client-side rate limit exceeded (60 req/min).")

    def _guard_rate_limit_in_memory(self) -> None:
        """Best-effort per-instance fallback window (no shared store)."""
        now = time.monotonic()
        cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
        self._request_times = [t for t in self._request_times if t > cutoff]
        if len(self._request_times) >= _RATE_LIMIT_MAX_REQUESTS:
            raise InvenTreeRateLimitError("InvenTree client-side rate limit exceeded (60 req/min).")
        self._request_times.append(now)

    def _client(self) -> httpx.AsyncClient:
        self._guard_url()
        self._guard_rate_limit()
        # follow_redirects=False (IT-003/SEC): never chase a 3xx to an internal target.
        return httpx.AsyncClient(
            headers=self._headers,
            timeout=self._timeout,
            verify=self._verify_ssl,
            follow_redirects=False,
        )

    # ── Reads ────────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        try:
            async with self._client() as client:
                resp = await client.get(f"{self._base_url}/api/")
                return resp.status_code == 200
        except (httpx.HTTPError, InvenTreeRateLimitError) as exc:
            logger.debug("inventree_health_check_unreachable", error=type(exc).__name__)
            return False

    async def get_part(self, part_id: int) -> InvenTreePartData | None:
        async with self._client() as client:
            resp = await client.get(f"{self._base_url}/api/part/{part_id}/")
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return self._map_part(resp.json())

    async def search_parts(
        self, query: str, *, category_id: int | None = None, limit: int = 25
    ) -> list[InvenTreePartData]:
        params: dict = {"search": query, "limit": limit}
        if category_id is not None:
            params["category"] = category_id
        async with self._client() as client:
            resp = await client.get(f"{self._base_url}/api/part/", params=params)
            resp.raise_for_status()
            return [self._map_part(item) for item in self._results(resp.json())]

    async def get_stock_items(self, part_id: int) -> list[InvenTreeStockItemData]:
        async with self._client() as client:
            resp = await client.get(f"{self._base_url}/api/stock/", params={"part": part_id})
            resp.raise_for_status()
            return [self._map_stock_item(item) for item in self._results(resp.json())]

    async def get_categories(self, *, parent_id: int | None = None) -> list[InvenTreeCategoryData]:
        params: dict = {}
        if parent_id is not None:
            params["parent"] = parent_id
        async with self._client() as client:
            resp = await client.get(f"{self._base_url}/api/part/category/", params=params)
            resp.raise_for_status()
            return [self._map_category(item) for item in self._results(resp.json())]

    # ── Writes ───────────────────────────────────────────────────────────

    async def remove_stock(self, items: list[dict], *, notes: str = "") -> StockAdjustmentResult:
        return await self._adjust_stock("remove", items, notes=notes)

    async def add_stock(self, items: list[dict], *, notes: str = "") -> StockAdjustmentResult:
        return await self._adjust_stock("add", items, notes=notes)

    async def count_stock(self, items: list[dict], *, notes: str = "") -> StockAdjustmentResult:
        return await self._adjust_stock("count", items, notes=notes)

    async def _adjust_stock(self, action: str, items: list[dict], *, notes: str = "") -> StockAdjustmentResult:
        payload = {"items": items, "notes": notes}
        try:
            async with self._client() as client:
                resp = await client.post(f"{self._base_url}/api/stock/{action}/", json=payload)
                resp.raise_for_status()
                return StockAdjustmentResult(success=True, items_affected=len(items))
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "inventree_stock_adjust_failed",
                action=action,
                status=exc.response.status_code,
            )
            return StockAdjustmentResult(success=False, error=f"HTTP {exc.response.status_code}")
        except (httpx.HTTPError, InvenTreeRateLimitError) as exc:
            logger.warning("inventree_stock_adjust_error", action=action, error=type(exc).__name__)
            return StockAdjustmentResult(success=False, error=type(exc).__name__)

    # ── Mapping ──────────────────────────────────────────────────────────

    @staticmethod
    def _results(data: object) -> list:
        if isinstance(data, dict):
            results = data.get("results", [])
            return results if isinstance(results, list) else []
        return data if isinstance(data, list) else []

    @staticmethod
    def _map_part(raw: dict) -> InvenTreePartData:
        category = raw.get("category_detail") or {}
        return InvenTreePartData(
            pk=raw["pk"],
            name=raw.get("name", ""),
            ipn=raw.get("IPN"),
            description=raw.get("description"),
            category_name=category.get("name") if isinstance(category, dict) else None,
            is_purchaseable=raw.get("purchaseable", False),
            is_trackable=raw.get("trackable", False),
            total_in_stock=float(raw.get("in_stock", 0.0) or 0.0),
            stock_unit=raw.get("units"),
        )

    @staticmethod
    def _map_stock_item(raw: dict) -> InvenTreeStockItemData:
        location = raw.get("location_detail") or {}
        return InvenTreeStockItemData(
            pk=raw["pk"],
            part_id=raw.get("part", 0),
            quantity=float(raw.get("quantity", 0.0) or 0.0),
            serial=raw.get("serial"),
            location_name=location.get("name") if isinstance(location, dict) else None,
            status=raw.get("status", 10),
        )

    @staticmethod
    def _map_category(raw: dict) -> InvenTreeCategoryData:
        return InvenTreeCategoryData(
            pk=raw["pk"],
            name=raw.get("name", ""),
            parent=raw.get("parent"),
            path=raw.get("pathstring", ""),
            part_count=raw.get("part_count", 0),
        )
