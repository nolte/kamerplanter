"""REQ-033 service-account auth + permission-matrix binding tests (§4.3, §4.4)."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

import pytest

from app.common.enums import McpPermission, TenantRole
from app.common.exceptions import ForbiddenError, RateLimitError, UnauthorizedError
from app.core.permissions import has_mcp_permission, list_mcp_permissions
from app.domain.models.auth import ApiKey
from app.domain.models.user import User
from app.mcp_server.auth import McpAuthenticator
from app.mcp_server.rate_limit import McpRateLimiter


# ── permission-matrix binding (§4.4) ───────────────────────────────────────────
class TestMcpPermissionMatrix:
    def test_viewer_is_read_only(self):
        assert has_mcp_permission(TenantRole.VIEWER, McpPermission.READ)
        assert not has_mcp_permission(TenantRole.VIEWER, McpPermission.WRITE)
        assert not has_mcp_permission(TenantRole.VIEWER, McpPermission.SETUP)

    def test_grower_reads_and_writes_but_not_setup(self):
        assert has_mcp_permission(TenantRole.GROWER, McpPermission.READ)
        assert has_mcp_permission(TenantRole.GROWER, McpPermission.WRITE)
        assert not has_mcp_permission(TenantRole.GROWER, McpPermission.SETUP)

    def test_admin_has_all_including_setup(self):
        assert list_mcp_permissions(TenantRole.ADMIN) == [
            McpPermission.READ,
            McpPermission.SETUP,
            McpPermission.WRITE,
        ]


# ── authenticator (§4.3) ────────────────────────────────────────────────────────
class _FakeApiKeyRepo:
    def __init__(self, api_key: ApiKey | None) -> None:
        self._api_key = api_key
        self.last_used_updated = False

    def get_by_hash(self, key_hash: str):
        return self._api_key

    def update_last_used(self, key: str) -> None:
        self.last_used_updated = True


class _FakeUserRepo:
    def __init__(self, user: User | None) -> None:
        self._user = user

    def get_by_key(self, key: str):
        return self._user


class _TenantWithRole:
    def __init__(self, key, slug, role):
        self.key = key
        self.slug = slug
        self.role = role


class _FakeTenantService:
    def __init__(self, tenants):
        self._tenants = tenants

    def list_my_tenants(self, user_key: str):
        return self._tenants


_RAW = "kp_secretkey"
_HASH = hashlib.sha256(_RAW.encode()).hexdigest()


def _service_user() -> User:
    return User(
        key="sa-1",
        email="bot@example.org",
        display_name="daily-bot",
        account_type="service",
        is_active=True,
    )


def _api_key(**overrides) -> ApiKey:
    base = dict(key="ak-1", user_key="sa-1", label="mcp", key_hash=_HASH, key_prefix="kp_secre")
    base.update(overrides)
    return ApiKey(**base)


def _authenticator(api_key, user, tenants, rate_limiter=None):
    return McpAuthenticator(
        _FakeApiKeyRepo(api_key),
        _FakeUserRepo(user),
        _FakeTenantService(tenants),
        rate_limiter=rate_limiter,
    )


class _FakeRedis:
    """Minimal in-memory Redis double for the per-minute counter."""

    def __init__(self) -> None:
        self.counters: dict = {}

    def incr(self, key: str) -> int:
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    def expire(self, key: str, seconds: int) -> None:  # pragma: no cover - trivial
        pass

    def ttl(self, key: str) -> int:  # pragma: no cover - trivial
        return 60


def test_authenticate_resolves_single_tenant_principal():
    auth = _authenticator(
        _api_key(),
        _service_user(),
        [_TenantWithRole("home", "home", TenantRole.GROWER)],
    )
    principal = auth.authenticate(_RAW)
    assert principal.service_account_key == "sa-1"
    assert principal.tenant_slug == "home"
    assert principal.role == TenantRole.GROWER


def test_authenticate_rejects_non_service_account():
    user = _service_user()
    user.account_type = "user"
    auth = _authenticator(_api_key(), user, [_TenantWithRole("home", "home", TenantRole.ADMIN)])
    with pytest.raises(ForbiddenError):
        auth.authenticate(_RAW)


def test_authenticate_rejects_missing_key():
    auth = _authenticator(None, None, [])
    with pytest.raises(UnauthorizedError):
        auth.authenticate(None)


def test_authenticate_rejects_unknown_key():
    auth = _authenticator(None, _service_user(), [])
    with pytest.raises(UnauthorizedError):
        auth.authenticate(_RAW)


def test_authenticate_rejects_expired_key():
    expired = _api_key(expires_at=datetime.now(UTC) - timedelta(days=1))
    auth = _authenticator(expired, _service_user(), [])
    with pytest.raises(UnauthorizedError):
        auth.authenticate(_RAW)


def test_authenticate_requires_tenant_scope_when_multi_tenant():
    auth = _authenticator(
        _api_key(),
        _service_user(),
        [
            _TenantWithRole("home", "home", TenantRole.ADMIN),
            _TenantWithRole("garden", "garden", TenantRole.VIEWER),
        ],
    )
    with pytest.raises(ForbiddenError):
        auth.authenticate(_RAW)


def test_authenticate_uses_tenant_scope_to_disambiguate():
    auth = _authenticator(
        _api_key(tenant_scope="garden"),
        _service_user(),
        [
            _TenantWithRole("home", "home", TenantRole.ADMIN),
            _TenantWithRole("garden-key", "garden", TenantRole.VIEWER),
        ],
    )
    principal = auth.authenticate(_RAW)
    assert principal.tenant_slug == "garden"
    assert principal.role == TenantRole.VIEWER


# ── SEC-003: valid-non-service masking ──────────────────────────────────────────
def test_authenticate_masks_non_service_as_unauthorized():
    user = _service_user()
    user.account_type = "user"
    auth = _authenticator(_api_key(), user, [_TenantWithRole("home", "home", TenantRole.ADMIN)])
    # Default (MCP transport) still discloses the 403 "service accounts only".
    with pytest.raises(ForbiddenError):
        auth.authenticate(_RAW)
    # With mask_non_service (the validate endpoint), it collapses to a generic 401.
    with pytest.raises(UnauthorizedError):
        auth.authenticate(_RAW, mask_non_service=True)


# ── SEC-004: service-account ip_allowlist enforcement ───────────────────────────
def test_authenticate_rejects_ip_not_in_allowlist():
    auth = _authenticator(
        _api_key(ip_allowlist=["10.0.0.0/8", "192.168.1.42/32"]),
        _service_user(),
        [_TenantWithRole("home", "home", TenantRole.GROWER)],
    )
    with pytest.raises(UnauthorizedError):
        auth.authenticate(_RAW, client_ip="203.0.113.7")


def test_authenticate_allows_ip_in_allowlist_cidr():
    auth = _authenticator(
        _api_key(ip_allowlist=["10.0.0.0/8"]),
        _service_user(),
        [_TenantWithRole("home", "home", TenantRole.GROWER)],
    )
    principal = auth.authenticate(_RAW, client_ip="10.1.2.3")
    assert principal.tenant_slug == "home"


def test_authenticate_rejects_when_ip_unresolved_but_allowlist_set():
    # Fail closed: an IP-restricted key with no resolvable client IP is rejected.
    auth = _authenticator(
        _api_key(ip_allowlist=["10.0.0.0/8"]),
        _service_user(),
        [_TenantWithRole("home", "home", TenantRole.GROWER)],
    )
    with pytest.raises(UnauthorizedError):
        auth.authenticate(_RAW, client_ip=None)


def test_authenticate_ignores_empty_allowlist():
    auth = _authenticator(
        _api_key(ip_allowlist=[]),
        _service_user(),
        [_TenantWithRole("home", "home", TenantRole.GROWER)],
    )
    principal = auth.authenticate(_RAW, client_ip="203.0.113.7")
    assert principal.tenant_slug == "home"


# ── SEC-004: service-account per-minute rate limit ──────────────────────────────
def test_authenticate_enforces_rate_limit_over_the_minute():
    redis = _FakeRedis()
    limiter = McpRateLimiter(redis)
    auth = _authenticator(
        _api_key(rate_limit_per_minute=2),
        _service_user(),
        [_TenantWithRole("home", "home", TenantRole.GROWER)],
        rate_limiter=limiter,
    )
    # First two calls are within quota, the third breaches → 429 (RateLimitError).
    auth.authenticate(_RAW, client_ip="10.0.0.1")
    auth.authenticate(_RAW, client_ip="10.0.0.1")
    with pytest.raises(RateLimitError):
        auth.authenticate(_RAW, client_ip="10.0.0.1")


def test_authenticate_no_rate_limit_when_field_unset():
    redis = _FakeRedis()
    auth = _authenticator(
        _api_key(),  # rate_limit_per_minute defaults to None
        _service_user(),
        [_TenantWithRole("home", "home", TenantRole.GROWER)],
        rate_limiter=McpRateLimiter(redis),
    )
    for _ in range(5):
        auth.authenticate(_RAW, client_ip="10.0.0.1")
    assert redis.counters == {}  # limiter never consulted
