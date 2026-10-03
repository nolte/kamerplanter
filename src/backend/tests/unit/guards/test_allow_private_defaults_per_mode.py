"""#1996 — every ``allow_private`` switch has a decided default in each deployment mode.

The class: a setting that lets a server-side request reach private address space
(LAN, the cluster's pod and service networks). Its default decides whether a
fresh full-mode deployment can be pointed at ArangoDB, Valkey or the API server.
This guard enumerates the class from ``Settings.model_fields`` (any field whose
name contains ``allow_private``), so a new switch fails here until its default
per mode is decided in :data:`DECIDED`, and pins the *effective* value — for
Apprise the mode-derived one from ``apprise_private_targets_allowed()``.

What it does not see: a private-address opt-in spelled without ``allow_private``
in its name, or one passed as an argument without a setting behind it
(``validate_oidc_fetch_url(..., allow_private=...)`` takes its value from the
OIDC provider record, not from settings).
"""

from __future__ import annotations

import pytest

from app.config.settings import Settings

#: field -> {mode: effective default with no env override}
DECIDED: dict[str, dict[str, bool]] = {
    "inventree_allow_private_endpoint": {"full": False, "light": False},
    "ha_allow_private_endpoint": {"full": False, "light": False},
    "storage_s3_allow_private_endpoint": {"full": False, "light": False},
    # User-typed targets; light mode is one user with a LAN Gotify/ntfy (REQ-030 §3.6).
    "apprise_allow_private_targets": {"full": False, "light": True},
}
#: Fields whose effective value is a method, not the raw field.
_EFFECTIVE = {"apprise_allow_private_targets": "apprise_private_targets_allowed"}


def _switches() -> set[str]:
    return {name for name in Settings.model_fields if "allow_private" in name}


def test_every_allow_private_switch_is_decided():
    assert _switches() == set(DECIDED), "decide the default per mode for each allow_private setting"
    assert len(DECIDED) == 4


@pytest.mark.parametrize("mode", ["full", "light"])
@pytest.mark.parametrize("field", sorted(DECIDED))
def test_the_effective_default_per_mode(monkeypatch, field, mode):
    monkeypatch.setenv("KAMERPLANTER_MODE", mode)
    monkeypatch.delenv(field.upper(), raising=False)
    loaded = Settings()
    method = _EFFECTIVE.get(field)
    effective = getattr(loaded, method)() if method else getattr(loaded, field)
    assert effective is DECIDED[field][mode], (field, mode)
