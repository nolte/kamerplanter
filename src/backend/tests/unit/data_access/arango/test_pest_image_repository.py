"""REQ-010 — unit tests for ArangoPestImageRepository (new Phase-2 methods).

Solitary unit tests: the injected ``StandardDatabase`` is doubled with
MagicMock; we assert AQL is parametrized (bind_vars only) and that the
tenant-vs-cross-tenant access boundary is enforced at the repo layer.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.common.enums import PestImageStatus
from app.data_access.arango.pest_image_repository import ArangoPestImageRepository
from app.domain.models.pest_image import PestImageContribution


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoPestImageRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {
        "_key": "pic1",
        "tenant_key": "t1",
        "pest_key": "p1",
        "attachment_id": "att1",
        "contributed_by": "u1",
        "status": PestImageStatus.PRIVATE.value,
    }
    doc.update(kwargs)
    return doc


class TestGetByKey:
    def test_returns_model_irrespective_of_tenant(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc(tenant_key="t-other")
        result = repo.get_by_key("pic1")
        assert isinstance(result, PestImageContribution)
        assert result.tenant_key == "t-other"

    def test_returns_none_when_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("pic1") is None


class TestListPromotedForPest:
    def test_binds_pest_and_promoted_status(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(status=PestImageStatus.PROMOTED.value)])
        results = repo.list_promoted_for_pest("p1")
        assert len(results) == 1
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["pest_key"] == "p1"
        assert bind_vars["status"] == PestImageStatus.PROMOTED.value


class TestListForUser:
    def test_binds_user(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc()])
        results = repo.list_for_user("u1")
        assert len(results) == 1
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["user_key"] == "u1"


class TestSetStatus:
    def test_promote_sets_audit(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        mock_db.collection.return_value.update.return_value = {
            "new": _doc(
                status=PestImageStatus.PROMOTED.value,
                promoted_by="admin1",
                promoted_at="2026-06-21T00:00:00+00:00",
            )
        }
        result = repo.set_status("pic1", PestImageStatus.PROMOTED, "admin1")
        assert result is not None
        assert result.status == PestImageStatus.PROMOTED
        assert result.promoted_by == "admin1"

    def test_missing_returns_none(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.set_status("missing", PestImageStatus.PROMOTED, "admin1") is None


class TestDeleteForTenant:
    def test_returns_removed_count(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([4])
        assert repo.delete_for_tenant("t1") == 4
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["tenant_key"] == "t1"

    def test_zero_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([0])
        assert repo.delete_for_tenant("t1") == 0
