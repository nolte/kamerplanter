"""An API key's ``tenant_scope`` binds on the REST tenant resolvers too — #1817.

A key can be restricted to one tenant (``ApiKey.tenant_scope``, REQ-023). Until
#1817 only the MCP authenticator read that restriction: on the REST path
``FullAuthProvider.resolve_user`` turned a ``kp_`` key into its owning account,
and every tenant decision after that was made on the *account's* memberships. A
key scoped to tenant A therefore acted in tenant B wherever its owner was a
member of B.

The restriction is enforced where an untrusted tenant choice becomes a tenant —
:func:`~app.common.auth._membership_for_slug` — so the ``/t/{slug}/`` path
surface and the ``X-Active-Tenant`` header surface refuse identically, plus the
header-less personal fallback, which names a tenant without going through a slug.

Every case below is driven with a real :class:`~app.domain.models.user.User`
(never a namespace double): the scope travels on it, and a double that simply
lacked the attribute would accept a shape the real model can never produce.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.common import auth as auth_mod
from app.common.enums import TenantRole
from app.common.exceptions import ForbiddenError, KamerplanterError, NotFoundError
from app.domain.models.user import User

_SCOPED = SimpleNamespace(key="tenant_a", slug="club-a")
_OTHER = SimpleNamespace(key="tenant_b", slug="club-b")
_PERSONAL = SimpleNamespace(key="tenant_p", slug="personal-owner")


def _membership(role: TenantRole = TenantRole.LEAD) -> SimpleNamespace:
    return SimpleNamespace(role=role, admin_scopes=[], is_active=True)


class _TenantService:
    """The owner is an active lead in **all three** tenants.

    That is the precondition of the defect: a refusal on ``club-b`` must come
    from the key's scope, never from a missing membership.
    """

    _by_slug = {t.slug: t for t in (_SCOPED, _OTHER, _PERSONAL)}

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        tenant = self._by_slug.get(slug)
        if tenant is None:
            raise NotFoundError("Tenant", slug)
        return tenant

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        if user_key == "owner" and tenant_key in {"tenant_a", "tenant_b", "tenant_p"}:
            return _membership()
        return None

    def get_personal_tenant(self, user_key: str) -> SimpleNamespace | None:
        return _PERSONAL if user_key == "owner" else None


def _owner(scope: str | None) -> User:
    return User(_key="owner", email="owner@example.org", display_name="Owner").with_api_key_tenant_scope(scope)


def _error(call: Any) -> KamerplanterError:
    with pytest.raises(KamerplanterError) as exc_info:
        call()
    return exc_info.value


def _path(slug: str, user: User) -> Any:
    return auth_mod.get_current_tenant(tenant_slug=slug, user=user, tenant_service=_TenantService())


def _header_key(slug: str | None, user: User) -> str:
    return auth_mod.get_active_tenant_key(user=user, tenant_service=_TenantService(), active_tenant_slug=slug)


def _header_ctx(slug: str | None, user: User) -> Any:
    return auth_mod.get_active_tenant_context(user=user, tenant_service=_TenantService(), active_tenant_slug=slug)


# ── The defect: a scoped key acting in another of its owner's tenants ────────


def test_a_key_scoped_to_a_is_refused_on_the_path_of_b():
    error = _error(lambda: _path("club-b", _owner("club-a")))

    assert isinstance(error, ForbiddenError)
    assert error.status_code == 403


@pytest.mark.parametrize("resolver", [_header_key, _header_ctx], ids=["key", "context"])
def test_a_key_scoped_to_a_is_refused_on_the_header_of_b(resolver: Any):
    error = _error(lambda: resolver("club-b", _owner("club-a")))

    assert isinstance(error, ForbiddenError)
    assert error.status_code == 403


def test_the_refusal_is_the_same_answer_as_for_a_non_member():
    """No new oracle: a scoped-out tenant must look exactly like a foreign one."""
    scoped_out = _error(lambda: _path("club-b", _owner("club-a")))
    unknown = _error(lambda: _path("no-such-club", _owner(None)))

    assert (scoped_out.status_code, scoped_out.error_code, scoped_out.message, scoped_out.details) == (
        unknown.status_code,
        unknown.error_code,
        unknown.message,
        unknown.details,
    )


def test_without_a_header_a_scoped_key_does_not_fall_back_into_the_personal_tenant():
    # The personal fallback names a tenant without a slug, so it bypasses the
    # slug check — the scope must bind here as well, narrowing to global scope.
    assert _header_key(None, _owner("club-a")) == ""
    ctx = _header_ctx(None, _owner("club-a"))
    assert ctx.tenant_key == ""
    assert ctx.role is TenantRole.VIEWER


# ── Non-vacuity: the scoped tenant itself, and unscoped callers, still work ──


@pytest.mark.parametrize("scope", ["club-a", "tenant_a"], ids=["slug", "key"])
def test_the_scoped_tenant_itself_resolves_by_slug_or_key(scope: str):
    # The MCP authenticator matches a scope on slug *or* key; REST must agree.
    ctx = _path("club-a", _owner(scope))
    assert ctx.tenant_key == "tenant_a"
    assert _header_key("club-a", _owner(scope)) == "tenant_a"


def test_a_key_scoped_to_the_personal_tenant_keeps_the_header_less_fallback():
    assert _header_key(None, _owner("personal-owner")) == "tenant_p"


def test_an_unscoped_caller_still_reaches_every_tenant_of_the_owner():
    assert _path("club-b", _owner(None)).tenant_key == "tenant_b"
    assert _header_key("club-b", _owner(None)) == "tenant_b"
    assert _header_key(None, _owner(None)) == "tenant_p"


def test_the_scope_is_request_state_and_never_serialised():
    # It rides on the principal for one request; a write-back of the account
    # (``model_dump``) must not persist one request's credential restriction.
    principal = _owner("club-a")
    assert principal.api_key_tenant_scope == "club-a"
    assert "api_key_tenant_scope" not in principal.model_dump(by_alias=True)
    assert "club-a" not in principal.model_dump_json()


def test_a_stored_account_document_cannot_carry_a_scope_in():
    # The scope is set by API-key authentication only. A field of the same name
    # in a user document (or any validated payload) must not reach the resolvers.
    loaded = User.model_validate(
        {"_key": "owner", "email": "owner@example.org", "display_name": "Owner", "api_key_tenant_scope": "club-a"}
    )
    assert loaded.api_key_tenant_scope is None
