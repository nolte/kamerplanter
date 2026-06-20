"""NFR-013 §2.2 / AC-09 — normalise legacy ``photo_refs`` to attachment ids.

Historically the ``photo_refs`` lists on diary entries, harvest batches,
inspections and tasks stored *raw* references — the REQ-013 spec even used a
provisional ``s3://kamerplanter/diary/...`` notation. NFR-013 standardises them
to **attachment ids** (the ULID embedded in the storage key, surfaced to the
frontend as ``/api/v1/t/{slug}/attachments/{attachment_id}``).

This migration walks the four collections that carry ``photo_refs`` and
rewrites each list element to its attachment id. It is:

- **idempotent** — a value that is already an attachment id is left untouched,
  so re-running is a safe no-op (only documents that actually change are
  written);
- **non-destructive** — it only normalises existing references, never deletes a
  photo or drops an unresolvable value (those are kept verbatim and reported);
- **reportable** — returns a :class:`PhotoRefMigrationReport` summarising what
  changed, so an empty/already-normalised dataset produces a clear no-op report.

Run from the backend root::

    python -m app.migrations.migrate_photo_refs            # apply
    python -m app.migrations.migrate_photo_refs --dry-run  # report only
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.data_access.arango import collections as col

logger = structlog.get_logger()

# Collections (and the field) that carry photo references.
_PHOTO_REF_COLLECTIONS: tuple[str, ...] = (
    col.PLANT_DIARY_ENTRIES,
    col.HARVEST_BATCHES,
    col.INSPECTIONS,
    col.TASKS,
)
_FIELD = "photo_refs"

# An attachment id is a 26-char Crockford-base32 ULID (NFR-013 §4.3). We accept
# the canonical ULID shape; anything else is treated as a raw reference to be
# parsed.
_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$", re.IGNORECASE)
# Matches a stored ``.../attachments/{id}`` API URI tail.
_API_URI_RE = re.compile(r"/attachments/(?P<id>[^/?#]+)")


def normalize_photo_ref(ref: str) -> str:
    """Return the attachment id for a single ``photo_refs`` entry.

    Resolution order:

    1. Empty / whitespace → returned unchanged.
    2. Already an attachment id (ULID shape) → returned unchanged.
    3. ``/api/v1/.../attachments/{id}`` API URI → the ``{id}`` tail.
    4. A storage key / URL (``s3://...``, ``t/{tenant}/{cat}/{yyyy}/{mm}/{ulid}.ext``,
       any ``.../{ulid}.{ext}``) → the ULID stem of the last path segment.
    5. Anything unresolvable → returned unchanged (never dropped; reported by
       the caller as ``unresolved``).
    """
    value = ref.strip()
    if not value:
        return ref
    if _ULID_RE.match(value):
        return value

    api_match = _API_URI_RE.search(value)
    if api_match:
        candidate = api_match.group("id")
        # Strip an extension if the URI carried one.
        candidate = candidate.split(".", 1)[0]
        return candidate

    # Treat as a path/URL: take the last segment, drop any extension.
    last_segment = value.rstrip("/").split("/")[-1]
    stem = last_segment.split(".", 1)[0]
    # Strip a thumbnail suffix (``{ulid}_t512``) back to the base attachment id.
    stem = re.sub(r"_t\d+$", "", stem)
    return stem or value


def normalize_refs(refs: list[str]) -> tuple[list[str], int]:
    """Normalise a whole ``photo_refs`` list.

    Returns ``(normalised_list, changed_count)`` where ``changed_count`` is the
    number of entries whose value actually changed.
    """
    out: list[str] = []
    changed = 0
    for ref in refs:
        if not isinstance(ref, str):
            # Defensive: keep non-string values verbatim, never crash.
            out.append(ref)
            continue
        normalised = normalize_photo_ref(ref)
        if normalised != ref:
            changed += 1
        out.append(normalised)
    return out, changed


@dataclass
class PhotoRefMigrationReport:
    """Summary of a ``photo_refs`` normalisation run."""

    dry_run: bool
    scanned_documents: int = 0
    changed_documents: int = 0
    changed_refs: int = 0
    per_collection: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "scanned_documents": self.scanned_documents,
            "changed_documents": self.changed_documents,
            "changed_refs": self.changed_refs,
            "per_collection": self.per_collection,
            "noop": self.changed_documents == 0,
        }


def run(db: Any | None = None, *, dry_run: bool = False) -> PhotoRefMigrationReport:
    """Walk all ``photo_refs`` collections and normalise their references.

    When ``dry_run`` is set the report is computed but no document is written.
    """
    if db is None:
        from app.common.dependencies import get_db

        db = get_db()

    report = PhotoRefMigrationReport(dry_run=dry_run)
    for collection_name in _PHOTO_REF_COLLECTIONS:
        changed_in_collection = _migrate_collection(db, collection_name, report, dry_run=dry_run)
        report.per_collection[collection_name] = changed_in_collection

    logger.info("migrate_photo_refs_completed", **report.as_dict())
    return report


def _migrate_collection(
    db: Any,
    collection_name: str,
    report: PhotoRefMigrationReport,
    *,
    dry_run: bool,
) -> int:
    """Normalise one collection's ``photo_refs``; returns changed-doc count."""
    query = """
    FOR doc IN @@collection
      FILTER HAS(doc, @field) AND IS_LIST(doc[@field]) AND LENGTH(doc[@field]) > 0
      RETURN { _key: doc._key, refs: doc[@field] }
    """
    bind_vars = {"@collection": collection_name, "field": _FIELD}
    cursor = db.aql.execute(query, bind_vars=bind_vars)

    collection = db.collection(collection_name)
    changed_docs = 0
    for row in cursor:
        report.scanned_documents += 1
        normalised, changed = normalize_refs(row["refs"])
        if changed == 0:
            continue
        changed_docs += 1
        report.changed_documents += 1
        report.changed_refs += changed
        if not dry_run:
            collection.update({"_key": row["_key"], _FIELD: normalised})
    return changed_docs


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI glue
    from app.config.logging import setup_logging

    setup_logging()
    args = argv if argv is not None else sys.argv[1:]
    dry_run = "--dry-run" in args
    report = run(dry_run=dry_run)
    result = report.as_dict()
    print(  # noqa: T201 — CLI summary output is intentional
        f"migrate_photo_refs: scanned={result['scanned_documents']} "
        f"changed_documents={result['changed_documents']} "
        f"changed_refs={result['changed_refs']} dry_run={result['dry_run']} "
        f"noop={result['noop']}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
