"""Unit tests for ArangoInvitationRepository (REQ-024 / NFR-011 R-12, #1800).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection.

Only :meth:`ArangoInvitationRepository.delete_expired_before` is covered here
(#1800 added it); the repository's other methods had no dedicated unit test
file before this change and are exercised through the integration suite and
the tenant-invitation flows instead.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.invitation_repository import ArangoInvitationRepository


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoInvitationRepository(mock_db)


class TestDeleteExpiredBefore:
    """NFR-011 R-12 — an ``expired`` invitation past the cutoff is hard-deleted, edges first."""

    def test_removes_edges_then_documents(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([1, 1])]

        purged = repo.delete_expired_before("2026-08-27T00:00:00+00:00")

        assert purged == 2
        assert mock_db.aql.execute.call_count == 2
        edges_call, docs_call = mock_db.aql.execute.call_args_list
        assert edges_call.kwargs["bind_vars"]["@edges"] == "has_invitation"
        assert "REMOVE edge" in edges_call.args[0]
        assert "REMOVE doc" in docs_call.args[0]
        for call in (edges_call, docs_call):
            assert call.kwargs["bind_vars"]["expired"] == "expired"
            assert call.kwargs["bind_vars"]["cutoff"] == "2026-08-27T00:00:00+00:00"

    def test_zero_when_nothing_due(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]
        assert repo.delete_expired_before("2026-08-27T00:00:00+00:00") == 0
