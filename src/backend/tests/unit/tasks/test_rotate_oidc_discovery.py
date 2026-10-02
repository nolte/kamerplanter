"""``rotate_oidc_discovery`` writes only what it owns (#1909).

The beat task reads every provider once, then fetches each discovery document in
turn; a fetch may take its whole timeout, paced by the issuer. A full write-back
of the snapshot read before the fetch reverts whatever an admin changed meanwhile
- a provider switched off, a rotated secret, a repointed issuer - and since #1883
those changes pass a step-up the refresh does not.

The double below enforces the rules of ``ArangoOidcConfigRepository``: ``update``
replaces the whole document, ``update_fields`` merges, ``update_discovery`` writes
two fields and only while the issuer is still the one the document came from. The
fetch hook is where the concurrent admin change lands.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.domain.models.oidc_config import OidcProviderConfig
from app.tasks.auth_tasks import rotate_oidc_discovery

DOC = {"authorization_endpoint": "https://corp.example.org/auth", "token_endpoint": "https://corp.example.org/token"}


class _Configs:
    def __init__(self) -> None:
        self.rows: dict[str, OidcProviderConfig] = {}

    def add(self, slug: str, **extra: Any) -> str:
        key = f"key-{slug}"
        self.rows[key] = OidcProviderConfig.model_validate(
            {
                "_key": key,
                "slug": slug,
                "display_name": slug,
                "issuer_url": f"https://{slug}.example.org",
                "client_id": f"{slug}-client",
                "client_secret_encrypted": "secret-v1",
                "enabled": True,
                "auto_discover": True,
                **extra,
            }
        )
        return key

    def list_all(self) -> list[OidcProviderConfig]:
        # A snapshot, like a cursor: later writes do not show through it.
        return [r.model_copy(deep=True) for r in self.rows.values()]

    def get_by_key(self, key: str) -> OidcProviderConfig | None:
        row = self.rows.get(key)
        return row.model_copy(deep=True) if row else None

    def update(self, key: str, config: OidcProviderConfig) -> OidcProviderConfig:
        """Full replace, as ``BaseArangoRepository.update`` does."""
        self.rows[key] = config.model_copy(deep=True)
        return self.rows[key]

    def update_fields(self, key: str, fields: dict[str, Any]) -> OidcProviderConfig:
        self.rows[key] = self.rows[key].model_copy(update=fields)
        return self.rows[key]

    def update_discovery(self, key: str, *, issuer_url: str, discovery_document: dict, refreshed_at: Any) -> bool:
        row = self.rows.get(key)
        if row is None or row.issuer_url != issuer_url:
            return False
        self.rows[key] = row.model_copy(
            update={"discovery_document": discovery_document, "discovery_refreshed_at": refreshed_at}
        )
        return True


def _run(configs: _Configs, on_fetch: Callable[[str], None] | None = None) -> dict:
    engine = MagicMock()

    def fetch(issuer_url: str) -> dict:
        if on_fetch:
            on_fetch(issuer_url)
        return DOC

    engine.fetch_discovery_document.side_effect = fetch
    with (
        patch("app.common.dependencies.get_oidc_config_repo", return_value=configs),
        patch("app.common.dependencies.get_oauth_engine", return_value=engine),
    ):
        return rotate_oidc_discovery()


def test_refresh_stores_the_document() -> None:
    configs = _Configs()
    key = configs.add("corp")

    result = _run(configs)

    assert result == {"updated": 1, "errors": 0}
    assert configs.rows[key].discovery_document == DOC
    assert configs.rows[key].discovery_refreshed_at is not None


def test_provider_switched_off_during_the_fetch_stays_off() -> None:
    configs = _Configs()
    key = configs.add("corp")

    _run(configs, on_fetch=lambda _issuer: configs.update_fields(key, {"enabled": False}))

    assert configs.rows[key].enabled is False
    assert configs.rows[key].discovery_document == DOC


def test_rotated_secret_during_the_fetch_survives() -> None:
    configs = _Configs()
    key = configs.add("corp")

    _run(configs, on_fetch=lambda _issuer: configs.update_fields(key, {"client_secret_encrypted": "secret-v2"}))

    assert configs.rows[key].client_secret_encrypted == "secret-v2"


def test_slow_earlier_provider_does_not_revert_a_change_to_a_later_one() -> None:
    """The window is the *whole* loop: a later provider's snapshot is as old as the earlier fetches are slow."""
    configs = _Configs()
    configs.add("aaa")
    later = configs.add("zzz")

    def on_fetch(issuer_url: str) -> None:
        if "aaa" in issuer_url:
            configs.update_fields(later, {"client_secret_encrypted": "secret-v2", "enabled": False})

    _run(configs, on_fetch=on_fetch)

    assert configs.rows[later].client_secret_encrypted == "secret-v2"
    assert configs.rows[later].enabled is False


def test_issuer_repointed_during_the_fetch_gets_no_stale_document() -> None:
    configs = _Configs()
    key = configs.add("corp")

    result = _run(
        configs, on_fetch=lambda _issuer: configs.update_fields(key, {"issuer_url": "https://new.example.org"})
    )

    assert configs.rows[key].issuer_url == "https://new.example.org"
    assert configs.rows[key].discovery_document is None
    assert result == {"updated": 0, "errors": 0}


def test_fetch_failure_is_counted_and_writes_nothing() -> None:
    configs = _Configs()
    key = configs.add("corp")
    engine = MagicMock()
    engine.fetch_discovery_document.side_effect = RuntimeError("boom")
    with (
        patch("app.common.dependencies.get_oidc_config_repo", return_value=configs),
        patch("app.common.dependencies.get_oauth_engine", return_value=engine),
    ):
        result = rotate_oidc_discovery()

    assert result == {"updated": 0, "errors": 1}
    assert configs.rows[key].discovery_document is None


@pytest.mark.parametrize("extra", [{"enabled": False}, {"auto_discover": False}])
def test_skipped_providers_are_not_fetched(extra: dict) -> None:
    configs = _Configs()
    configs.add("corp", **extra)

    result = _run(configs, on_fetch=lambda _i: pytest.fail("fetched a skipped provider"))

    assert result == {"updated": 0, "errors": 0}
