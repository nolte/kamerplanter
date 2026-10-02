"""v0064 binds unambiguous legacy provider links to their configuration (#1869).

The rule lives in the pure ``plan_bindings``; ``up`` is checked through a double
that answers exactly this migration's two queries and refuses any other.
"""

from __future__ import annotations

import re
from typing import Any

from app.migrations.versions.v0064_bind_provider_links_to_configuration import (
    BindProviderLinksToConfigurationMigration,
    plan_bindings,
)

_CONFIGS = [
    {"slug": "google", "provider_type": "google"},
    {"slug": "corp-a", "provider_type": "oidc"},
    {"slug": "corp-b", "provider_type": "oidc"},
]


def test_a_link_with_the_only_configuration_of_its_type_is_bound_to_it() -> None:
    assert plan_bindings([{"_key": "l1", "provider": "google"}], _CONFIGS) == {"l1": "google"}


def test_a_link_with_two_configurations_of_its_type_is_left_alone() -> None:
    assert plan_bindings([{"_key": "l1", "provider": "oidc"}], _CONFIGS) == {}


def test_a_disabled_configuration_counts() -> None:
    """The configurations passed in are all of them; disabled ones made links too."""
    configs = [*_CONFIGS[:2], {"slug": "corp-b", "provider_type": "oidc", "enabled": False}]

    assert plan_bindings([{"_key": "l1", "provider": "oidc"}], configs) == {}


def test_a_link_whose_type_has_no_configuration_is_left_alone() -> None:
    assert plan_bindings([{"_key": "l1", "provider": "github"}], _CONFIGS) == {}


class _Collection:
    def __init__(self, docs: dict[str, dict[str, Any]]) -> None:
        self.docs = docs
        self.index_rows: list[dict[str, Any]] = [
            {"id": "i-legacy", "type": "persistent", "unique": True, "fields": ["provider", "provider_user_id"]},
            {"id": "i-user", "type": "persistent", "unique": False, "fields": ["user_key"]},
        ]

    def indexes(self) -> list[dict[str, Any]]:
        return list(self.index_rows)

    def add_persistent_index(self, fields: list[str], unique: bool) -> None:
        if not any(i["fields"] == fields for i in self.index_rows):
            self.index_rows.append(
                {"id": f"i-{len(self.index_rows)}", "type": "persistent", "unique": unique, "fields": fields}
            )

    def delete_index(self, index_id: str, ignore_missing: bool = False) -> None:  # noqa: ARG002
        self.index_rows = [i for i in self.index_rows if i["id"] != index_id]

    def update(self, patch: dict[str, Any], **kwargs: Any) -> None:  # noqa: ARG002
        self.docs[patch["_key"]].update({k: v for k, v in patch.items() if k != "_key"})


class _Db:
    def __init__(self, links: dict[str, dict[str, Any]], configs: list[dict[str, Any]]) -> None:
        self.links = _Collection(links)
        self.configs = configs
        self.aql = self

    def has_collection(self, name: str) -> bool:
        return name in {"auth_providers", "oidc_provider_configs"}

    def collection(self, name: str) -> _Collection:
        assert name == "auth_providers"
        return self.links

    def execute(self, query: str, bind_vars: dict | None = None, **kwargs: Any) -> list[Any]:  # noqa: ARG002
        q = re.sub(r"\s+", " ", query).strip()
        if q.startswith("FOR p IN auth_providers FILTER p.oidc_config_slug == null"):
            return [
                {"_key": k, "provider": d.get("provider")}
                for k, d in self.links.docs.items()
                if d.get("oidc_config_slug") is None
            ]
        if q.startswith("FOR c IN oidc_provider_configs"):
            return [{"slug": c["slug"], "provider_type": c["provider_type"]} for c in self.configs]
        raise AssertionError(f"unexpected query: {q}")


def _db() -> _Db:
    return _Db(
        {
            "g_legacy": {"provider": "google", "provider_user_id": "g1"},
            "o_legacy": {"provider": "oidc", "provider_user_id": "o1"},
            "o_bound": {"provider": "oidc", "provider_user_id": "o2", "oidc_config_slug": "corp-b"},
        },
        _CONFIGS,
    )


def test_up_binds_the_unambiguous_links_and_a_second_run_is_a_no_op() -> None:
    db = _db()
    migration = BindProviderLinksToConfigurationMigration()

    first = migration.up(db)  # type: ignore[arg-type]
    second = migration.up(db)  # type: ignore[arg-type]

    assert db.links.docs["g_legacy"]["oidc_config_slug"] == "google"
    assert db.links.docs["o_legacy"].get("oidc_config_slug") is None
    assert db.links.docs["o_bound"]["oidc_config_slug"] == "corp-b"
    assert (first.scanned, first.details["bound"], first.details["legacy_unique_indexes_dropped"]) == (2, 1, 1)
    assert second.changed == 0
    unique = [i["fields"] for i in db.links.index_rows if i["unique"]]
    assert unique == [["provider", "oidc_config_slug", "provider_user_id"]]


def test_a_dry_run_writes_nothing() -> None:
    db = _db()

    report = BindProviderLinksToConfigurationMigration().up(db, dry_run=True)  # type: ignore[arg-type]

    assert report.details["bound"] == 1
    assert report.changed == 0
    assert "oidc_config_slug" not in db.links.docs["g_legacy"]
    assert any(i["fields"] == ["provider", "provider_user_id"] for i in db.links.index_rows)
