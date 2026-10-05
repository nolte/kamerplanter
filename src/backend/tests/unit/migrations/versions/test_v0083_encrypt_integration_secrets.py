"""v0083 (#2113): without a key the migration writes nothing and does not block; a dry run only reads.

The writes themselves are measured against a real ArangoDB in
``tests/integration/test_integration_secrets_at_rest.py`` (every legacy secret
encrypted, a second run changes nothing).
"""

from __future__ import annotations

from typing import Any

import pytest
from cryptography.fernet import Fernet

from app.migrations.versions import v0083_encrypt_integration_secrets as module
from app.migrations.versions.v0083_encrypt_integration_secrets import migration

HA_TOKEN = "eyJ" + "hbGciOiJIUzI1NiJ9" + "-mig-2113"


class _Collection:
    def __init__(self, doc: dict[str, Any] | None) -> None:
        self.doc = doc

    def get(self, key: str) -> dict[str, Any] | None:  # noqa: ARG002
        return self.doc


class _Db:
    def __init__(self, settings_doc: dict[str, Any] | None, url_rows: list[dict[str, Any]]) -> None:
        self.settings_doc = settings_doc
        self.url_rows = url_rows
        self.queries: list[str] = []
        self.aql = self

    def has_collection(self, name: str) -> bool:  # noqa: ARG002
        return True

    def collection(self, name: str) -> _Collection:  # noqa: ARG002
        return _Collection(self.settings_doc)

    def execute(self, query: str, bind_vars: dict | None = None, **kwargs: Any) -> list[Any]:  # noqa: ARG002
        self.queries.append(query)
        if query == module._PLAINTEXT_URL_ROWS:
            return list(self.url_rows)
        return [True]


def _legacy_db() -> _Db:
    return _Db(
        {"home_assistant": {"ha_access_token": HA_TOKEN}, "plant_identification": {"plantnet_api_key": ""}},
        [{"key": "notifpref_a", "urls": ["tgram://a/b"], "urls_encrypted": None}],
    )


def test_without_a_key_nothing_is_read_or_written_and_the_run_is_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module.settings, "fernet_key", "")
    db = _legacy_db()

    report = migration.up(db)  # type: ignore[arg-type]

    assert (report.changed, report.precondition_unmet, db.queries) == (0, False, [])
    assert report.details == {"skipped": "no_fernet_key"}


def test_a_dry_run_counts_and_only_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module.settings, "fernet_key", Fernet.generate_key().decode())
    db = _legacy_db()

    report = migration.up(db, dry_run=True)  # type: ignore[arg-type]

    assert report.changed == 0
    assert report.details == {"settings_secrets": 2, "preference_rows": 1}
    assert db.queries == [module._PLAINTEXT_URL_ROWS]


def test_an_already_sealed_entry_is_kept_and_an_unsealed_one_is_sealed() -> None:
    from app.domain.engines.encryption_engine import EncryptionEngine, is_fernet_token  # noqa: PLC0415

    engine = EncryptionEngine(Fernet.generate_key().decode())
    token = engine.encrypt("tgram://a/b")

    sealed = module._sealed_urls({"urls": None, "urls_encrypted": [token, "gotify://h/t", 3]}, engine)

    assert sealed[0] == token
    assert is_fernet_token(sealed[1])
    assert len(sealed) == 2
