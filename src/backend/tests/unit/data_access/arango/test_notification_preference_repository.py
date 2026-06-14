"""Unit tests for ArangoNotificationPreferenceRepository.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection. The repository uses
a deterministic ``_key = notifpref_{user_key}`` for upsert semantics, which the
tests assert as observable behaviour.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.notification_preference_repository import (
    ArangoNotificationPreferenceRepository,
)
from app.domain.models.notification import NotificationPreferences


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoNotificationPreferenceRepository(mock_db)


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
