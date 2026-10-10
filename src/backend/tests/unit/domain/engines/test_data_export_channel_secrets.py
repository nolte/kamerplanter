"""#2113 — the Art. 15 bundle never carries an Apprise URL, in clear or as ciphertext.

The ``notification_preferences`` section exports ``channels`` whole. An Apprise
URL is a credential (the bot token / webhook secret is part of the URL), and since
#2113 it is stored as Fernet ciphertext under ``urls_encrypted`` — a row written
before the migration may still carry the plaintext ``urls``. The bundle states
*that* URLs are configured and how many, never the value: the subject learns the
category and the extent (Art. 15(1)), and a leaked bundle is no credential (the
ciphertext would become one the moment ``FERNET_KEY`` leaks). The calendar-feed
``token`` is withheld the same way (``DataExportEngine.USER_DATA_MANIFEST``).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.domain.engines.data_export_engine import DataExportEngine

TGRAM = "tgram://" + "123456789:" + "AAbot2113" + "Secret/4711"
CIPHER = "gAAAAA" + "B" * 120


def _bundle(rows: list[dict]) -> dict:
    engine = DataExportEngine()
    source = next(s for s in engine.USER_DATA_MANIFEST if s.collection == "notification_preferences")
    return engine.build_bundle(
        "u1", datetime(2026, 10, 5, tzinfo=UTC), [(source, rows)], controller_name="c", controller_email="c@example.org"
    )


def test_ciphertext_and_legacy_plaintext_urls_are_replaced_by_a_count() -> None:
    rows = [
        {"channels": {"apprise": {"enabled": True, "config": {"urls_encrypted": [CIPHER, CIPHER]}}}},
        {"channels": {"apprise": {"enabled": True, "config": {"urls": [TGRAM]}}}},
    ]

    bundle = _bundle(rows)

    text = json.dumps(bundle)
    assert TGRAM not in text
    assert CIPHER not in text
    records = bundle["sections"][0]["records"]
    assert records[0]["channels"]["apprise"]["config"] == {"urls_configured": 2}
    assert records[1]["channels"]["apprise"]["config"] == {"urls_configured": 1}


def test_the_rest_of_the_preferences_is_exported_unchanged_and_the_input_is_not_mutated() -> None:
    row = {
        "channels": {
            "apprise": {"enabled": True, "priority": 3, "config": {"urls_encrypted": [CIPHER]}},
            "email": {"enabled": True, "config": {"digest": True}},
        },
        "quiet_hours": {"enabled": False},
    }

    record = _bundle([row])["sections"][0]["records"][0]

    assert record["channels"]["email"] == {"enabled": True, "config": {"digest": True}}
    assert record["channels"]["apprise"]["priority"] == 3
    assert record["quiet_hours"] == {"enabled": False}
    assert row["channels"]["apprise"]["config"] == {"urls_encrypted": [CIPHER]}


def test_the_calendar_feed_section_declares_neither_the_token_nor_its_hash() -> None:
    """#2171: the export reads only the declared fields (``ArangoPersonalDataRepository`` KEEPs them).

    A row written before v0090 may still carry ``token``; every row carries ``token_hash``. Neither is a
    declared field, so neither reaches the Art. 15 bundle.
    """
    source = next(s for s in DataExportEngine().USER_DATA_MANIFEST if s.collection == "calendar_feeds")

    assert "name" in source.fields  # the control: the section exports the feed itself
    assert {"token", "token_hash"}.isdisjoint(source.fields)
