"""REQ-053 WP 9.3 review (DSGVO): the request digest of a buffered write is keyed, so it cannot re-link a person.

An unkeyed SHA-256 over ``{"user": <account key>, ...}`` lets anyone holding the stored digest try the account keys
of an installation and find whose write an anonymised row was. The digest is an HMAC keyed with the erasure
tombstone salt, a server secret.
"""

from __future__ import annotations

import hashlib
import json

from app.config.settings import settings
from app.domain.models.client_event import client_event_digest, is_client_event_conflict

PAYLOAD = {"user": "u_sabine", "body": {"summary": "Snails"}}


def _plain_sha256(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_the_digest_is_not_the_unkeyed_hash_and_depends_on_the_server_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "a" * 32)
    keyed = client_event_digest(PAYLOAD)
    monkeypatch.setattr(settings, "erasure_tombstone_salt", "b" * 32)

    assert keyed != _plain_sha256(PAYLOAD)
    assert client_event_digest(PAYLOAD) != keyed  # another secret, another digest
    assert client_event_digest(dict(reversed(PAYLOAD.items()))) == client_event_digest(PAYLOAD)  # canonical


def test_only_a_client_event_index_counts_as_a_replay_conflict() -> None:
    assert is_client_event_conflict([{"field": "client_event_id"}])
    assert is_client_event_conflict([{"field": "completion_client_event_id"}])
    assert not is_client_event_conflict([{"field": "batch_id"}])
