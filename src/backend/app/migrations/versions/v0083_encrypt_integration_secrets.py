"""v0083 — encrypt the integration secrets stored in clear (#2113).

Before #2113 three secrets were stored as typed:

* ``system_settings.home_assistant.ha_access_token`` — the HA long-lived token;
* ``system_settings.plant_identification.plantnet_api_key`` — the Pl@ntNet key;
* ``notification_preferences.channels.apprise.config.urls`` — Apprise URLs, whose
  bot tokens / webhook secrets are part of the URL.

The code now writes Fernet ciphertext (``ha_access_token_encrypted``,
``plantnet_api_key_encrypted``, ``urls_encrypted``) and a save re-encrypts a value
it finds in clear. A read never writes: the GET routes that reach these readers
must not persist (``tests/unit/api/test_write_route_gates.py``), so a lazy
re-encryption on read is not available — and it would have left every value
nobody reads (the preferences of an inactive account) in clear for good anyway.
This migration encrypts the whole collection once, at startup.

**What it changes.** Per secret, a stored plaintext value (under the legacy name,
or under the ``_encrypted`` name while it is not a Fernet token — what a debug
instance without a key wrote) becomes ciphertext under the ``_encrypted`` name and
the legacy attribute is removed. An empty legacy value is removed without
counting. Every write is conditional on the document still holding the value
that was read, so a concurrent save wins.

**Cheap.** One read of the settings singleton and one filtered AQL scan of
``notification_preferences`` that returns only the rows still holding plaintext
URLs; encryption is in-process (Fernet, microseconds per value) and the writes go
back in batches of :data:`_BATCH` per statement. Measured on a local ArangoDB 3.12
(2026-10-05): 10,000 preference rows, 5,000 of them with two URLs each, 0.32 s; the
second run, with nothing left to encrypt, 0.02 s.

**Without a key** (``FERNET_KEY`` empty — debug only; the API and the worker refuse
to start without one otherwise) nothing can be encrypted: the migration writes
nothing, reports ``skipped: no_fernet_key`` and is recorded — it does not block
the migrations after it. Once a key is set, the next save of each document
encrypts it.

**Idempotent (M-3).** A Fernet token no longer matches; a second run changes
nothing. **Dry run (M-5)** counts and writes nothing. **Not reversible (M-6):**
decrypting secrets back into the database is the defect being repaired.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

import structlog
from arango.database import StandardDatabase

from app.config.settings import settings
from app.data_access.arango import collections as col
from app.domain.engines.encryption_engine import EncryptionEngine, is_fernet_token
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

_SINGLETON_KEY = "default"
_BATCH = 500

#: (block, encrypted field, legacy plaintext field) in ``system_settings``.
_SETTINGS_SECRETS: tuple[tuple[str, str, str], ...] = (
    ("home_assistant", "ha_access_token_encrypted", "ha_access_token"),
    ("plant_identification", "plantnet_api_key_encrypted", "plantnet_api_key"),
)

_REPLACE_SETTINGS_SECRET = """
FOR doc IN @@collection
  FILTER doc._key == @key
  LET current = doc[@block][@field] ? doc[@block][@field] : doc[@block][@legacy]
  FILTER current == @plaintext
  UPDATE doc WITH { [@block]: { [@field]: @ciphertext, [@legacy]: null } } IN @@collection
    OPTIONS { keepNull: false, mergeObjects: true }
  RETURN true
"""

_DROP_LEGACY_SETTINGS_KEY = """
FOR doc IN @@collection
  FILTER doc._key == @key
  FILTER HAS(doc[@block], @legacy)
  UPDATE doc WITH { [@block]: { [@legacy]: null } } IN @@collection OPTIONS { keepNull: false, mergeObjects: true }
  RETURN true
"""

_PLAINTEXT_URL_ROWS = """
FOR doc IN @@collection
  LET config = doc.channels.apprise.config
  FILTER config != null
  FILTER IS_ARRAY(config.urls)
    OR (IS_ARRAY(config.urls_encrypted) AND LENGTH(
      FOR t IN config.urls_encrypted FILTER NOT IS_STRING(t) OR NOT STARTS_WITH(t, "gAAAAA") RETURN 1
    ) > 0)
  RETURN { key: doc._key, urls: config.urls, urls_encrypted: config.urls_encrypted }
"""

_SEAL_URL_ROWS = """
FOR row IN @rows
  LET doc = DOCUMENT(@@collection, row.key)
  FILTER doc != null
  FILTER doc.channels.apprise.config.urls == row.urls
  FILTER doc.channels.apprise.config.urls_encrypted == row.urls_encrypted
  UPDATE doc WITH { channels: { apprise: { config: { urls_encrypted: row.sealed, urls: null } } } }
    IN @@collection OPTIONS { keepNull: false, mergeObjects: true }
  COLLECT WITH COUNT INTO n
  RETURN n
"""


class EncryptIntegrationSecretsMigration(Migration):
    version = "0083"
    name = "encrypt_integration_secrets"
    description = (
        "Fernet-encrypt the Home Assistant token, the Pl@ntNet key and the Apprise URLs stored in clear "
        "before #2113; skipped without a FERNET_KEY (the next save encrypts such a value once a key is set)."
    )
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        encryption = EncryptionEngine(settings.fernet_key)
        if not encryption.enabled:
            logger.warning("encrypt_integration_secrets_skipped", reason="no_fernet_key")
            return MigrationReport(
                version=self.version,
                name=self.name,
                dry_run=dry_run,
                details={"skipped": "no_fernet_key"},
            )
        settings_scanned, settings_changed = self._settings(db, encryption, dry_run=dry_run)
        rows_scanned, rows_changed = self._preferences(db, encryption, dry_run=dry_run)
        logger.info(
            "encrypt_integration_secrets",
            dry_run=dry_run,
            settings_secrets=settings_scanned,
            preference_rows=rows_scanned,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=settings_scanned + rows_scanned,
            changed=settings_changed + rows_changed,
            dry_run=dry_run,
            details={"settings_secrets": settings_scanned, "preference_rows": rows_scanned},
        )

    @staticmethod
    def _settings(db: StandardDatabase, encryption: EncryptionEngine, *, dry_run: bool) -> tuple[int, int]:
        if not db.has_collection(col.SYSTEM_SETTINGS):
            return 0, 0
        doc: Any = db.collection(col.SYSTEM_SETTINGS).get(_SINGLETON_KEY)
        if not isinstance(doc, dict):
            return 0, 0
        scanned = changed = 0
        for block, field, legacy in _SETTINGS_SECRETS:
            section = doc.get(block)
            if not isinstance(section, dict):
                continue
            current = section.get(field)
            if is_fernet_token(current) or (legacy in section and not (current or section.get(legacy))):
                # Already ciphertext (a legacy key beside it was written by an older
                # image during a rollout and is superseded), or an empty legacy value
                # ("" was the Pl@ntNet default): nothing to encrypt, drop the legacy key.
                if legacy in section:
                    scanned += 1
                    if not dry_run:
                        cursor = db.aql.execute(
                            _DROP_LEGACY_SETTINGS_KEY,
                            bind_vars={
                                "@collection": col.SYSTEM_SETTINGS,
                                "key": _SINGLETON_KEY,
                                "block": block,
                                "legacy": legacy,
                            },
                        )
                        changed += sum(1 for _ in cast(Iterable[bool], cursor))
                continue
            plaintext = current if current else section.get(legacy)
            if not isinstance(plaintext, str) or not plaintext:
                continue
            scanned += 1
            if dry_run:
                continue
            cursor = db.aql.execute(
                _REPLACE_SETTINGS_SECRET,
                bind_vars={
                    "@collection": col.SYSTEM_SETTINGS,
                    "key": _SINGLETON_KEY,
                    "block": block,
                    "field": field,
                    "legacy": legacy,
                    "plaintext": plaintext,
                    "ciphertext": encryption.encrypt(plaintext),
                },
            )
            changed += sum(1 for _ in cast(Iterable[bool], cursor))
        return scanned, changed

    @staticmethod
    def _preferences(db: StandardDatabase, encryption: EncryptionEngine, *, dry_run: bool) -> tuple[int, int]:
        if not db.has_collection(col.NOTIFICATION_PREFERENCES):
            return 0, 0
        rows = list(
            cast(
                Iterable[dict[str, Any]],
                db.aql.execute(_PLAINTEXT_URL_ROWS, bind_vars={"@collection": col.NOTIFICATION_PREFERENCES}),
            )
        )
        if dry_run or not rows:
            return len(rows), 0
        changed = 0
        for start in range(0, len(rows), _BATCH):
            batch = [
                {
                    "key": row["key"],
                    "urls": row["urls"],
                    "urls_encrypted": row["urls_encrypted"],
                    "sealed": _sealed_urls(row, encryption),
                }
                for row in rows[start : start + _BATCH]
            ]
            cursor = db.aql.execute(
                _SEAL_URL_ROWS, bind_vars={"@collection": col.NOTIFICATION_PREFERENCES, "rows": batch}
            )
            changed += next(iter(cast(Iterable[int], cursor)), 0)
        return len(rows), changed


def _sealed_urls(row: dict[str, Any], encryption: EncryptionEngine) -> list[str]:
    """Ciphertext for every URL of *row*: a plaintext ``urls`` list wins, an unsealed entry is sealed."""
    if isinstance(row.get("urls"), list):
        return [encryption.encrypt(url) for url in row["urls"] if isinstance(url, str)]
    return [
        value if is_fernet_token(value) else encryption.encrypt(value)
        for value in row.get("urls_encrypted") or []
        if isinstance(value, str)
    ]


migration = EncryptIntegrationSecretsMigration()
