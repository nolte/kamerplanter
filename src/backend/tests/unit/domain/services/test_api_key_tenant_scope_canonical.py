"""An API key's ``tenant_scope`` is stored as the tenant's key, validated at creation — #1852.

``POST /api/v1/auth/api-keys`` used to store ``tenant_scope`` exactly as typed,
and the scope predicate matched slug *or* key. A slug-scoped key therefore
survived the tenant erasure (which deletes keys whose ``tenant_scope`` equals the
tenant's **key**) and followed a re-issued slug to another tenant. A value naming
no tenant, or a tenant the caller is not in, was accepted too.

The tenant store here mirrors the real ``TenantService`` where it matters: an
unknown key *and* an unknown slug raise ``NotFoundError`` (``get_tenant`` /
``get_tenant_by_slug`` do), and membership is looked up per (user, tenant).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.common.exceptions import ForbiddenError, NotFoundError
from app.domain.engines.login_throttle_engine import LoginThrottleEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.tenant_erasure_engine import TenantErasureEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.models.auth import ApiKey, api_key_scope_admits
from app.domain.services.auth_service import AuthService

_OWNER = "owner"


class _TenantService:
    _tenants = {
        "tenant_a": SimpleNamespace(key="tenant_a", slug="club-a", is_active=True),
        "tenant_b": SimpleNamespace(key="tenant_b", slug="club-b", is_active=True),
        "tenant_x": SimpleNamespace(key="tenant_x", slug="closed", is_active=False),
        "tenant_i": SimpleNamespace(key="tenant_i", slug="left", is_active=True),
    }
    _memberships = {
        ("owner", "tenant_a"): True,
        ("owner", "tenant_x"): True,
        ("owner", "tenant_i"): False,  # inactive membership
    }

    def get_tenant(self, tenant_key: str) -> SimpleNamespace:
        if tenant_key not in self._tenants:
            raise NotFoundError("Tenant", tenant_key)
        return self._tenants[tenant_key]

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        for tenant in self._tenants.values():
            if tenant.slug == slug:
                return tenant
        raise NotFoundError("Tenant", slug)

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        active = self._memberships.get((user_key, tenant_key))
        return None if active is None else SimpleNamespace(is_active=active)


def _service() -> tuple[AuthService, list[ApiKey]]:
    stored: list[ApiKey] = []
    api_key_repo = MagicMock()

    def _create(key: ApiKey) -> ApiKey:
        stored.append(key)
        return key.model_copy(update={"key": "ak-1"})

    api_key_repo.create.side_effect = _create
    service = AuthService(
        user_repo=MagicMock(),
        auth_provider_repo=MagicMock(),
        refresh_token_repo=MagicMock(),
        password_engine=PasswordEngine(),
        token_engine=TokenEngine("test-secret-key-for-unit-tests-32chars!", "HS256"),
        throttle_engine=LoginThrottleEngine(),
        email_service=MagicMock(),
        frontend_url="http://localhost:5173",
        tenant_service=_TenantService(),  # type: ignore[arg-type]
        api_key_repo=api_key_repo,
    )
    return service, stored


@pytest.mark.parametrize("typed", ["club-a", "tenant_a", " club-a "], ids=["slug", "key", "padded-slug"])
def test_the_scope_is_stored_as_the_tenant_key(typed: str) -> None:
    service, stored = _service()

    created = service.create_api_key(_OWNER, "ha", typed)

    assert stored[0].tenant_scope == "tenant_a"
    assert created.tenant_scope == "tenant_a"


@pytest.mark.parametrize(
    "typed",
    ["no-such-tenant", "club-b", "tenant_b", "closed", "left", "tenants/tenant_a", "../x", "a b"],
    ids=[
        "unknown",
        "foreign-slug",
        "foreign-key",
        "inactive-tenant",
        "inactive-membership",
        "id-form",
        "path",
        "space",
    ],
)
def test_a_scope_the_caller_cannot_act_in_is_refused_with_one_answer(typed: str) -> None:
    service, stored = _service()

    with pytest.raises(ForbiddenError) as refused:
        service.create_api_key(_OWNER, "ha", typed)

    assert refused.value.message == ("tenant_scope must name a tenant you are an active member of.")
    assert stored == []


@pytest.mark.parametrize("typed", [None, "", "   "])
def test_no_scope_stays_unscoped(typed: str | None) -> None:
    service, stored = _service()

    service.create_api_key(_OWNER, "ha", typed)

    assert stored[0].tenant_scope is None


def test_the_predicate_matches_the_tenant_key_only() -> None:
    assert api_key_scope_admits("tenant_a", tenant_key="tenant_a") is True
    assert api_key_scope_admits("club-a", tenant_key="tenant_a") is False
    assert api_key_scope_admits(None, tenant_key="tenant_a") is True


def test_the_tenant_erasure_removes_a_key_created_with_the_tenants_slug() -> None:
    # The executor deletes ``api_keys`` rows where ``doc[tenant_field] ==
    # <erased tenant key>`` (tenant_erasure_executor._match). A key created
    # with the slug must therefore carry the key in exactly that field.
    service, stored = _service()
    service.create_api_key(_OWNER, "ha", "club-a")
    entry = next(e for e in TenantErasureEngine.INVENTORY if e.collection == "api_keys")

    doc = stored[0].model_dump(by_alias=True)

    assert entry.action == "delete"
    assert doc[entry.tenant_field] == "tenant_a"
