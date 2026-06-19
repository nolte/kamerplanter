"""NFR-013 §2.2 — unit tests for ArangoAttachmentRepository.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O
boundary and is doubled with MagicMock. No real ArangoDB connection.
"""

from unittest.mock import MagicMock

import pytest

from app.common.enums import AttachmentCategory
from app.data_access.arango.attachment_repository import ArangoAttachmentRepository
from app.domain.models.attachment import Attachment


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoAttachmentRepository(mock_db)


def _attachment_doc(**kwargs) -> dict:
    doc = {
        "_key": "att1",
        "tenant_key": "t-1",
        "mime_type": "image/jpeg",
        "byte_size": 1024,
        "sha256": "deadbeef",
        "original_filename": "photo.jpg",
        "created_by": "u-1",
        "category": AttachmentCategory.DIARY.value,
        "storage_key": "t-1/diary/att1.jpg",
    }
    doc.update(kwargs)
    return doc


class TestGet:
    def test_returns_model_for_matching_tenant(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _attachment_doc()
        result = repo.get("att1", "t-1")
        assert isinstance(result, Attachment)
        assert result.storage_key == "t-1/diary/att1.jpg"

    def test_returns_none_for_other_tenant(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _attachment_doc(tenant_key="t-2")
        assert repo.get("att1", "t-1") is None

    def test_returns_none_when_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get("att1", "t-1") is None


class TestFindByUser:
    def test_binds_tenant_and_user(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_attachment_doc()])
        results = repo.find_by_user("t-1", "u-1")
        assert len(results) == 1
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["tenant_key"] == "t-1"
        assert bind_vars["user_key"] == "u-1"
        assert bind_vars["categories"] is None

    def test_passes_category_values(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        repo.find_by_user("t-1", "u-1", [AttachmentCategory.DIARY, AttachmentCategory.IPM])
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["categories"] == ["diary", "ipm"]


class TestFindBySha256:
    def test_returns_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_attachment_doc()])
        result = repo.find_by_sha256("t-1", "deadbeef")
        assert isinstance(result, Attachment)
        assert result.sha256 == "deadbeef"

    def test_returns_none_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.find_by_sha256("t-1", "nope") is None


class TestCountByTenant:
    def test_returns_count(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([7])
        assert repo.count_by_tenant("t-1") == 7

    def test_returns_zero_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.count_by_tenant("t-1") == 0


class TestDelete:
    def test_deletes_when_owned(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _attachment_doc()
        assert repo.delete("att1", "t-1") is True

    def test_refuses_when_other_tenant(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _attachment_doc(tenant_key="t-2")
        assert repo.delete("att1", "t-1") is False
