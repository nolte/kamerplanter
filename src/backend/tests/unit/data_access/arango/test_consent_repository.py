"""Unit tests for ArangoConsentRepository (REQ-025).

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. No real ArangoDB connection. Assertions target
returned ``ConsentRecord`` models and the AQL bind_vars / edges emitted.
"""

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.consent_repository import ArangoConsentRepository
from app.domain.models.privacy import ConsentRecord


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def repo(mock_db):
    return ArangoConsentRepository(mock_db)


def _doc(**kwargs) -> dict:
    doc = {"_key": "c1", "user_key": "u1", "purpose": "sentry", "granted": True}
    doc.update(kwargs)
    return doc


def _model(**kwargs) -> ConsentRecord:
    defaults = {"user_key": "u1", "purpose": "sentry", "granted": True}
    defaults.update(kwargs)
    return ConsentRecord(**defaults)


class TestCreate:
    def test_creates_record_and_user_edge(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc()}

        result = repo.create(_model())

        assert isinstance(result, ConsentRecord)
        assert result.key == "c1"
        # Document insert + has_consent edge insert.
        assert coll.insert.call_count == 2
        edge = coll.insert.call_args_list[1].args[0]
        assert edge["_from"] == "users/u1"
        assert edge["_to"] == "consent_records/c1"

    def test_skips_edge_without_user_key(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.insert.return_value = {"new": _doc(user_key="")}

        repo.create(_model(user_key=""))

        assert coll.insert.call_count == 1


class TestGetByKey:
    def test_found(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = _doc()
        assert isinstance(repo.get_by_key("c1"), ConsentRecord)

    def test_missing(self, repo, mock_db):
        mock_db.collection.return_value.get.return_value = None
        assert repo.get_by_key("c1") is None


class TestGetByUserAndPurpose:
    def test_returns_first_match(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(purpose="hibp")])

        result = repo.get_by_user_and_purpose("u1", "hibp")

        assert result.purpose == "hibp"
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["user_key"] == "u1"
        assert bind_vars["purpose"] == "hibp"

    def test_returns_none_when_empty(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.get_by_user_and_purpose("u1", "hibp") is None


class TestUpdate:
    def test_returns_model(self, repo, mock_db):
        coll = mock_db.collection.return_value
        coll.update.return_value = {"new": _doc(granted=False)}

        result = repo.update("c1", _model(granted=False))

        assert result.granted is False
        assert coll.update.call_args.args[0]["_key"] == "c1"


class TestListByUser:
    def test_maps_models(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([_doc(), _doc(_key="c2", purpose="enrichment")])

        result = repo.list_by_user("u1")

        assert len(result) == 2
        assert all(isinstance(r, ConsentRecord) for r in result)


class TestDelete:
    def test_removes_edges_then_deletes(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        mock_db.collection.return_value.delete.return_value = True

        assert repo.delete("c1") is True
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"] == {"consent_id": "consent_records/c1"}
        mock_db.collection.return_value.delete.assert_called_once_with("c1")


class TestDeleteAllForUser:
    def test_counts_removed_rows(self, repo, mock_db):
        # side_effect (not return_value) yields a fresh cursor per call, so the
        # assertion holds even if the method is invoked more than once.
        mock_db.aql.execute.side_effect = lambda *a, **k: iter([1, 1, 1])

        assert repo.delete_all_for_user("u1") == 3

    def test_zero_when_nothing_removed(self, repo, mock_db):
        mock_db.aql.execute.side_effect = lambda *a, **k: iter([])
        assert repo.delete_all_for_user("u1") == 0


class TestListUnanonymizedIpsBefore:
    """NFR-011 R-04a (#1800) — the R-03 analogue for ``consent_records``."""

    def test_returns_key_ip_pairs(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter(
            [{"_key": "c1", "ip_address": "192.0.2.42"}, {"_key": "c2", "ip_address": "2001:db8::1"}]
        )

        result = repo.list_unanonymized_ips_before("2026-09-18T00:00:00+00:00")

        assert result == [("c1", "192.0.2.42"), ("c2", "2001:db8::1")]
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["cutoff"] == "2026-09-18T00:00:00+00:00"

    def test_empty_when_nothing_due(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert repo.list_unanonymized_ips_before("2026-09-18T00:00:00+00:00") == []


class TestMarkIpAnonymized:
    """#1800 security review (SEC-003) — a conditional write, not a blind overwrite."""

    def test_writes_the_anonymised_ip_and_stamp_when_still_the_selected_ip(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([1])

        written = repo.mark_ip_anonymized("c1", "192.0.2.42", "192.0.2.0", "2026-09-25T04:00:00+00:00")

        assert written is True
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["key"] == "c1"
        assert bind_vars["previous_ip"] == "192.0.2.42"
        assert bind_vars["anonymized_ip"] == "192.0.2.0"
        assert bind_vars["anonymized_at"] == "2026-09-25T04:00:00+00:00"
        assert "ip_anonymized_at == null" in mock_db.aql.execute.call_args.args[0]

    def test_skips_the_write_when_a_concurrent_regrant_changed_the_ip(self, repo, mock_db):
        """A re-grant between selection and this write must not be overwritten by a stale hash."""
        mock_db.aql.execute.return_value = iter([])

        written = repo.mark_ip_anonymized("c1", "192.0.2.42", "192.0.2.0", "2026-09-25T04:00:00+00:00")

        assert written is False


class TestDeleteRevokedBefore:
    """NFR-011 R-04 (#1800) — edges removed first, then the revoked-and-expired records."""

    def test_removes_edges_then_documents(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([1, 1])]

        purged = repo.delete_revoked_before("2023-09-25T00:00:00+00:00")

        assert purged == 2
        assert mock_db.aql.execute.call_count == 2
        edges_call, docs_call = mock_db.aql.execute.call_args_list
        assert edges_call.kwargs["bind_vars"]["@edges"] == "has_consent"
        assert "REMOVE edge" in edges_call.args[0]
        assert "REMOVE doc" in docs_call.args[0]
        for call in (edges_call, docs_call):
            assert call.kwargs["bind_vars"]["cutoff"] == "2023-09-25T00:00:00+00:00"

    def test_zero_when_nothing_due(self, repo, mock_db):
        mock_db.aql.execute.side_effect = [iter([]), iter([])]

        assert repo.delete_revoked_before("2023-09-25T00:00:00+00:00") == 0


class TestRevokeAllUnrevoked:
    """NFR-011 R-04 (#1800 review, SEC-001) — run at erasure so an unrevoked consent stays reachable by the purge."""

    def test_revokes_every_unrevoked_record_of_the_user(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([1, 1])

        revoked = repo.revoke_all_unrevoked("u1", "2026-09-25T04:35:00+00:00")

        assert revoked == 2
        bind_vars = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind_vars["user_key"] == "u1"
        assert bind_vars["now"] == "2026-09-25T04:35:00+00:00"
        query = mock_db.aql.execute.call_args.args[0]
        assert "revoked_at == null" in query
        assert "granted: false" in query

    def test_zero_when_nothing_unrevoked(self, repo, mock_db):
        mock_db.aql.execute.return_value = iter([])

        assert repo.revoke_all_unrevoked("u1", "2026-09-25T04:35:00+00:00") == 0
