"""``X-Active-Tenant``: the org-context signal for global routes (#1091, R1-R3, ADR-009).

The species/cultivar/botanical-family/companion-planting catalogues are mounted
*globally* (no ``/t/{slug}/`` segment), so they carry no signal of *which* tenant
an organisation member is acting in. Before #1091 the resolver therefore always
answered the caller's **personal** tenant — the "known limitation (#808 A1)" the
docstring recorded. The ``X-Active-Tenant`` header (a tenant *slug*) is that
missing signal.

What this file pins, per input class:

* **no header** — byte-for-byte today's behaviour (personal tenant, ``""`` when
  there is none). Whitespace-only counts as no header;
* **valid header** — that tenant's key, and — decisively — the role of the
  membership *in that tenant* (an org viewer must never inherit the ``lead`` of
  their own personal tenant);
* **unknown slug** and **non-member / inactive membership** — 403 ``FORBIDDEN``,
  with **identical** bodies apart from ``error_id``. The natural implementation
  reuses :meth:`TenantService.get_tenant_by_slug`, which raises
  :class:`NotFoundError` (404) — and a leaking 404 *is* the tenant-existence
  oracle R2 forbids. That conversion is asserted on the status code, so the
  omission fails loudly rather than passing as "some 4xx";
* **non-divergence** — for every input class the key resolver and the context
  resolver agree (same key, or the same exception type). They share ONE internal
  resolution, so read scope and write stamping can never drift apart.
"""

from __future__ import annotations

import inspect
from types import SimpleNamespace
from typing import Any, get_args

import pytest
from fastapi import params as fastapi_params

from app.common import auth as auth_mod
from app.common.enums import AdminScope, TenantRole
from app.common.exceptions import ForbiddenError, KamerplanterError, NotFoundError
from app.config.settings import settings

# ── Fakes ────────────────────────────────────────────────────────────────────


def _user(key: str | None = "user_1") -> SimpleNamespace:
    return SimpleNamespace(key=key)


def _tenant(key: str, slug: str) -> SimpleNamespace:
    return SimpleNamespace(key=key, slug=slug)


def _membership(
    role: TenantRole = TenantRole.VIEWER,
    *,
    admin_scopes: list[AdminScope] | None = None,
    is_active: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(role=role, admin_scopes=admin_scopes or [], is_active=is_active)


class _FakeTenantService:
    """The slice of :class:`TenantService` the resolver calls, with call recording.

    ``get_tenant_by_slug`` raises :class:`NotFoundError` for an unknown slug —
    exactly what the real service does. That fidelity is the point of this
    double: a resolver that forwards the exception fails the 403 assertions.
    """

    def __init__(
        self,
        *,
        personal: SimpleNamespace | None = None,
        by_slug: dict[str, SimpleNamespace] | None = None,
        memberships: dict[tuple[str, str], SimpleNamespace] | None = None,
    ) -> None:
        self._personal = personal
        self._by_slug = dict(by_slug or {})
        self._memberships = dict(memberships or {})
        self.slug_lookups: list[str] = []
        self.personal_lookups: list[str] = []
        self.membership_lookups: list[tuple[str, str]] = []

    def get_personal_tenant(self, user_key: str) -> SimpleNamespace | None:
        self.personal_lookups.append(user_key)
        return self._personal

    def get_tenant_by_slug(self, slug: str) -> SimpleNamespace:
        self.slug_lookups.append(slug)
        tenant = self._by_slug.get(slug)
        if tenant is None:
            raise NotFoundError("tenants", slug)
        return tenant

    def get_membership(self, user_key: str, tenant_key: str) -> SimpleNamespace | None:
        self.membership_lookups.append((user_key, tenant_key))
        return self._memberships.get((user_key, tenant_key))


_PERSONAL = _tenant("tenant_personal_1", "user-1-garden")
_ORG = _tenant("tenant_org_1", "green-club")


def _service(**kwargs: Any) -> _FakeTenantService:
    """A service where the caller owns a personal tenant (lead) and an org exists."""
    defaults: dict[str, Any] = {
        "personal": _PERSONAL,
        "by_slug": {"user-1-garden": _PERSONAL, "green-club": _ORG},
        "memberships": {
            ("user_1", "tenant_personal_1"): _membership(TenantRole.LEAD, admin_scopes=[AdminScope.MANAGEMENT]),
            ("user_1", "tenant_org_1"): _membership(TenantRole.VIEWER),
        },
    }
    defaults.update(kwargs)
    return _FakeTenantService(**defaults)


def _error(call: Any) -> KamerplanterError:
    """Run ``call`` and return the raised application error."""
    with pytest.raises(KamerplanterError) as exc_info:
        call()
    return exc_info.value


def _body(error: KamerplanterError) -> tuple[int, str, str, list[dict[str, str]]]:
    """Everything a client sees except the per-occurrence ``error_id``."""
    return (error.status_code, error.error_code, error.message, error.details)


# ── AC 1 / AC 6 — no header keeps today's behaviour ──────────────────────────


def test_without_a_header_the_personal_tenant_still_wins():
    service = _service()

    assert auth_mod.get_active_tenant_key(user=_user(), tenant_service=service) == "tenant_personal_1"
    assert service.personal_lookups == ["user_1"]
    # No header → no slug lookup at all: the pre-#1091 code path is untouched.
    assert service.slug_lookups == []


def test_without_a_header_the_context_still_carries_the_personal_membership():
    service = _service()

    ctx = auth_mod.get_active_tenant_context(user=_user(), tenant_service=service)

    assert ctx.tenant_key == "tenant_personal_1"
    assert ctx.tenant_slug == "user-1-garden"
    assert ctx.role is TenantRole.LEAD
    assert ctx.admin_scopes == [AdminScope.MANAGEMENT]


def test_without_a_tenant_at_all_the_global_fallback_survives():
    service = _service(personal=None)

    assert auth_mod.get_active_tenant_key(user=_user(), tenant_service=service) == ""
    ctx = auth_mod.get_active_tenant_context(user=_user(), tenant_service=service)
    assert ctx.tenant_key == ""
    assert ctx.tenant_slug == ""
    assert ctx.role is TenantRole.VIEWER


@pytest.mark.parametrize("value", ["", " ", "\t", "   \n  "])
def test_an_empty_or_whitespace_header_counts_as_absent(value: str):
    # AC 6: a client that clears its active tenant may send the header empty
    # rather than omitting it. That is "no org context", not "a tenant named ''"
    # — treating it as a lookup would 403 every such caller out of the catalogue.
    service = _service()

    assert auth_mod.get_active_tenant_key(user=_user(), tenant_service=service, active_tenant_slug=value) == (
        "tenant_personal_1"
    )
    assert service.slug_lookups == []


# ── AC 2 — a valid header binds that tenant, with that tenant's role ─────────


def test_a_valid_header_resolves_that_tenants_key():
    service = _service()

    result = auth_mod.get_active_tenant_key(user=_user(), tenant_service=service, active_tenant_slug="green-club")

    assert result == "tenant_org_1"
    assert service.slug_lookups == ["green-club"]
    # The personal tenant is not even looked up — the header replaces it, it does
    # not union with it (the visibility direction #324 got wrong twice).
    assert service.personal_lookups == []


def test_a_valid_header_yields_the_org_role_never_the_personal_lead_role():
    # The single most valuable assertion in this file: an org *viewer* whose own
    # personal tenant makes them a *lead* must be a viewer while acting in the org.
    service = _service()

    ctx = auth_mod.get_active_tenant_context(user=_user(), tenant_service=service, active_tenant_slug="green-club")

    assert ctx.tenant_key == "tenant_org_1"
    assert ctx.tenant_slug == "green-club"
    assert ctx.user_key == "user_1"
    assert ctx.role is TenantRole.VIEWER
    assert ctx.admin_scopes == []


def test_admin_scopes_come_from_the_active_tenants_membership():
    service = _service(
        memberships={
            ("user_1", "tenant_personal_1"): _membership(TenantRole.LEAD),
            ("user_1", "tenant_org_1"): _membership(TenantRole.GROWER, admin_scopes=[AdminScope.TECHNICAL]),
        }
    )

    ctx = auth_mod.get_active_tenant_context(user=_user(), tenant_service=service, active_tenant_slug="green-club")

    assert ctx.role is TenantRole.GROWER
    assert ctx.admin_scopes == [AdminScope.TECHNICAL]


def test_surrounding_whitespace_in_the_header_is_stripped():
    service = _service()

    result = auth_mod.get_active_tenant_key(user=_user(), tenant_service=service, active_tenant_slug="  green-club  ")

    assert result == "tenant_org_1"


# ── AC 3 / AC 4 / AC 5 — the two invalid classes answer one 403 ─────────────


def test_an_unknown_slug_is_a_403_not_the_404_the_service_raises():
    # R-5, the predicted implementation defect: ``get_tenant_by_slug`` raises
    # NotFoundError(404). Forwarding it turns the resolver into a tenant-existence
    # oracle — "does 'competitor-gmbh' exist?" answered by any authenticated user.
    service = _service()

    error = _error(
        lambda: auth_mod.get_active_tenant_key(user=_user(), tenant_service=service, active_tenant_slug="no-such-org")
    )

    assert error.status_code == 403
    assert error.error_code == "FORBIDDEN"
    assert isinstance(error, ForbiddenError)
    assert "no-such-org" not in error.message


def test_a_non_member_is_refused_exactly_like_an_unknown_slug():
    # AC 4: same status, same code, same message, same details — only ``error_id``
    # differs, and that is per-occurrence, not per-case.
    service = _service(memberships={})

    unknown = _error(
        lambda: auth_mod.get_active_tenant_key(user=_user(), tenant_service=service, active_tenant_slug="no-such-org")
    )
    non_member = _error(
        lambda: auth_mod.get_active_tenant_key(user=_user(), tenant_service=service, active_tenant_slug="green-club")
    )

    assert _body(unknown) == _body(non_member)
    assert unknown.error_id != non_member.error_id


def test_an_inactive_membership_is_refused_like_a_non_member():
    service = _service(
        memberships={("user_1", "tenant_org_1"): _membership(TenantRole.GROWER, is_active=False)},
    )

    error = _error(
        lambda: auth_mod.get_active_tenant_key(user=_user(), tenant_service=service, active_tenant_slug="green-club")
    )

    assert error.status_code == 403


def test_a_keyless_caller_may_not_claim_an_org_via_the_header():
    # An anonymous/light caller has no membership anywhere, so a header naming a
    # real tenant must be refused rather than granting its scope.
    service = _service()

    error = _error(
        lambda: auth_mod.get_active_tenant_key(
            user=_user(key=None), tenant_service=service, active_tenant_slug="green-club"
        )
    )

    assert error.status_code == 403


@pytest.mark.parametrize("slug", ["no-such-org", "green-club"])
@pytest.mark.parametrize("resolver", ["get_active_tenant_key", "get_creating_tenant_key", "get_active_tenant_context"])
def test_an_invalid_header_never_silently_falls_back(resolver: str, slug: str):
    # AC 5: neither resolver may answer "personal" or "" for a header it could not
    # honour. A silent fallback would write rows into the wrong tenant — the exact
    # context confusion this feature exists to end.
    service = _service(memberships={})

    error = _error(lambda: getattr(auth_mod, resolver)(user=_user(), tenant_service=service, active_tenant_slug=slug))

    assert error.status_code == 403


# ── AC 7 — the write-stamping alias moves with the header ───────────────────


def test_the_creating_alias_is_still_the_same_function_object():
    assert auth_mod.get_creating_tenant_key is auth_mod.get_active_tenant_key


def test_the_creating_alias_stamps_the_header_tenant():
    service = _service()

    assert (
        auth_mod.get_creating_tenant_key(user=_user(), tenant_service=service, active_tenant_slug="green-club")
        == "tenant_org_1"
    )


# ── AC 8 — non-divergence between the key and the context resolver ──────────


@pytest.mark.parametrize(
    ("case", "slug"),
    [
        ("no header", None),
        ("blank header", "   "),
        ("valid header", "green-club"),
        ("unknown slug", "no-such-org"),
        ("non-member", "foreign-club"),
    ],
)
def test_key_and_context_resolvers_never_diverge(case: str, slug: str | None):
    """One shared resolution: same key, or the same failure, for every input class."""
    foreign = _tenant("tenant_foreign", "foreign-club")

    def _fresh() -> _FakeTenantService:
        return _service(by_slug={"user-1-garden": _PERSONAL, "green-club": _ORG, "foreign-club": foreign})

    try:
        key = auth_mod.get_active_tenant_key(user=_user(), tenant_service=_fresh(), active_tenant_slug=slug)
    except KamerplanterError as key_error:
        ctx_error = _error(
            lambda: auth_mod.get_active_tenant_context(user=_user(), tenant_service=_fresh(), active_tenant_slug=slug)
        )
        assert type(ctx_error) is type(key_error), case
        assert _body(ctx_error) == _body(key_error), case
        return

    ctx = auth_mod.get_active_tenant_context(user=_user(), tenant_service=_fresh(), active_tenant_slug=slug)
    assert ctx.tenant_key == key, case


# ── AC 9 — light mode (REQ-027), both arms ──────────────────────────────────
#
# The light-mode seed (``app/migrations/seed_light_mode.py`` +
# ``seed_data/light_mode.yaml``) creates the system user, the ``system-tenant``
# with slug ``mein-garten``, and an active ``lead`` membership between them. The
# frontend sends that slug in light mode too (operator decision Q2), so this arm
# is production traffic, not a thought experiment.


def _light_mode_service() -> _FakeTenantService:
    system_tenant = _tenant("system-tenant", "mein-garten")
    return _FakeTenantService(
        personal=system_tenant,
        by_slug={"mein-garten": system_tenant},
        memberships={
            ("system-user", "system-tenant"): _membership(
                TenantRole.LEAD, admin_scopes=[AdminScope.MANAGEMENT, AdminScope.TECHNICAL]
            )
        },
    )


def test_light_mode_accepts_the_seeded_slug(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    service = _light_mode_service()

    key = auth_mod.get_active_tenant_key(
        user=_user(key="system-user"), tenant_service=service, active_tenant_slug="mein-garten"
    )
    ctx = auth_mod.get_active_tenant_context(
        user=_user(key="system-user"), tenant_service=service, active_tenant_slug="mein-garten"
    )

    assert key == "system-tenant"
    assert ctx.tenant_key == "system-tenant"
    assert ctx.tenant_slug == "mein-garten"
    assert ctx.role is TenantRole.LEAD


def test_light_mode_without_the_header_is_unchanged(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "kamerplanter_mode", "light")
    service = _light_mode_service()

    assert auth_mod.get_active_tenant_key(user=_user(key="system-user"), tenant_service=service) == "system-tenant"
    assert service.slug_lookups == []


# ── AC 10 — the header is a declared FastAPI parameter (OpenAPI surface) ────


@pytest.mark.parametrize("resolver", ["get_active_tenant_key", "get_active_tenant_context"])
def test_the_header_is_declared_as_a_fastapi_header_parameter(resolver: str):
    # Declared, not read off ``Request``: only a declared parameter reaches the
    # generated OpenAPI document, and the document is what tells a client (and the
    # generated API types) that the header exists. (Asserted end-to-end against a
    # real generated document in ``tests/api/test_active_tenant_header_api.py``.)
    parameter = inspect.signature(getattr(auth_mod, resolver)).parameters["active_tenant_slug"]
    markers = [m for m in get_args(parameter.annotation) if isinstance(m, fastapi_params.Header)]

    assert len(markers) == 1
    assert markers[0].alias == auth_mod.ACTIVE_TENANT_HEADER == "X-Active-Tenant"
    # The Python default stays a real ``None`` (Annotated form), so the resolver is
    # still callable as a plain function — the calling convention of every unit
    # test here and of the two pre-#1091 modules.
    assert parameter.default is None
