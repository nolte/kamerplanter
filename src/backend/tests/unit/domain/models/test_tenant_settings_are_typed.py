"""``Tenant.settings`` is a typed model, not ``dict[str, Any]`` — MT-056 (#2144).

Measured before typing it: no application path writes ``Tenant.settings`` (every
tenant is created with ``{}``); the one reader is the REQ-031 ``FeatureGuard``,
which read the ``ai_*`` keys with ``bool(raw.get(...))``. That turned a stored
string ``"false"`` into *enabled* — the KI features of a tenant switched on by the
spelling of "off". A future writer had nothing to validate against.

Decisions:

* the four REQ-031 §3.1 flags are typed fields with the guard's defaults;
* keys the model does not name are **preserved**, not rejected: no writer exists,
  so whatever a stored document carries was put there by hand or by an older
  build, and a model that dropped or refused it would lose it on the next write
  or fail every read of that tenant. No data migration is needed.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.common.exceptions import AiDisabledError
from app.domain.guards.feature_guard import FeatureGuard
from app.domain.models.tenant import Tenant, TenantSettings


def _tenant(settings: dict) -> Tenant:
    return Tenant(_key="t1", name="T", slug="t", owner_user_key="u1", settings=settings)


def test_a_stored_string_false_keeps_the_ai_features_off() -> None:
    tenant = _tenant({"ai_features_enabled": "false"})

    with pytest.raises(AiDisabledError):
        FeatureGuard.require_ai_enabled(tenant.settings)


def test_the_flags_are_typed() -> None:
    settings = _tenant({"ai_features_enabled": True, "ai_allow_cloud_providers": "true"}).settings

    assert isinstance(settings, TenantSettings)
    assert settings.ai_features_enabled is True
    assert settings.ai_allow_cloud_providers is True
    assert settings.ai_daily_tip_enabled is True  # the guard's default


def test_a_value_that_is_no_flag_is_refused() -> None:
    with pytest.raises(ValidationError):
        _tenant({"ai_features_enabled": "maybe"})


def test_an_empty_settings_object_reads_as_everything_off() -> None:
    settings = _tenant({}).settings

    assert FeatureGuard.extract_settings(settings).ai_features_enabled is False


def test_keys_the_model_does_not_name_survive_a_read_and_a_write() -> None:
    tenant = _tenant({"ai_features_enabled": True, "legacy_hand_set": {"x": 1}})

    dumped = tenant.model_dump(by_alias=True)

    assert dumped["settings"]["legacy_hand_set"] == {"x": 1}
    assert dumped["settings"]["ai_features_enabled"] is True


def test_the_guard_still_accepts_a_plain_dict() -> None:
    assert FeatureGuard.require_ai_enabled({"ai_features_enabled": True}).ai_features_enabled is True
