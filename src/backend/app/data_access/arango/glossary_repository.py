"""REQ-035 §2, §4 — ArangoDB repositories for the KI terminology glossary.

Two repositories: :class:`ArangoGlossaryTermRepository` over the curated
``glossary_terms`` skeleton and :class:`ArangoGlossaryTermCacheRepository` over
the ``glossary_term_cache`` RAG answer cache. Both are global reference data
(not tenant-scoped, §6), so no ``tenant_key`` filtering applies.
"""

from __future__ import annotations

from datetime import UTC, datetime

from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.models.glossary_term import GlossaryTerm, GlossaryTermCacheEntry


class ArangoGlossaryTermRepository(BaseArangoRepository[GlossaryTerm]):
    """``glossary_terms`` — the curated term skeleton (§2.1)."""

    _model_cls = GlossaryTerm
    _entity_name = "GlossaryTerm"

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.GLOSSARY_TERMS)

    def get_by_slug(self, slug: str) -> GlossaryTerm | None:
        """Return the term with the canonical ``slug`` (or ``None``)."""
        return self.find_one_by_field("slug", slug)

    def resolve_slug(self, needle: str, language: str) -> str | None:
        """Resolve ``needle`` to a canonical slug via slug or language alias.

        The lookup is case-insensitive and language-sensitive: a value is matched
        against the canonical ``slug`` first, then against the ``aliases.{language}``
        list of every active term. Returns the canonical slug or ``None`` when no
        term matches (§4.1 step 1).
        """
        normalized = needle.strip().lower()
        query = """
        FOR doc IN @@collection
          FILTER doc.is_active == true
          FILTER LOWER(doc.slug) == @needle
             OR @needle IN (
               FOR alias IN (doc.aliases[@language] != null ? doc.aliases[@language] : [])
                 RETURN LOWER(alias)
             )
          LIMIT 1
          RETURN doc.slug
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": self._collection_name,
                "needle": normalized,
                "language": language,
            },
        )
        return next(cursor, None)

    def list_active(self, *, category: str | None = None) -> list[GlossaryTerm]:
        """Return all active terms, optionally filtered by ``category`` (§3.1)."""
        filters = "FILTER doc.is_active == true"
        bind_vars: dict = {"@collection": self._collection_name}
        if category:
            filters += "\n          FILTER doc.category == @category"
            bind_vars["category"] = category
        query = f"""
        FOR doc IN @@collection
          {filters}
          SORT doc.category ASC, doc.slug ASC
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [GlossaryTerm(**doc) for doc in cursor]

    def list_all_including_inactive(self, *, category: str | None = None) -> list[GlossaryTerm]:
        """Platform-admin listing including soft-deleted terms (§3.3)."""
        filters = ""
        bind_vars: dict = {"@collection": self._collection_name}
        if category:
            filters = "FILTER doc.category == @category"
            bind_vars["category"] = category
        query = f"""
        FOR doc IN @@collection
          {filters}
          SORT doc.category ASC, doc.slug ASC
          RETURN doc
        """
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [GlossaryTerm(**doc) for doc in cursor]

    def create_term(self, term: GlossaryTerm) -> GlossaryTerm:
        """Insert a new term keyed by its ``slug`` (§3.3 admin create).

        Raises :class:`~app.common.exceptions.DuplicateError` when the slug is
        already taken (the unique ``slug`` index also guards this at storage
        level).
        """
        from app.common.exceptions import DuplicateError

        now = datetime.now(UTC).isoformat()
        doc = term.model_dump(by_alias=True, exclude_none=True, mode="json")
        doc.pop("_key", None)
        doc["_key"] = term.slug
        doc["created_at"] = now
        doc["updated_at"] = now
        if self.collection.has(term.slug):
            raise DuplicateError("GlossaryTerm", "slug", term.slug)
        result = self.collection.insert(doc, return_new=True)
        return GlossaryTerm(**self._from_doc(result["new"]))

    def update_term(self, slug: str, term: GlossaryTerm) -> GlossaryTerm:
        """Replace the editable fields of the term with ``slug`` (§3.3 admin edit)."""
        from app.common.exceptions import NotFoundError

        if not self.collection.has(slug):
            raise NotFoundError("GlossaryTerm", slug)
        doc = term.model_dump(by_alias=True, exclude_none=True, mode="json")
        doc.pop("_key", None)
        doc["slug"] = slug
        doc["updated_at"] = datetime.now(UTC).isoformat()
        result = self.collection.update({"_key": slug, **doc}, return_new=True, keep_none=False)
        return GlossaryTerm(**self._from_doc(result["new"]))

    def soft_delete(self, slug: str) -> bool:
        """Set ``is_active=false`` for the term with ``slug`` (§3.3). Returns hit."""
        query = """
        FOR doc IN @@collection
          FILTER doc.slug == @slug
          UPDATE doc WITH { is_active: false, updated_at: @now } IN @@collection
          COLLECT WITH COUNT INTO updated
          RETURN updated
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": self._collection_name,
                "slug": slug,
                "now": datetime.now(UTC).isoformat(),
            },
        )
        return next(cursor, 0) > 0


class ArangoGlossaryTermCacheRepository(BaseArangoRepository[GlossaryTermCacheEntry]):
    """``glossary_term_cache`` — cached RAG answers per term/language/level (§2.2)."""

    _model_cls = GlossaryTermCacheEntry
    _entity_name = "GlossaryTermCacheEntry"

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.GLOSSARY_TERM_CACHE)

    def find_valid(
        self,
        term_slug: str,
        language: str,
        expertise_level: str,
        *,
        now: datetime | None = None,
    ) -> GlossaryTermCacheEntry | None:
        """Return the still-valid cached answer for a term variant, or ``None``."""
        stamp = (now or datetime.now(UTC)).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.term_slug == @term_slug
          FILTER doc.language == @language
          FILTER doc.expertise_level == @expertise_level
          FILTER doc.valid_until == null OR doc.valid_until > @now
          SORT doc.generated_at DESC
          LIMIT 1
          RETURN doc
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": self._collection_name,
                "term_slug": term_slug,
                "language": language,
                "expertise_level": expertise_level,
                "now": stamp,
            },
        )
        doc = next(cursor, None)
        return GlossaryTermCacheEntry(**doc) if doc else None

    def upsert(self, entry: GlossaryTermCacheEntry) -> GlossaryTermCacheEntry:
        """Insert or replace the cache entry for its unique key tuple (§4.1 step 8).

        Any pre-existing entries for the same (term, language, level) are removed
        first, so a regenerated answer with a new ``kb_version`` never collides
        with the stale row on the unique index.
        """
        self.delete_for_variant(entry.term_slug, entry.language, entry.expertise_level)
        return self.create(entry)

    def delete_for_variant(self, term_slug: str, language: str, expertise_level: str) -> int:
        """Remove all cache rows for a term/language/level (used before upsert)."""
        query = """
        FOR doc IN @@collection
          FILTER doc.term_slug == @term_slug
          FILTER doc.language == @language
          FILTER doc.expertise_level == @expertise_level
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": self._collection_name,
                "term_slug": term_slug,
                "language": language,
                "expertise_level": expertise_level,
            },
        )
        return next(cursor, 0)

    def invalidate_slug(self, term_slug: str) -> int:
        """Delete every cached variant for one term (§3.3 cache invalidate)."""
        query = """
        FOR doc IN @@collection
          FILTER doc.term_slug == @term_slug
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": self._collection_name, "term_slug": term_slug},
        )
        return next(cursor, 0)

    def invalidate_all(self) -> int:
        """Delete the entire glossary cache (§3.3, §4.3 reingest invalidation)."""
        query = """
        FOR doc IN @@collection
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(query, bind_vars={"@collection": self._collection_name})
        return next(cursor, 0)

    def delete_expired(self, *, now: datetime | None = None) -> int:
        """Remove cache rows whose ``valid_until`` has passed (§4.3 cleanup)."""
        cutoff = (now or datetime.now(UTC)).isoformat()
        query = """
        FOR doc IN @@collection
          FILTER doc.valid_until != null AND doc.valid_until < @cutoff
          REMOVE doc IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={"@collection": self._collection_name, "cutoff": cutoff},
        )
        return next(cursor, 0)
