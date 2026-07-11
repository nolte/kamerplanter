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
* **Rate limit (IT-005):** a best-effort per-adapter token window caps outbound
  requests at 60/min so a Kamerplanter loop cannot hammer InvenTree.

No InvenTree SDK is used — only httpx (project convention for external adapters).
"""

from __future__ import annotations

import time

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
        self._request_times: list[float] = []

    # ── Guards ───────────────────────────────────────────────────────────

    def _guard_url(self) -> None:
        """Re-validate the base URL against SSRF before dialing (IT-003/SEC)."""
        validate_inventree_url(self._base_url, allow_private=self._allow_private, field="base_url")

    def _guard_rate_limit(self) -> None:
        """Best-effort client-side rate limit (IT-005, 60 req/min)."""
        now = time.monotonic()
        cutoff = now - _RATE_LIMIT_WINDOW_SECONDS
        self._request_times = [t for t in self._request_times if t > cutoff]
        if len(self._request_times) >= _RATE_LIMIT_MAX_REQUESTS:
            raise InvenTreeRateLimitError("InvenTree client-side rate limit exceeded (60 req/min).")
        self._request_times.append(now)

    def _client(self) -> httpx.AsyncClient:
        self._guard_url()
        self._guard_rate_limit()
        return httpx.AsyncClient(headers=self._headers, timeout=self._timeout, verify=self._verify_ssl)

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
