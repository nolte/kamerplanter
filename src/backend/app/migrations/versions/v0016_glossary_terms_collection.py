"""v0016 — REQ-035 KI glossary: ``glossary_terms`` + ``glossary_term_cache``.

Creates the two document collections that back the KI terminology glossary on
*existing* volumes and adds their persistent indexes (§2.1, §2.2):

* ``glossary_terms`` — unique ``slug`` + ``category`` + ``is_active`` indexes;
* ``glossary_term_cache`` — unique ``(term_slug, language, expertise_level,
  kb_version)`` + ``valid_until`` cleanup index.

Both collections are global reference data (not tenant-scoped, §6). Fresh
databases already get all of this from the idempotent startup
``ensure_collections`` (``collections.py``), which the app lifespan runs *before*
migrations; this migration brings existing volumes — and the standalone
``python -m app.migrations`` path, which does not call ``ensure_collections`` — to
the same shape.

Purely additive and idempotent (M-3): every step checks for existence first, so a
re-run (or a fresh DB that was already bootstrapped) is a no-op (``changed == 0``).
No data is read or rewritten. Irreversible (M-6): dropping a collection that the
bootstrap also creates would not honestly restore the pre-migration state, so no
inverse is offered.
"""

from __future__ import annotations

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger()

_DOC_COLLECTIONS = [col.GLOSSARY_TERMS, col.GLOSSARY_TERM_CACHE]

#: ``(collection, fields, unique)`` index specifications (§2.1, §2.2).
_INDEXES: list[tuple[str, list[str], bool]] = [
    (col.GLOSSARY_TERMS, ["slug"], True),
    (col.GLOSSARY_TERMS, ["category"], False),
    (col.GLOSSARY_TERMS, ["is_active"], False),
    (col.GLOSSARY_TERM_CACHE, ["term_slug", "language", "expertise_level", "kb_version"], True),
    (col.GLOSSARY_TERM_CACHE, ["valid_until"], False),
]


def _has_index(indexes: object, fields: list[str]) -> bool:
    if not isinstance(indexes, list):
        return False
    return any(
        isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == fields for idx in indexes
    )


class GlossaryTermsCollectionMigration(Migration):
    version = "0016"
    name = "glossary_terms_collection"
    description = "Create the REQ-035 glossary_terms + glossary_term_cache collections on existing volumes."
    reversible = False

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        docs_missing = [name for name in _DOC_COLLECTIONS if not db.has_collection(name)]

        index_missing: list[tuple[str, list[str], bool]] = []
        for collection_name, fields, unique in _INDEXES:
            present = [] if collection_name in docs_missing else db.collection(collection_name).indexes()
            if collection_name in docs_missing or not _has_index(present, fields):
                index_missing.append((collection_name, fields, unique))

        pending = {
            "document_collections": docs_missing,
            "indexes": [f"{name}:{fields}" for name, fields, _ in index_missing],
        }
        changes = len(docs_missing) + len(index_missing)
        scanned = len(_DOC_COLLECTIONS) + len(_INDEXES)

        if dry_run:
            logger.info("glossary_migration_dry_run", pending=pending)
            return MigrationReport(
                version=self.version, name=self.name, scanned=scanned, changed=0, dry_run=True, details=pending
            )

        for name in docs_missing:
            db.create_collection(name)

        for collection_name, fields, unique in index_missing:
            collection = db.collection(collection_name)
            if not _has_index(collection.indexes(), fields):
                collection.add_persistent_index(fields=fields, unique=unique)

        logger.info("glossary_migration_applied", changed=changes, pending=pending)
        return MigrationReport(
            version=self.version, name=self.name, scanned=scanned, changed=changes, dry_run=False, details=pending
        )


migration = GlossaryTermsCollectionMigration()
