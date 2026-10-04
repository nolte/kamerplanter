"""Unit tests for ArangoNotificationPreferenceRepository.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection. The repository uses
a deterministic ``_key = notifpref_{user_key}`` for upsert semantics, which the
tests assert as observable behaviour.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.notification_preference_repository import (
    NOTIFICATION_PREFERENCES,
    ArangoNotificationPreferenceRepository,
)
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.models.notification import NotificationPreferences


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoNotificationPreferenceRepository(mock_db, EncryptionEngine(""))


def _doc(**kwargs) -> dict:
    doc = {"_key": "notifpref_u1", "user_key": "u1"}
    doc.update(kwargs)
    return doc


class TestMakeKey:
    def test_builds_deterministic_key(self):
        assert ArangoNotificationPreferenceRepository._make_key("u1") == "notifpref_u1"


class TestGetByUser:
    def test_found_uses_deterministic_key(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc()

        result = repo.get_by_user("u1")

        assert isinstance(result, NotificationPreferences)
        assert result.user_key == "u1"
        coll.get.assert_called_once_with("notifpref_u1")

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_user("u1") is None


class TestUpsert:
    def test_inserts_when_not_existing(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.get.return_value = None  # no existing doc
        coll.insert.return_value = {"new": _doc()}

        result = repo.upsert(NotificationPreferences(user_key="u1"))

        assert isinstance(result, NotificationPreferences)
        coll.insert.assert_called_once()
        inserted = coll.insert.call_args.args[0]
        assert inserted["_key"] == "notifpref_u1"
        assert inserted["user_key"] == "u1"
        assert "created_at" in inserted
        assert "updated_at" in inserted
        coll.update.assert_not_called()

    def test_updates_when_existing(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc()  # existing doc
        coll.update.return_value = {"new": _doc()}

        result = repo.upsert(NotificationPreferences(user_key="u1"))

        assert isinstance(result, NotificationPreferences)
        coll.update.assert_called_once()
        updated = coll.update.call_args.args[0]
        assert updated["_key"] == "notifpref_u1"
        assert "updated_at" in updated
        coll.insert.assert_not_called()


class TestListUsersWithDigestEnabled:
    def test_filters_enabled_and_digest(self, repo, mock_db):
        doc = _doc(channels={"email": {"enabled": True, "config": {"email": "a@x", "digest": True}}})
        mock_db.aql.execute.return_value = iter([doc])

        result = repo.list_users_with_digest_enabled()

        assert len(result) == 1
        assert isinstance(result[0], NotificationPreferences)
        assert result[0].channels["email"].config["digest"] is True
        call = mock_db.aql.execute.call_args
        query = call.args[0]
        assert "p.channels.email.enabled == true" in query
        assert "p.channels.email.config.digest == true" in query
        assert call.kwargs["bind_vars"] == {"@collection": NOTIFICATION_PREFERENCES}

    def test_empty_result_returns_empty_list(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.list_users_with_digest_enabled() == []


class TestAppriseUrlsSealed:
    """#2113 — the stored form carries ciphertext only; the reader decrypts; a read never writes."""

    URL = "tgram://" + "123456789:" + "AAbot2113" + "Unit/4711"

    @pytest.fixture
    def keyed(self, mock_db):
        from cryptography.fernet import Fernet  # noqa: PLC0415

        return ArangoNotificationPreferenceRepository(mock_db, EncryptionEngine(Fernet.generate_key().decode()))

    def _prefs(self) -> NotificationPreferences:
        from app.domain.models.notification import ChannelPreference  # noqa: PLC0415

        return NotificationPreferences(
            user_key="u1", channels={"apprise": ChannelPreference(enabled=True, config={"urls": [self.URL]})}
        )

    def test_insert_stores_ciphertext_and_returns_plaintext(self, keyed, mock_db):
        coll = mock_db.collection.return_value
        coll.get.return_value = None
        coll.insert.side_effect = lambda data, return_new: {"new": dict(data)}

        result = keyed.upsert(self._prefs())

        inserted = coll.insert.call_args.args[0]
        assert self.URL not in str(inserted)
        assert "urls" not in inserted["channels"]["apprise"]["config"]
        assert result.channels["apprise"].config["urls"] == [self.URL]

    def test_update_removes_a_plaintext_key_the_merge_would_keep(self, keyed, mock_db):
        coll = mock_db.collection.return_value
        coll.get.return_value = _doc()
        coll.update.side_effect = lambda data, return_new, keep_none: {"new": dict(data)}

        keyed.upsert(self._prefs())

        payload = coll.update.call_args.args[0]
        assert payload["channels"]["apprise"]["config"]["urls"] is None
        assert coll.update.call_args.kwargs["keep_none"] is False
        assert self.URL not in str(payload)

    def test_a_legacy_row_is_read_without_a_write(self, keyed, mock_db):
        """A read never writes (the preferences GET must not persist); v0083 or the next save seals it."""
        mock_db.collection.return_value.get.return_value = _doc(
            channels={"apprise": {"enabled": True, "config": {"urls": [self.URL]}}}
        )

        assert keyed.get_by_user("u1").channels["apprise"].config["urls"] == [self.URL]
        mock_db.aql.execute.assert_not_called()
        mock_db.collection.return_value.update.assert_not_called()

    def test_without_a_key_a_legacy_row_is_not_rewritten(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc(
            channels={"apprise": {"enabled": True, "config": {"urls": [self.URL]}}}
        )

        assert repo.get_by_user("u1").channels["apprise"].config["urls"] == [self.URL]
        mock_db.aql.execute.assert_not_called()

    def test_an_already_sealed_row_is_not_rewritten(self, keyed, mock_db):
        sealed = keyed._encryption.encrypt(self.URL)
        mock_db.collection.return_value.get.return_value = _doc(
            channels={"apprise": {"enabled": True, "config": {"urls_encrypted": [sealed]}}}
        )

        assert keyed.get_by_user("u1").channels["apprise"].config["urls"] == [self.URL]
        mock_db.aql.execute.assert_not_called()
