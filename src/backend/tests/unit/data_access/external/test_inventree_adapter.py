"""REQ-016 — unit tests for the InvenTree REST adapter.

Covers the JSON→model mapping, the mocked async HTTP path (request shape +
response mapping), the SSRF guard that fires before every dial, and the
client-side rate limit (IT-005).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.common.exceptions import ValidationError
from app.data_access.external.inventree_adapter import (
    _RATE_LIMIT_MAX_REQUESTS,
    InvenTreeRateLimitError,
    InvenTreeRestAdapter,
)

# A public numeric host avoids any DNS lookup while still passing the SSRF gate.
# The base URL is the InvenTree server root; the adapter appends ``/api/...``.
PUBLIC_URL = "http://8.8.8.8"

PART_RESPONSE = {
    "pk": 42,
    "name": "BioBizz Bio-Bloom 1L",
    "IPN": "FERT-BB-001",
    "description": "Bloom booster",
    "category_detail": {"name": "Fertilizers"},
    "purchaseable": True,
    "trackable": False,
    "in_stock": 12.5,
    "units": "litre",
}

STOCK_RESPONSE = {
    "results": [
        {"pk": 900, "part": 42, "quantity": 12.5, "serial": None, "location_detail": {"name": "Shelf A"}, "status": 10},
    ]
}


def _adapter(url: str = PUBLIC_URL, **kwargs) -> InvenTreeRestAdapter:
    return InvenTreeRestAdapter(url, "secret-token", allow_private=True, **kwargs)


class _FakeRedis:
    """Minimal in-memory sorted-set store shared across adapter instances.

    Implements just the sliding-window surface the adapter uses (pipeline with
    zremrangebyscore/zadd/zcard/expire + zrem). State lives in ``self.store`` so
    two adapters constructed with the *same* instance share one window — mirroring
    a real Valkey/Redis backend.
    """

    def __init__(self) -> None:
        self.store: dict[str, dict[str, float]] = {}

    def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        zset = self.store.setdefault(key, {})
        removed = [m for m, s in zset.items() if min_score <= s <= max_score]
        for member in removed:
            del zset[member]
        return len(removed)

    def zadd(self, key: str, mapping: dict[str, float]) -> int:
        zset = self.store.setdefault(key, {})
        added = 0
        for member, score in mapping.items():
            if member not in zset:
                added += 1
            zset[member] = score
        return added

    def zcard(self, key: str) -> int:
        return len(self.store.get(key, {}))

    def zrem(self, key: str, *members: str) -> int:
        zset = self.store.setdefault(key, {})
        removed = 0
        for member in members:
            if member in zset:
                del zset[member]
                removed += 1
        return removed

    def expire(self, key: str, ttl: int) -> bool:  # noqa: ARG002 - TTL is a no-op here
        return True

    def pipeline(self) -> _FakePipeline:
        return _FakePipeline(self)


class _FakePipeline:
    """Queues operations and applies them on ``execute`` (like redis-py)."""

    def __init__(self, redis: _FakeRedis) -> None:
        self._redis = redis
        self._ops: list[tuple[str, tuple]] = []

    def zremrangebyscore(self, *args) -> _FakePipeline:
        self._ops.append(("zremrangebyscore", args))
        return self

    def zadd(self, *args) -> _FakePipeline:
        self._ops.append(("zadd", args))
        return self

    def zcard(self, *args) -> _FakePipeline:
        self._ops.append(("zcard", args))
        return self

    def expire(self, *args) -> _FakePipeline:
        self._ops.append(("expire", args))
        return self

    def execute(self) -> list:
        return [getattr(self._redis, name)(*args) for name, args in self._ops]


def _mock_client(mock_cls, *, get=None, post=None):
    mock_ac = AsyncMock()
    if get is not None:
        mock_ac.get.return_value = get
    if post is not None:
        mock_ac.post.return_value = post
    mock_ac.__aenter__ = AsyncMock(return_value=mock_ac)
    mock_ac.__aexit__ = AsyncMock(return_value=False)
    mock_cls.return_value = mock_ac
    return mock_ac


class TestMapping:
    def test_map_part_projects_inventree_fields(self):
        part = InvenTreeRestAdapter._map_part(PART_RESPONSE)
        assert part.pk == 42
        assert part.name == "BioBizz Bio-Bloom 1L"
        assert part.ipn == "FERT-BB-001"
        assert part.category_name == "Fertilizers"
        assert part.is_purchaseable is True
        assert part.total_in_stock == 12.5
        assert part.stock_unit == "litre"

    def test_map_stock_item_projects_fields(self):
        item = InvenTreeRestAdapter._map_stock_item(STOCK_RESPONSE["results"][0])
        assert item.pk == 900
        assert item.part_id == 42
        assert item.quantity == 12.5
        assert item.location_name == "Shelf A"

    def test_results_handles_dict_and_list_shapes(self):
        assert InvenTreeRestAdapter._results({"results": [1, 2]}) == [1, 2]
        assert InvenTreeRestAdapter._results([3, 4]) == [3, 4]
        assert InvenTreeRestAdapter._results({"no_results": 1}) == []


class TestSsrfGuard:
    def test_metadata_address_always_rejected(self):
        adapter = InvenTreeRestAdapter("http://169.254.169.254/api", "t", allow_private=True)
        with pytest.raises(ValidationError):
            adapter._guard_url()

    def test_private_address_rejected_without_opt_in(self):
        adapter = InvenTreeRestAdapter("http://127.0.0.1/api", "t", allow_private=False)
        with pytest.raises(ValidationError):
            adapter._guard_url()

    def test_private_address_allowed_with_opt_in(self):
        adapter = InvenTreeRestAdapter("http://127.0.0.1/api", "t", allow_private=True)
        assert adapter._guard_url() is None

    @pytest.mark.asyncio
    async def test_health_check_raises_on_blocked_url(self):
        # The SSRF ValidationError surfaces from _guard_url; health_check itself
        # only swallows httpx / rate-limit errors, so the caller (service) maps it.
        adapter = InvenTreeRestAdapter("http://10.0.0.5/api", "t", allow_private=False)
        with pytest.raises(ValidationError):
            await adapter.health_check()


class TestRateLimit:
    def test_rate_limit_trips_after_max_requests(self):
        adapter = _adapter()
        for _ in range(_RATE_LIMIT_MAX_REQUESTS):
            adapter._guard_rate_limit()
        with pytest.raises(InvenTreeRateLimitError):
            adapter._guard_rate_limit()


class TestPersistentRateLimit:
    """IT-005: the window must live in the shared store, not per-adapter memory."""

    def test_rate_limit_persists_across_adapter_instances(self):
        redis = _FakeRedis()
        # Exhaust the window on one adapter instance.
        first = _adapter(connection_key="conn-1", redis_client=redis)
        for _ in range(_RATE_LIMIT_MAX_REQUESTS):
            first._guard_rate_limit()
        # A brand-new adapter (rebuilt per request) shares the same window and must
        # stay blocked instead of resetting the counter.
        second = _adapter(connection_key="conn-1", redis_client=redis)
        with pytest.raises(InvenTreeRateLimitError):
            second._guard_rate_limit()

    def test_rate_limit_isolated_per_connection_key(self):
        redis = _FakeRedis()
        exhausted = _adapter(connection_key="conn-a", redis_client=redis)
        for _ in range(_RATE_LIMIT_MAX_REQUESTS):
            exhausted._guard_rate_limit()
        # A different connection has its own window and is unaffected.
        other = _adapter(connection_key="conn-b", redis_client=redis)
        other._guard_rate_limit()  # must not raise

    def test_falls_back_to_in_memory_when_store_unavailable(self):
        class _BrokenRedis:
            def pipeline(self):
                raise ConnectionError("valkey down")

        adapter = _adapter(connection_key="conn-x", redis_client=_BrokenRedis())
        # Degrades gracefully to the per-instance window (NFR-007) — still caps.
        for _ in range(_RATE_LIMIT_MAX_REQUESTS):
            adapter._guard_rate_limit()
        with pytest.raises(InvenTreeRateLimitError):
            adapter._guard_rate_limit()


class TestNoRedirectFollow:
    """IT-003/SEC: the outbound client must never chase a 3xx Location."""

    @pytest.mark.asyncio
    async def test_client_is_built_without_redirect_following(self):
        adapter = _adapter()
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = PART_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.inventree_adapter.httpx.AsyncClient") as mock_cls:
            _mock_client(mock_cls, get=mock_resp)
            await adapter.get_part(42)

        assert mock_cls.call_args.kwargs["follow_redirects"] is False


class TestMockedHttp:
    @pytest.mark.asyncio
    async def test_get_part_maps_response(self):
        adapter = _adapter()
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = PART_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.inventree_adapter.httpx.AsyncClient") as mock_cls:
            mock_ac = _mock_client(mock_cls, get=mock_resp)
            part = await adapter.get_part(42)

        assert part is not None
        assert part.pk == 42
        assert part.total_in_stock == 12.5
        assert mock_ac.get.call_args.args[0] == "http://8.8.8.8/api/part/42/"

    @pytest.mark.asyncio
    async def test_get_part_returns_none_on_404(self):
        adapter = _adapter()
        mock_resp = MagicMock(status_code=404)

        with patch("app.data_access.external.inventree_adapter.httpx.AsyncClient") as mock_cls:
            _mock_client(mock_cls, get=mock_resp)
            assert await adapter.get_part(99) is None

    @pytest.mark.asyncio
    async def test_get_stock_items_maps_results(self):
        adapter = _adapter()
        mock_resp = MagicMock()
        mock_resp.json.return_value = STOCK_RESPONSE
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.inventree_adapter.httpx.AsyncClient") as mock_cls:
            _mock_client(mock_cls, get=mock_resp)
            items = await adapter.get_stock_items(42)

        assert len(items) == 1
        assert items[0].pk == 900

    @pytest.mark.asyncio
    async def test_remove_stock_posts_adjustment(self):
        adapter = _adapter()
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()

        with patch("app.data_access.external.inventree_adapter.httpx.AsyncClient") as mock_cls:
            mock_ac = _mock_client(mock_cls, post=mock_resp)
            result = await adapter.remove_stock([{"pk": 900, "quantity": 50}], notes="feed")

        assert result.success is True
        assert result.items_affected == 1
        assert mock_ac.post.call_args.args[0] == "http://8.8.8.8/api/stock/remove/"

    @pytest.mark.asyncio
    async def test_health_check_true_on_200(self):
        adapter = _adapter()
        mock_resp = MagicMock(status_code=200)

        with patch("app.data_access.external.inventree_adapter.httpx.AsyncClient") as mock_cls:
            _mock_client(mock_cls, get=mock_resp)
            assert await adapter.health_check() is True
