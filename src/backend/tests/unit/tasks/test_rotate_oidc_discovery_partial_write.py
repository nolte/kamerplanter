"""#1883 security review SEC-002, the scheduled sibling: the discovery refresh writes only the discovery fields.

``rotate_oidc_discovery`` reads every configuration once, then fetches each
issuer's discovery document in turn (each fetch up to its timeout, paced by the
issuer). Writing the whole snapshot back afterwards reverted whatever an admin
changed meanwhile — a provider switched off came back enabled, a rotated secret
came back old, and neither needed the step-up #1883 puts in front of those
changes. The refresh now merges only ``discovery_document`` and
``discovery_refreshed_at``.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from app.domain.models.oidc_config import OidcProviderConfig


def _config() -> OidcProviderConfig:
    return OidcProviderConfig.model_validate(
        {
            "_key": "cfg-1",
            "slug": "corp",
            "display_name": "Corp",
            "issuer_url": "https://corp.example.org",
            "client_id": "c",
            "enabled": True,
            "auto_discover": True,
        }
    )


def test_a_change_made_during_the_fetch_survives_the_refresh() -> None:
    from app.tasks.auth_tasks import rotate_oidc_discovery

    stored = {"cfg-1": _config()}
    discovery = {"issuer": "https://corp.example.org", "authorization_endpoint": "a", "token_endpoint": "t"}

    def update_fields(key: str, fields: dict[str, Any]) -> OidcProviderConfig:
        stored[key] = stored[key].model_copy(update=fields)
        return stored[key]

    def update(key: str, config: OidcProviderConfig) -> OidcProviderConfig:
        stored[key] = config
        return config

    repo = MagicMock(**{"list_all.return_value": [stored["cfg-1"]]})
    repo.update_fields.side_effect = update_fields
    repo.update.side_effect = update

    engine = MagicMock()

    def slow_fetch(_issuer: str) -> dict[str, Any]:
        # An admin switches the provider off while the refresh waits on the issuer.
        stored["cfg-1"] = stored["cfg-1"].model_copy(update={"enabled": False})
        return discovery

    engine.fetch_discovery_document.side_effect = slow_fetch

    with (
        patch("app.common.dependencies.get_oidc_config_repo", return_value=repo),
        patch("app.common.dependencies.get_oauth_engine", return_value=engine),
    ):
        result = rotate_oidc_discovery()

    assert result == {"updated": 1, "errors": 0}
    assert stored["cfg-1"].enabled is False, "the refresh wrote back its stale snapshot"
    assert stored["cfg-1"].discovery_document == discovery
