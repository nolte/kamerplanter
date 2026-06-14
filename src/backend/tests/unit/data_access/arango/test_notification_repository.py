"""Unit tests for ArangoNotificationRepository.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O
boundary and is doubled with MagicMock. No real ArangoDB connection. Assertions
target the public interface (returned ``Notification`` models, counts) and the
AQL query/bind_vars and edges the repository emits to its collaborator.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.notification_repository import (
    NOTIFICATIONS,
    ArangoNotificationRepository,
)
from app.domain.models.notification import (
    Notification,
    NotificationStatus,
    NotificationUrgency,
)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoNotificationRepository(mock_db)


def _notif_doc(**kwargs) -> dict:
    doc = {
        "_key": "n1",
        "user_key": "u1",
        "tenant_key": "t1",
        "notification_type": "care.watering.due",
        "title": "Watering due",
        "body": "Your tomato needs water",
        "urgency": NotificationUrgency.NORMAL.value,
        "status": NotificationStatus.PENDING.value,
        "escalation_level": 0,
    }
    doc.update(kwargs)
    return doc


def _notif_model(**kwargs) -> Notification:
    defaults = {
        "notification_type": "care.watering.due",
        "title": "Watering due",
        "body": "Your tomato needs water",
    }
    defaults.update(kwargs)
    return Notification(**defaults)


class TestCrud:
    def test_create_returns_notification_with_timestamps(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _notif_doc()}

        result = repo.create(_notif_model())

        assert isinstance(result, Notification)
        assert result.key == "n1"
        inserted = coll.insert.call_args.args[0]
        assert "created_at" in inserted
        assert "updated_at" in inserted

    def test_get_returns_model_when_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _notif_doc()

        result = repo.get("n1")

        assert isinstance(result, Notification)
        assert result.title == "Watering due"

    def test_get_returns_none_when_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None

        assert repo.get("n1") is None

    def test_update_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _notif_doc(title="Changed")}

        result = repo.update("n1", _notif_model(title="Changed"))

        assert result.title == "Changed"
        assert coll.update.call_args.args[0]["_key"] == "n1"


class TestListForUser:
    def test_filters_by_user_only_by_default(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_notif_doc()])

        result = repo.list_for_user("u1")

        assert len(result) == 1
        assert isinstance(result[0], Notification)
        call = mock_db.aql.execute.call_args
        query = call.args[0]
        bind_vars = call.kwargs["bind_vars"]
        assert "doc.user_key == @user_key" in query
        assert bind_vars["user_key"] == "u1"
        assert bind_vars["limit"] == 50
        assert bind_vars["offset"] == 0
        # No optional filters present.
        assert "tenant_key" not in bind_vars
        assert "notification_type" not in bind_vars

    def test_tenant_filter_adds_clause_and_bind(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.list_for_user("u1", tenant_key="t1")

        call = mock_db.aql.execute.call_args
        assert "doc.tenant_key == @tenant_key" in call.args[0]
        assert call.kwargs["bind_vars"]["tenant_key"] == "t1"

    def test_status_filter_adds_read_at_null_clause_without_bind(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.list_for_user("u1", status=NotificationStatus.DELIVERED)

        call = mock_db.aql.execute.call_args
        assert "doc.read_at == null" in call.args[0]
        # The status filter is a literal clause, not a bind var.
        assert "status" not in call.kwargs["bind_vars"]

    def test_type_filter_adds_clause_and_bind(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.list_for_user("u1", notification_type="care.watering.due")

        call = mock_db.aql.execute.call_args
        assert "doc.notification_type == @notification_type" in call.args[0]
        assert call.kwargs["bind_vars"]["notification_type"] == "care.watering.due"

    def test_custom_pagination_passed_through(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        repo.list_for_user("u1", limit=10, offset=20)

        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["limit"] == 10
        assert bind_vars["offset"] == 20


class TestMarkRead:
    def test_returns_updated_model_and_isoformats_timestamp(self, repo, mock_db):
        read_at = datetime(2026, 6, 14, 9, 0, 0, tzinfo=UTC)
        mock_db.aql.execute.return_value = iter([_notif_doc(read_at=read_at.isoformat())])

        result = repo.mark_read("n1", read_at)

        assert isinstance(result, Notification)
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars == {"key": "n1", "read_at": read_at.isoformat()}

    def test_returns_none_when_not_found(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.mark_read("missing", datetime(2026, 6, 14, tzinfo=UTC)) is None


class TestMarkActed:
    def test_returns_updated_model(self, repo, mock_db):
        acted_at = datetime(2026, 6, 14, 10, 0, 0, tzinfo=UTC)
        mock_db.aql.execute.return_value = iter([_notif_doc(acted_at=acted_at.isoformat())])

        result = repo.mark_acted("n1", acted_at)

        assert isinstance(result, Notification)
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["acted_at"] == acted_at.isoformat()

    def test_returns_none_when_not_found(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.mark_acted("n1", datetime(2026, 6, 14, tzinfo=UTC)) is None


class TestFindOverdueWatering:
    def test_filters_by_cutoff_and_level(self, repo, mock_db):
        cutoff = datetime(2026, 6, 12, tzinfo=UTC)
        mock_db.aql.execute.return_value = iter([_notif_doc(escalation_level=1)])

        result = repo.find_overdue_watering(overdue_since=cutoff, escalation_level=1)

        assert len(result) == 1
        call = mock_db.aql.execute.call_args
        assert "STARTS_WITH(doc.notification_type, 'care.watering')" in call.args[0]
        assert call.kwargs["bind_vars"] == {"cutoff": cutoff.isoformat(), "level": 1}

    def test_empty_result_returns_empty_list(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.find_overdue_watering(datetime(2026, 6, 12, tzinfo=UTC), 0) == []


class TestCountUnread:
    def test_counts_by_user(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([4])

        assert repo.count_unread("u1") == 4
        query = mock_db.aql.execute.call_args.args[0]
        assert "doc.read_at == null" in query

    def test_counts_with_tenant_filter(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([2])

        assert repo.count_unread("u1", tenant_key="t1") == 2
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["tenant_key"] == "t1"

    def test_empty_cursor_yields_zero(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.count_unread("u1") == 0


class TestCreateEdges:
    def test_creates_task_and_plant_edges(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": {}}

        repo.create_edges("n1", task_keys=["task1"], plant_keys=["plant1", "plant2"])

        # One edge per task + one per plant = 3 inserts.
        assert coll.insert.call_count == 3
        inserted_edges = [c.args[0] for c in coll.insert.call_args_list]
        task_edge = inserted_edges[0]
        assert task_edge["_from"] == f"{NOTIFICATIONS}/n1"
        assert task_edge["_to"] == "tasks/task1"
        plant_edge = inserted_edges[1]
        assert plant_edge["_to"] == "plant_instances/plant1"

    def test_no_keys_creates_no_edges(self, repo, mock_db):
        coll = mock_db.collection.return_value

        repo.create_edges("n1", task_keys=[], plant_keys=[])

        coll.insert.assert_not_called()
