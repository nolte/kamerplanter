"""REQ-035 §2, §4 — unit tests for the glossary ArangoDB repositories.

Solitary unit tests: the injected ``StandardDatabase`` is the owned I/O boundary
and is doubled with MagicMock. Query bind_vars and model mapping are asserted; no
real ArangoDB connection.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.data_access.arango.glossary_repository import (
    ArangoGlossaryTermCacheRepository,
    ArangoGlossaryTermRepository,
)
from app.domain.models.glossary_term import GlossaryTerm, GlossaryTermCacheEntry


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def term_repo(mock_db):
    return ArangoGlossaryTermRepository(mock_db)


@pytest.fixture
def cache_repo(mock_db):
    return ArangoGlossaryTermCacheRepository(mock_db)


def _term_doc(**kwargs) -> dict:
    doc = {
        "_key": "vpd",
        "slug": "vpd",
        "labels": {"de": "VPD", "en": "VPD"},
        "category": "umwelt",
        "is_active": True,
        "fallback_text": {"de": "x", "en": "y"},
    }
    doc.update(kwargs)
    return doc


class TestResolveSlug:
    def test_resolves_via_alias(self, term_repo, mock_db):
        mock_db.aql.execute.return_value = iter(["vpd"])
        result = term_repo.resolve_slug("Saettigungsdefizit", "de")
        assert result == "vpd"
        bind = mock_db.aql.execute.call_args.kwargs["bind_vars"]
        assert bind["needle"] == "saettigungsdefizit"  # lowercased
        assert bind["language"] == "de"

    def test_returns_none_when_unknown(self, term_repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert term_repo.resolve_slug("nope", "de") is None


class TestListActive:
    def test_maps_documents_to_models(self, term_repo, mock_db):
        mock_db.aql.execute.return_value = iter([_term_doc(), _term_doc(_key="ec", slug="ec")])
        terms = term_repo.list_active()
        assert len(terms) == 2
        assert all(isinstance(t, GlossaryTerm) for t in terms)

    def test_category_filter_binds(self, term_repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        term_repo.list_active(category="umwelt")
        assert mock_db.aql.execute.call_args.kwargs["bind_vars"]["category"] == "umwelt"


class TestSoftDelete:
    def test_returns_true_on_hit(self, term_repo, mock_db):
        mock_db.aql.execute.return_value = iter([1])
        assert term_repo.soft_delete("vpd") is True

    def test_returns_false_on_miss(self, term_repo, mock_db):
        mock_db.aql.execute.return_value = iter([0])
        assert term_repo.soft_delete("nope") is False


class TestCreateTerm:
    def test_rejects_duplicate(self, term_repo, mock_db):
        from app.common.exceptions import DuplicateError

        mock_db.collection.return_value.has.return_value = True
        with pytest.raises(DuplicateError):
            term_repo.create_term(GlossaryTerm(slug="vpd", labels={"de": "VPD"}))

    def test_inserts_with_slug_key(self, term_repo, mock_db):
        coll = mock_db.collection.return_value
        coll.has.return_value = False
        coll.insert.return_value = {"new": _term_doc()}
        result = term_repo.create_term(GlossaryTerm(slug="vpd", labels={"de": "VPD"}))
        assert isinstance(result, GlossaryTerm)
        assert coll.insert.call_args.args[0]["_key"] == "vpd"


class TestCacheFindValid:
    def test_returns_model_on_hit(self, cache_repo, mock_db):
        mock_db.aql.execute.return_value = iter(
            [{"_key": "c1", "term_slug": "vpd", "language": "de", "expertise_level": "beginner", "answer_text": "A"}]
        )
        entry = cache_repo.find_valid("vpd", "de", "beginner")
        assert isinstance(entry, GlossaryTermCacheEntry)
        assert entry.answer_text == "A"

    def test_returns_none_on_miss(self, cache_repo, mock_db):
        mock_db.aql.execute.return_value = iter([])
        assert cache_repo.find_valid("vpd", "de", "beginner") is None


class TestCacheUpsert:
    def test_deletes_variant_then_creates(self, cache_repo, mock_db):
        # delete_for_variant runs an AQL COLLECT; create inserts the new doc.
        mock_db.aql.execute.return_value = iter([1])
        coll = mock_db.collection.return_value
        coll.insert.return_value = {
            "new": {
                "_key": "c2",
                "term_slug": "vpd",
                "language": "de",
                "expertise_level": "beginner",
                "answer_text": "B",
            }
        }
        entry = GlossaryTermCacheEntry(term_slug="vpd", language="de", expertise_level="beginner", answer_text="B")
        result = cache_repo.upsert(entry)
        assert result.answer_text == "B"
        mock_db.aql.execute.assert_called()  # delete_for_variant ran


class TestCacheInvalidate:
    def test_invalidate_all(self, cache_repo, mock_db):
        mock_db.aql.execute.return_value = iter([7])
        assert cache_repo.invalidate_all() == 7

    def test_invalidate_slug(self, cache_repo, mock_db):
        mock_db.aql.execute.return_value = iter([3])
        assert cache_repo.invalidate_slug("vpd") == 3

    def test_delete_expired(self, cache_repo, mock_db):
        mock_db.aql.execute.return_value = iter([4])
        assert cache_repo.delete_expired() == 4
