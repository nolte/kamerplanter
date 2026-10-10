"""Tenant A never reads tenant B's row through the repositories MT-023 scoped (#2119).

Two halves:

* **The base list reads.** Every repository that now sets ``is_tenant_scoped``
  refuses a :meth:`get_all` / :meth:`list_window` without a ``tenant_key`` (or an
  explicit ``all_tenants=True``) and, given one, filters on it. Before #2119 the
  same call returned every tenant's rows.
* **The reads that took ``tenant_key`` positionally** and now take it
  keyword-only without a default. Each is exercised against a database double that
  replays the tenant predicate the query *actually* carries
  (:mod:`tests.support.tenant_replay`), so a read that lost its filter hands the
  foreign row straight back here — as ArangoDB would.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from app.data_access.arango.ai_repository import ArangoAiProviderRepository
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.calendar_feed_repository import ArangoCalendarFeedRepository
from app.data_access.arango.identification_repository import ArangoIdentificationRepository
from app.data_access.arango.invitation_repository import ArangoInvitationRepository
from app.data_access.arango.location_assignment_repository import ArangoLocationAssignmentRepository
from app.data_access.arango.membership_repository import ArangoMembershipRepository
from app.data_access.arango.notification_repository import ArangoNotificationRepository
from app.data_access.arango.pest_detection_repository import ArangoPestDetectionRepository
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.data_access.arango.plant_diary_repository import ArangoPlantDiaryRepository
from app.data_access.arango.tenant_erasure_repository import ArangoTenantErasureRepository
from app.domain.models.pest_detection import PestFeedback
from tests.support.tenant_replay import apply_predicates

TENANT_A = "tenant-a"
TENANT_B = "tenant-b"

#: The repositories #2119 moved onto ``is_tenant_scoped`` (MT-023).
SCOPED_BY_2119: tuple[type[BaseArangoRepository[Any]], ...] = (
    ArangoCalendarFeedRepository,
    ArangoAttachmentRepository,
    ArangoPlantDiaryRepository,
    ArangoNotificationRepository,
    ArangoPestDetectionRepository,
    ArangoPestImageRepository,
    ArangoIdentificationRepository,
    ArangoAiProviderRepository,
    ArangoInvitationRepository,
    ArangoLocationAssignmentRepository,
    ArangoMembershipRepository,
    ArangoTenantErasureRepository,
)


def _identity(row: dict[str, Any]) -> dict[str, Any]:
    return row


#: The loop variables the hand-written AQL of these repositories uses.
_RESOLVERS = {name: _identity for name in ("req", "c", "f")}


class _ReplayAql:
    """Answers every query from ``rows`` filtered by the predicates it spells out."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, query: str, bind_vars: dict[str, Any] | None = None, **_: Any):
        bind_vars = dict(bind_vars or {})
        self.calls.append((query, bind_vars))
        rows = apply_predicates(list(self._rows), query, bind_vars, _RESOLVERS)
        if "COLLECT WITH COUNT" in query:
            return iter([len(rows)])
        if "RETURN 1" in query:
            return iter([1] if rows else [])
        if "RETURN DISTINCT doc.user_key" in query:
            return iter(sorted({r["user_key"] for r in rows}))
        return iter(rows)


def _db(rows: list[dict[str, Any]]) -> MagicMock:
    db = MagicMock()
    db.aql = _ReplayAql(rows)
    by_key = {row["_key"]: row for row in rows}
    db.collection.return_value.get.side_effect = lambda key: by_key.get(key)
    return db


# ── The base list reads ───────────────────────────────────────────────────────


@pytest.mark.parametrize("repo_cls", SCOPED_BY_2119, ids=lambda c: c.__name__)
class TestTheBaseListReadsAreTenantBound:
    def test_the_repository_is_tenant_scoped(self, repo_cls) -> None:
        assert repo_cls.is_tenant_scoped is True

    def test_a_list_without_a_tenant_is_refused(self, repo_cls) -> None:
        repo = repo_cls(_db([]))
        with pytest.raises(ValueError, match="tenant-scoped"):
            repo.get_all()
        with pytest.raises(ValueError, match="tenant-scoped"):
            repo.list_window()

    def test_a_list_with_a_tenant_filters_on_it(self, repo_cls) -> None:
        db = _db([])
        repo_cls(db).get_all(tenant_key=TENANT_A)

        assert db.aql.calls, "get_all issued no query"
        for query, bind_vars in db.aql.calls:
            assert "doc.tenant_key == @v0" in query
            assert bind_vars["v0"] == TENANT_A

    def test_the_system_context_is_an_explicit_opt_in(self, repo_cls) -> None:
        db = _db([])
        repo_cls(db).get_all(all_tenants=True)
        assert db.aql.calls


# ── The reads converted to a keyword-only tenant ──────────────────────────────


def _ident(key: str, tenant_key: str) -> dict[str, Any]:
    return {"_key": key, "tenant_key": tenant_key, "user_key": "u1", "adapter_key": "local", "image_hash": "h"}


def _contribution(key: str, tenant_key: str) -> dict[str, Any]:
    return {
        "_key": key,
        "tenant_key": tenant_key,
        "pest_key": "aphid",
        "attachment_id": f"att-{key}",
        "contributed_by": "u1",
    }


class TestIdentificationRequests:
    rows = [_ident("own", TENANT_A), _ident("foreign", TENANT_B)]

    def test_by_key_answers_only_the_own_tenant(self) -> None:
        repo = ArangoIdentificationRepository(_db(self.rows))
        assert repo.get("own", tenant_key=TENANT_A) is not None
        assert repo.get("foreign", tenant_key=TENANT_A) is None

    def test_the_history_lists_only_the_own_tenant(self) -> None:
        repo = ArangoIdentificationRepository(_db(self.rows))
        assert [r.key for r in repo.list_for_user(tenant_key=TENANT_A, user_key="u1")] == ["own"]

    def test_the_tenant_cannot_be_passed_positionally(self) -> None:
        repo = ArangoIdentificationRepository(_db(self.rows))
        with pytest.raises(TypeError):
            repo.get("own", TENANT_A)  # type: ignore[misc]
        with pytest.raises(TypeError):
            repo.list_for_user(TENANT_A, "u1")  # type: ignore[misc]


class TestPestDetections:
    rows = [
        {"_key": "own", "tenant_key": TENANT_A, "plant_instance_key": "p1"},
        {"_key": "foreign", "tenant_key": TENANT_B, "plant_instance_key": "p1"},
    ]

    def test_by_key_answers_only_the_own_tenant(self) -> None:
        repo = ArangoPestDetectionRepository(_db(self.rows))
        assert repo.get("own", tenant_key=TENANT_A) is not None
        assert repo.get("foreign", tenant_key=TENANT_A) is None

    def test_feedback_reaches_only_the_own_tenants_detection(self) -> None:
        # ``add_feedback`` reads the detection twice through ``get``; a positional
        # call left behind by the keyword-only conversion would raise here.
        db = _db(self.rows)
        repo = ArangoPestDetectionRepository(db)
        feedback = PestFeedback(finding_label="aphid", confirmed=False)

        assert repo.add_feedback("foreign", TENANT_A, feedback) is None
        db.collection.return_value.update.assert_not_called()

        updated = repo.add_feedback("own", TENANT_A, feedback)
        assert updated is not None and updated.key == "own"
        db.collection.return_value.update.assert_called_once()

    def test_the_plant_list_holds_only_the_own_tenant(self) -> None:
        repo = ArangoPestDetectionRepository(_db(self.rows))
        assert [d.key for d in repo.list_for_plant(tenant_key=TENANT_A, plant_instance_key="p1")] == ["own"]

    def test_the_tenant_cannot_be_passed_positionally(self) -> None:
        repo = ArangoPestDetectionRepository(_db(self.rows))
        with pytest.raises(TypeError):
            repo.get("own", TENANT_A)  # type: ignore[misc]
        with pytest.raises(TypeError):
            repo.list_for_plant(TENANT_A, "p1")  # type: ignore[misc]


class TestPestImageContributions:
    rows = [_contribution("own", TENANT_A), _contribution("foreign", TENANT_B)]

    def test_by_key_answers_only_the_own_tenant(self) -> None:
        repo = ArangoPestImageRepository(_db(self.rows))
        assert repo.get("own", tenant_key=TENANT_A) is not None
        assert repo.get("foreign", tenant_key=TENANT_A) is None

    def test_a_foreign_contribution_cannot_be_deleted(self) -> None:
        db = _db(self.rows)
        assert ArangoPestImageRepository(db).delete("foreign", TENANT_A) is False
        db.collection.return_value.delete.assert_not_called()

    def test_the_lists_hold_only_the_own_tenant(self) -> None:
        repo = ArangoPestImageRepository(_db(self.rows))
        assert [c.key for c in repo.list_for_pest(tenant_key=TENANT_A, pest_key="aphid")] == ["own"]
        assert [c.key for c in repo.list_for_tenant(tenant_key=TENANT_A)] == ["own"]

    def test_the_tenant_cannot_be_passed_positionally(self) -> None:
        repo = ArangoPestImageRepository(_db(self.rows))
        with pytest.raises(TypeError):
            repo.get("own", TENANT_A)  # type: ignore[misc]
        with pytest.raises(TypeError):
            repo.list_for_pest(TENANT_A, "aphid")  # type: ignore[misc]
        with pytest.raises(TypeError):
            repo.list_for_tenant(TENANT_A)  # type: ignore[misc]


class TestCalendarFeeds:
    rows = [
        {"_key": "own", "tenant_key": TENANT_A, "user_key": "u1", "name": "Mine"},
        {"_key": "foreign", "tenant_key": TENANT_B, "user_key": "u1", "name": "Other garden"},
    ]

    def test_the_feed_list_holds_only_the_own_tenant(self) -> None:
        repo = ArangoCalendarFeedRepository(_db(self.rows))
        assert [f.key for f in repo.list_by_user("u1", tenant_key=TENANT_A)] == ["own"]

    def test_the_tenant_cannot_be_passed_positionally(self) -> None:
        repo = ArangoCalendarFeedRepository(_db(self.rows))
        with pytest.raises(TypeError):
            repo.list_by_user("u1", TENANT_A)  # type: ignore[misc]


class TestNotificationGroups:
    rows = [
        {
            "_key": "own",
            "tenant_key": TENANT_A,
            "user_key": "u1",
            "group_key": "g",
            "notification_type": "x",
            "title": "t",
            "body": "b",
        },
        {
            "_key": "foreign",
            "tenant_key": TENANT_B,
            "user_key": "u2",
            "group_key": "g",
            "notification_type": "x",
            "title": "t",
            "body": "b",
        },
    ]

    def test_the_group_reads_hold_only_the_own_tenant(self) -> None:
        repo = ArangoNotificationRepository(_db(self.rows))
        assert [n.key for n in repo.list_by_group_key("g", tenant_key=TENANT_A)] == ["own"]
        assert repo.find_notified_user_keys("g", tenant_key=TENANT_A) == {"u1"}
        assert repo.exists_by_group_key("g", tenant_key=TENANT_A) is True

    def test_a_group_only_another_tenant_holds_is_absent(self) -> None:
        repo = ArangoNotificationRepository(_db(self.rows[1:]))
        assert repo.list_by_group_key("g", tenant_key=TENANT_A) == []
        assert repo.find_notified_user_keys("g", tenant_key=TENANT_A) == set()
        assert repo.exists_by_group_key("g", tenant_key=TENANT_A) is False

    @pytest.mark.parametrize("method", ["list_by_group_key", "find_notified_user_keys", "exists_by_group_key"])
    def test_the_tenant_cannot_be_passed_positionally(self, method: str) -> None:
        repo = ArangoNotificationRepository(_db(self.rows))
        with pytest.raises(TypeError):
            getattr(repo, method)("g", TENANT_A)
