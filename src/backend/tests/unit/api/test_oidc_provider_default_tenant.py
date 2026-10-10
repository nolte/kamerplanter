"""#2182 security review SEC-001 / SEC-002 - an OIDC provider's ``default_tenant_key`` is checked when written.

Before: the value was stored as typed, behind the step-up, and only the sign-in decided - silently -
whether it could be used. A default tenant on Google, GitHub or Apple (where anybody can create an
identity) let everybody join the tenant; a personal tenant, the platform tenant or a key that names
no tenant was stored and never reported. The response did not show the field, and a partial update
(``exclude_none``) could not remove it again.

Now, through the real router, service and step-up (the admin's password):

* only a generic ``oidc`` provider may carry one - 422 on create, on update, and on an update that
  switches a provider *with* a default tenant to an open-registration type;
* the tenant exists, is not personal and is not the platform tenant - 422 otherwise;
* all of it before the step-up, so a refused request spends no attempt and writes nothing;
* the response carries the field, and ``null`` or ``""`` clears it.
"""

from __future__ import annotations

from typing import Any

import pytest

from app.common.enums import TenantType
from app.domain.models.tenant import Tenant
from tests.unit.api.test_oidc_provider_step_up import NEW_PROVIDER, PASSWORD, ROUTE, _World

ORG = "t-club"


def _tenant(key: str) -> Tenant | None:
    shapes: dict[str, dict[str, Any]] = {
        ORG: {"tenant_type": TenantType.ORGANIZATION},
        "t-personal": {"tenant_type": TenantType.PERSONAL},
        "platform": {"tenant_type": TenantType.ORGANIZATION, "is_platform": True},
    }
    if key not in shapes:
        return None
    return Tenant.model_validate({"_key": key, "name": key, "slug": key, "owner_user_key": "u-lead", **shapes[key]})


def _world() -> _World:
    world = _World()
    world.tenants.get_by_key.side_effect = _tenant
    return world


def _confirmed(body: dict[str, Any]) -> dict[str, Any]:
    return {**body, "current_password": PASSWORD}


# ── what is refused ──────────────────────────────────────────────────────────


@pytest.mark.parametrize("provider_type", ["google", "github", "apple"])
def test_an_open_registration_provider_cannot_carry_a_default_tenant(provider_type: str) -> None:
    world = _world()
    body = {
        **NEW_PROVIDER,
        "provider_type": provider_type,
        "default_tenant_key": ORG,
        "scopes": ["openid", "user:email"],
    }

    resp = world.call("POST", ROUTE, _confirmed(body))

    assert resp.status_code == 422, resp.text
    assert "generic OIDC provider" in resp.json()["message"]
    assert world.configs.writes == []


@pytest.mark.parametrize(
    ("tenant_key", "why"),
    [
        ("t-unknown", "no tenant has this key"),
        ("t-personal", "a personal tenant"),
        ("platform", "the platform tenant"),
    ],
)
def test_an_unfit_tenant_is_refused_on_create_and_on_update(tenant_key: str, why: str) -> None:
    world = _world()

    created = world.call("POST", ROUTE, _confirmed({**NEW_PROVIDER, "default_tenant_key": tenant_key}))
    updated = world.call("PUT", f"{ROUTE}/key-corp", _confirmed({"default_tenant_key": tenant_key}))

    assert (created.status_code, updated.status_code) == (422, 422), (created.text, updated.text)
    assert why in created.json()["message"]
    assert world.configs.writes == []
    assert world.configs.rows["key-corp"].default_tenant_key is None


def test_switching_a_provider_with_a_default_tenant_to_google_is_refused() -> None:
    world = _world()
    world.configs.rows["key-corp"] = world.configs.rows["key-corp"].model_copy(update={"default_tenant_key": ORG})

    resp = world.call("PUT", f"{ROUTE}/key-corp", _confirmed({"provider_type": "google"}))

    assert resp.status_code == 422, resp.text
    assert world.configs.rows["key-corp"].provider_type == "oidc"


def test_the_refusal_comes_before_the_step_up_and_spends_no_attempt() -> None:
    world = _world()
    for _ in range(6):
        resp = world.call("PUT", f"{ROUTE}/key-corp", {"default_tenant_key": "t-personal", "current_password": "wrong"})
        assert resp.status_code == 422, resp.text

    # Six refusals before the step-up: the throttle (five failures lock it) was never asked.
    assert world.call("PUT", f"{ROUTE}/key-corp", _confirmed({"default_tenant_key": ORG})).status_code == 200


def test_an_unrelated_edit_is_not_blocked_by_a_default_tenant_deleted_since() -> None:
    world = _world()
    world.configs.rows["key-corp"] = world.configs.rows["key-corp"].model_copy(
        update={"default_tenant_key": "t-deleted-meanwhile"}
    )

    resp = world.call("PUT", f"{ROUTE}/key-corp", _confirmed({"client_id": "rotated"}))

    assert resp.status_code == 200, resp.text


# ── what is stored, shown and cleared ────────────────────────────────────────


def test_an_organisation_on_a_generic_provider_is_stored_and_shown() -> None:
    world = _world()

    created = world.call("POST", ROUTE, _confirmed({**NEW_PROVIDER, "default_tenant_key": f"  {ORG} "}))

    assert created.status_code == 201, created.text
    assert created.json()["default_tenant_key"] == ORG
    key = created.json()["key"]
    assert world.call("GET", f"{ROUTE}/{key}").json()["default_tenant_key"] == ORG
    assert all("default_tenant_key" in row for row in world.call("GET", ROUTE).json())


@pytest.mark.parametrize("cleared", [None, "", "   "], ids=["null", "empty", "blank"])
def test_null_or_empty_clears_the_default_tenant(cleared: str | None) -> None:
    world = _world()
    world.configs.rows["key-corp"] = world.configs.rows["key-corp"].model_copy(update={"default_tenant_key": ORG})

    resp = world.call("PUT", f"{ROUTE}/key-corp", _confirmed({"default_tenant_key": cleared}))

    assert resp.status_code == 200, resp.text
    assert resp.json()["default_tenant_key"] is None
    assert world.configs.rows["key-corp"].default_tenant_key is None
    assert world.configs.writes == ["update:key-corp"]


def test_a_field_not_sent_leaves_the_default_tenant_alone() -> None:
    world = _world()
    world.configs.rows["key-corp"] = world.configs.rows["key-corp"].model_copy(update={"default_tenant_key": ORG})

    resp = world.call("PUT", f"{ROUTE}/key-corp", {"display_name": "Corporate"})

    assert resp.status_code == 200, resp.text
    assert world.configs.rows["key-corp"].default_tenant_key == ORG


def test_clearing_needs_the_step_up_like_setting_it() -> None:
    """Whom a sign-in lets in is not presentation (D6): removing the join is a change of it too."""
    world = _world()
    world.configs.rows["key-corp"] = world.configs.rows["key-corp"].model_copy(update={"default_tenant_key": ORG})

    resp = world.call("PUT", f"{ROUTE}/key-corp", {"default_tenant_key": None})

    assert resp.status_code == 401, resp.text
    assert world.configs.rows["key-corp"].default_tenant_key == ORG
