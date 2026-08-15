"""Service accounts in the active-tenant mechanism (#1122, REQ-049 §2.11).

#1091 introduced ``X-Active-Tenant`` and resolved it from the caller's
**membership**. Service accounts (``account_type='service'`` — the REQ-023 M2M
integrations: Home Assistant, Grafana, CI/CD) were deliberately scoped out, so
their behaviour on the global catalogue routes was undefined.

The decision, recorded on the issue: **model real memberships.** A service account
participates exactly like an interactive caller — it must hold an explicit, active
membership in the tenant it names, and a tenant it is not a member of is
indistinguishable from one that does not exist. It differs in exactly one respect:

* **no personal-tenant fallback.** With no header it resolves to ``""``, global
  scope. "Which tenant did this machine mean?" has no implicit answer, so the
  answer is none.

That single exception is the reason this file exists. Today nothing creates a
personal tenant for a service account, so the fallback returns ``None`` anyway and
the behaviour would look identical without the rule — which is exactly what makes
it worth pinning. The tests below therefore give the service account a personal
tenant *in the fixture*, so the assertion measures the rule and not the absence of
data. Without that, every one of them would pass against a resolver that has no
service-account branch at all.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.common import auth as auth_mod
from app.common.auth import ACTIVE_TENANT_HEADER, get_active_tenant_key
from app.common.dependencies import get_tenant_service
from app.common.enums import TenantRole, TenantType
from app.common.error_handlers import app_error_handler
from app.common.exceptions import KamerplanterError, NotFoundError
from app.domain.models.tenant import Tenant

_ORG = Tenant(
    key="tenant_org",
    name="Community Garden",
    slug="org",
    tenant_type=TenantType.ORGANIZATION,
    owner_user_key="owner",
)
_MACHINE_PERSONAL = Tenant(
    key="tenant_machine_personal",
    name="svc",
    slug="svc-personal",
    tenant_type=TenantType.PERSONAL,
    owner_user_key="acct",
)


class _FakeTenantService:
    """Resolves slugs and memberships from explicit fixtures.

    ``personal`` is handed in per test rather than assumed absent: the whole point
    of the service-account rule is what happens when one *does* exist.
    """

    def __init__(self, *, memberships: dict[tuple[str, str], TenantRole], personal: Tenant | None) -> None:
        self._memberships = memberships
        self._personal = personal

    def get_tenant_by_slug(self, slug: str) -> Tenant:
        for tenant in (_ORG, _MACHINE_PERSONAL):
            if tenant.slug == slug:
                return tenant
        raise NotFoundError("Tenant", slug)

    def get_membership(self, user_key: str, tenant_key: str):
        role = self._memberships.get((user_key, tenant_key))
        return SimpleNamespace(role=role, is_active=True, admin_scopes=[]) if role else None

    def get_personal_tenant(self, user_key: str) -> Tenant | None:
        return self._personal


def _client(
    *,
    account_type: str,
    memberships: dict[tuple[str, str], TenantRole] | None = None,
    personal: Tenant | None = None,
) -> TestClient:
    app = FastAPI()
    app.add_exception_handler(KamerplanterError, app_error_handler)  # type: ignore[arg-type]

    @app.get("/probe")
    def probe(tenant_key: str = Depends(get_active_tenant_key)) -> dict[str, str]:
        """Stands in for any global catalogue route: it reports the resolved key.

        Asserting on the key rather than on a catalogue's contents keeps this
        about the resolver — the routes that depend on it are covered by
        ``test_active_tenant_header_scope_api.py``.
        """
        return {"tenant_key": tenant_key}

    service = _FakeTenantService(memberships=memberships or {}, personal=personal)
    app.dependency_overrides[auth_mod.get_current_user] = lambda: SimpleNamespace(key="acct", account_type=account_type)
    app.dependency_overrides[get_tenant_service] = lambda: service
    return TestClient(app)


# ── the one difference: no personal fallback ─────────────────────────────────


def test_a_header_less_service_account_gets_global_scope_even_with_a_personal_tenant() -> None:
    """The rule, measured against the case that could break it.

    The fixture deliberately gives the service account a personal tenant. A
    resolver without the service-account branch would return that key here and the
    machine would silently act inside a tenant — the widening §2.11 forbids.
    """
    client = _client(account_type="service", personal=_MACHINE_PERSONAL)

    response = client.get("/probe")

    assert response.status_code == 200, response.text
    assert response.json() == {"tenant_key": ""}


def test_an_interactive_caller_still_falls_back_to_their_personal_tenant() -> None:
    """The counterfactual half: the rule must not have narrowed everybody.

    Identical fixture, only ``account_type`` differs. If this asserted nothing, a
    resolver that returned ``""`` for *every* header-less caller would pass the
    test above and break every single-tenant client.
    """
    client = _client(account_type="user", personal=_MACHINE_PERSONAL)

    assert client.get("/probe").json() == {"tenant_key": _MACHINE_PERSONAL.key}


# ── everything else: exactly like an interactive caller ──────────────────────


def test_a_service_account_with_a_real_membership_may_act_in_that_tenant() -> None:
    """ "Model real memberships" is the decision — so a granted machine works."""
    client = _client(
        account_type="service",
        memberships={("acct", _ORG.key): TenantRole.GROWER},
        personal=_MACHINE_PERSONAL,
    )

    response = client.get("/probe", headers={ACTIVE_TENANT_HEADER: _ORG.slug})

    assert response.status_code == 200, response.text
    assert response.json() == {"tenant_key": _ORG.key}


def test_a_service_account_without_the_membership_is_refused() -> None:
    """Not silently ignored and not fallen back on: refused.

    Ignoring an unhonourable header would make the machine act in global scope
    while believing it acts in the org — the silent context confusion the whole
    mechanism removes.
    """
    client = _client(account_type="service", personal=_MACHINE_PERSONAL)

    response = client.get("/probe", headers={ACTIVE_TENANT_HEADER: _ORG.slug})

    assert response.status_code == 403, response.text


@pytest.mark.parametrize("slug", ["org", "does-not-exist"])
def test_the_two_refusals_are_byte_identical_for_a_service_account(slug: str) -> None:
    """No tenant-existence oracle, on this surface either.

    A machine account is the *easier* thing to point at a slug list, so the
    property that "unknown tenant" and "not a member" answer identically has to
    hold here as much as for a browser session.
    """
    client = _client(account_type="service", personal=_MACHINE_PERSONAL)

    response = client.get("/probe", headers={ACTIVE_TENANT_HEADER: slug})

    assert response.status_code == 403
    assert _comparable(response.json()) == _EXPECTED_DENIAL


def test_a_service_account_cannot_reach_its_own_personal_tenant_by_naming_it() -> None:
    """The fallback is removed, not merely made implicit.

    Without this, a machine could recover the personal-tenant scope simply by
    sending its slug — and the rule above would be a speed bump rather than a
    boundary. It holds because the header path demands a membership, and a
    service account has none in a tenant nobody enrolled it in.
    """
    client = _client(account_type="service", personal=_MACHINE_PERSONAL)

    response = client.get("/probe", headers={ACTIVE_TENANT_HEADER: _MACHINE_PERSONAL.slug})

    assert response.status_code == 403, response.text


def _comparable(body: dict) -> dict:
    """The refusal body minus its per-request identifiers.

    ``error_id`` and ``timestamp`` differ between any two requests by design.
    Dropping exactly those two — rather than comparing a hand-picked subset —
    keeps every remaining field, including ``message`` and ``details``, inside the
    comparison: those are where a slug would leak if one ever did.
    """
    return {k: v for k, v in body.items() if k not in ("error_id", "timestamp")}


_EXPECTED_DENIAL: dict = {}


@pytest.fixture(autouse=True)
def _capture_denial_body() -> None:
    """Fill ``_EXPECTED_DENIAL`` from the *unknown-slug* refusal.

    Hard-coding the expected body would let the two refusals drift together
    unnoticed if the message were edited in one place; deriving it from one case
    and comparing the other against it keeps the assertion about their *equality*,
    which is the property that matters.
    """
    client = _client(account_type="service", personal=_MACHINE_PERSONAL)
    _EXPECTED_DENIAL.clear()
    _EXPECTED_DENIAL.update(_comparable(client.get("/probe", headers={ACTIVE_TENANT_HEADER: "no-such-tenant"}).json()))
