"""``/t/{slug}/`` must not be a tenant-existence oracle either (#1091 A-11, ADR-009).

:func:`~app.common.auth.get_active_tenant_key` (A-2) already answers **one**
indistinguishable 403 for the two invalid header cases — "no such tenant" and
"you are not in it". The *path*-bound sibling :func:`get_current_tenant` did not:
it forwarded the :class:`NotFoundError` that
:meth:`TenantService.get_tenant_by_slug` raises, so a caller could tell the two
apart by status code alone::

    GET /api/v1/t/competitor-gmbh/sites  → 404  "tenants with key '…' not found."
    GET /api/v1/t/green-club/sites       → 403  "You are not a member of this tenant."

That is a slug-existence oracle on every one of the ~54 tenant-scoped routers,
and — worse than the header case — the 404 body *named the probed slug* in both
``message`` and ``details``. This module pins the alignment at the decision
level; ``tests/api/test_path_tenant_oracle_api.py`` pins it through real HTTP.

The load-bearing assertion here is the last one: the refusal of the *path*
surface and the refusal of the *header* surface must be the same object shape,
byte for byte. Two surfaces that refuse "differently but both with 403" would let
a caller correlate them, and would drift apart at the next edit — which is why
both raise sites go through one helper and one message constant.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.common import auth as auth_mod
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import ForbiddenError, KamerplanterError, NotFoundError

# ── Fakes (deliberately the same shapes A-2's unit module uses) ──────────────


def _user(key: str | None = "user_1") -> SimpleNamespace:
    return SimpleNamespace(key=key)


def _tenant(key: str, slug: str) -> SimpleNamespace:
    return SimpleNamespace(key=key, slug=slug)


def _membership(
    role: TenantRole = TenantRole.GROWER,
    *,
    admin_scopes: list[AdminScope] | None = None,
    is_active: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(role=role, admin_scopes=admin_scopes or [], is_active=is_active)


class _FakeTenantService:
    """The slice of :class:`TenantService` the resolver calls.

    ``get_tenant_by_slug`` raises :class:`NotFoundError` for an unknown slug —
    exactly what the real service does. That fidelity is the whole point: a
    resolver that forwards the exception fails the 403 assertions below instead
    of quietly passing as "some 4xx".
    """

    def __init__(
        self,
        *,
        by_slug: dict[str, SimpleNamespace] | None = None,
        memberships: dict[tuple[str, str], SimpleNamespace] | None = None,
    ) -> None:
        self._by_slug = dict(by_slug or {})
        self._memberships = dict(memberships or {})

    def get_personal_tenant(self, user_key: str) -> SimpleNamespace | None:  # pragma: no cover - not on this path
        raise AssertionError("the path-bound resolver must never fall back to the personal tenant")

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        tenant = self._by_slug.get(slug)
        if tenant is None:
            raise NotFoundError("tenants", slug)
        return tenant

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        return self._memberships.get((user_key, tenant_key))


_OWN = _tenant("tenant_own", "green-club")
_FOREIGN = _tenant("tenant_foreign", "foreign-club")


def _service(**kwargs: Any) -> _FakeTenantService:
    defaults: dict[str, Any] = {
        "by_slug": {"green-club": _OWN, "foreign-club": _FOREIGN},
        "memberships": {
            ("user_1", "tenant_own"): _membership(TenantRole.GROWER, admin_scopes=[AdminScope.TECHNICAL]),
        },
    }
    defaults.update(kwargs)
    return _FakeTenantService(**defaults)


def _error(call: Any) -> KamerplanterError:
    with pytest.raises(KamerplanterError) as exc_info:
        call()
    return exc_info.value


def _body(error: KamerplanterError) -> tuple[int, str, str, list[dict[str, str]]]:
    """Everything a client sees except the per-occurrence ``error_id``."""
    return (error.status_code, error.error_code, error.message, error.details)


def _resolve(slug: str, service: _FakeTenantService, user: SimpleNamespace | None = None) -> Any:
    return auth_mod.get_current_tenant(tenant_slug=slug, user=user or _user(), tenant_service=service)


# ── The valid case is untouched (non-vacuity guard) ──────────────────────────


def test_a_member_still_resolves_their_tenant_and_role():
    ctx = _resolve("green-club", _service())

    assert ctx.tenant_key == "tenant_own"
    assert ctx.tenant_slug == "green-club"
    assert ctx.user_key == "user_1"
    assert ctx.role is TenantRole.GROWER
    assert ctx.admin_scopes == [AdminScope.TECHNICAL]


# ── The two invalid classes answer one 403 ──────────────────────────────────


def test_an_unknown_slug_is_a_403_not_the_404_the_service_raises():
    # The A-11 red-first case: before the alignment this raised NotFoundError
    # (404) whose message and details both spelled out the probed slug.
    error = _error(lambda: _resolve("no-such-org", _service()))

    assert error.status_code == 403
    assert error.error_code == "FORBIDDEN"
    assert isinstance(error, ForbiddenError)


def test_a_non_member_is_refused_exactly_like_an_unknown_slug():
    service = _service()

    unknown = _error(lambda: _resolve("no-such-org", service))
    non_member = _error(lambda: _resolve("foreign-club", service))

    assert _body(unknown) == _body(non_member)
    assert unknown.error_id != non_member.error_id


def test_an_inactive_membership_is_refused_like_a_non_member():
    service = _service(memberships={("user_1", "tenant_own"): _membership(is_active=False)})

    error = _error(lambda: _resolve("green-club", service))

    assert error.status_code == 403


def test_a_keyless_caller_is_refused_rather_than_granted_the_tenant():
    # An anonymous caller holds no membership anywhere; a slug in the path must
    # not become standing in that tenant.
    error = _error(lambda: _resolve("green-club", _service(), user=_user(key=None)))

    assert error.status_code == 403


@pytest.mark.parametrize(("case", "slug"), [("unknown slug", "no-such-org"), ("non-member", "foreign-club")])
def test_neither_refusal_names_the_probed_slug(case: str, slug: str):
    # The old 404 body was ``tenants with key 'foo' not found.`` plus a details
    # entry repeating it — the probe answered itself even without reading the
    # status code.
    error = _error(lambda: _resolve(slug, _service()))

    assert slug not in error.message, case
    assert slug not in str(error.details), case


# ── The decisive property: both surfaces refuse identically ─────────────────


@pytest.mark.parametrize(("case", "slug"), [("unknown slug", "no-such-org"), ("non-member", "foreign-club")])
def test_the_path_refusal_is_identical_to_the_header_refusal(case: str, slug: str):
    """A ``/t/{slug}/`` refusal and an ``X-Active-Tenant`` refusal are one answer.

    Same class, same status, same code, same message, same details. Two surfaces
    with two *different* 403s would still be correlatable — and would drift the
    moment one of them is edited. Both go through the same helper and the same
    :data:`~app.common.auth._ACTIVE_TENANT_DENIED` constant, so this holds by
    construction rather than by coincidence.
    """
    path_error = _error(lambda: _resolve(slug, _service()))
    header_error = _error(
        lambda: auth_mod.get_active_tenant_key(user=_user(), tenant_service=_service(), active_tenant_slug=slug)
    )

    assert type(path_error) is type(header_error), case
    assert _body(path_error) == _body(header_error), case
