"""NFR-013 §2.2 / AC-09 — rewrite ``photo_refs`` API URIs to attachment ids.

``photo_refs`` lists (diary entries, plant galleries, inspections, harvest and
storage observations, tasks) hold **attachment ids** per NFR-013 §2.2 — the
document key of the row in ``attachments``. Legacy rows hold other spellings,
and this migration rewrites the one spelling that can be resolved from its own
text: the ``/api/v1/t/{slug}/attachments/{id}`` API URI, whose ``{id}`` segment
*is* that document key.

**What this module deliberately does not do: resolve a storage key.** A storage
key (``t/{tenant}/{cat}/{yyyy}/{mm}/{ulid}.{ext}``, or the same behind
``s3://``) ends in a ULID that ``StorageKeyBuilder.build`` mints for the object;
the attachment's ``_key`` is a short **numeric** id ArangoDB assigns
(``BaseArangoRepository._to_doc`` pops ``_key`` before the insert and no key
generator is configured). The two identities are unrelated, so the ULID stem
names no document — measured in #1393 round 7. Until #1438 this module reduced
such a reference to that stem anyway, turning a reference the readers resolve
today (``ArangoAttachmentRepository`` compares an entry against the
attachment's own ``storage_key``) into one that resolves to nothing. Such an
entry is now returned **verbatim**.

Reconciling a reference against the attachment catalogue — the only way to map
a storage key to a document key — needs the catalogue, which a pure text
transformation does not have. That is owned by
``versions/v0046_reconcile_photo_refs.py`` (#1438 part 2), not by this module:
v0046 rewrites an entry onto the ``_key`` of the single attachment it denotes
and reports every entry that denotes nothing.

It is:

- **idempotent** — a value it cannot rewrite is left untouched, so re-running is
  a safe no-op (only documents that actually change are written);
- **non-destructive** — it never deletes a photo or drops a value it cannot
  resolve (those are kept verbatim and reported);
- **reportable** — returns a :class:`PhotoRefMigrationReport` summarising what
  changed, so an empty/already-normalised dataset produces a clear no-op report.

**Writing is an explicit decision** at every entry point (``run``, the Celery
task and the CLI all default to ``dry_run=True``): the rewrite is irreversible
(``v0003`` declares ``reversible = False``) and this module's premise has been
wrong once already.

Run from the backend root::

    python -m app.migrations.migrate_photo_refs          # report only (default)
    python -m app.migrations.migrate_photo_refs --write  # apply
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.data_access.arango.attachment_repository import PHOTO_REF_COLLECTIONS

logger = structlog.get_logger()

# Collections (and the field) that carry photo references.
#
# Taken from the pinned carrier list rather than repeated here. The local copy this
# replaces was **wrong in both directions**, measured: it named ``HARVEST_BATCHES``,
# which has no ``photo_refs`` at all (the field is on ``HarvestObservation``), and it
# omitted ``PLANT_INSTANCES``, ``HARVEST_OBSERVATIONS`` and ``STORAGE_OBSERVATIONS``,
# all three of which carry it. So the migration reported success while leaving every
# legacy reference in the plant gallery and the harvest/storage observations
# untouched — and this migration is named in #1393's safety story as part of the
# reference history the orphan sweep has to survive.
#
# ``PHOTO_REF_COLLECTIONS`` is pinned against the models by
# ``tests/unit/data_access/arango/test_photo_ref_carriers.py``, so consuming it means
# a seventh carrier reaches this migration without anyone remembering it exists.
_PHOTO_REF_COLLECTIONS: tuple[str, ...] = PHOTO_REF_COLLECTIONS
_FIELD = "photo_refs"

# A ULID-shaped entry. Note what this shape does **not** prove: an attachment's
# ``_key`` is numeric, so a ULID here is an object id from a storage key, a thumbnail
# stem, or an id from some other system — never, by itself, a resolvable attachment
# id. The rule keyed on it therefore only trims and passes the value through; it is
# not evidence that the reference resolves (#1438).
_ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$", re.IGNORECASE)
# Matches a stored ``.../attachments/{id}`` API URI tail.
_API_URI_RE = re.compile(r"/attachments/(?P<id>[^/?#]+)")


def normalize_photo_ref(ref: str) -> str:
    """Return the attachment id for a single ``photo_refs`` entry.

    Resolution order:

    1. Empty / whitespace → returned unchanged.
    2. ULID shape → trimmed and passed through. This is *not* a claim that the
       value is an attachment id (a ``_key`` is numeric); it is a foreign id this
       function has no catalogue to resolve, and leaving it alone is the same
       answer rule 3 gives — minus surrounding whitespace.
    3. ``/api/v1/.../attachments/{id}`` API URI → the ``{id}`` tail. The only
       rewrite left, and it is sound because the URI is built *from* the document
       key, so the key can be read back out of it.
    4. Anything else — a storage key, an ``s3://`` URL, a thumbnail rendition, an
       unparseable legacy value → returned unchanged (never dropped; reported by
       the caller as an unchanged entry).

    Rule 4 used to reduce a storage key to the ULID stem of its last path segment.
    That stem is the object id ``StorageKeyBuilder`` minted, not the attachment's
    ``_key``, so the rewrite replaced a reference the readers resolve (via the
    ``storage_key`` comparison in ``ArangoAttachmentRepository``) with one that
    resolves to nothing — see the module docstring and #1438. Mapping a storage
    key onto a document key requires the attachment catalogue and belongs to the
    reconcile migration, not to a pure string transformation.
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

    return ref


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


def run(db: Any | None = None, *, dry_run: bool = True) -> PhotoRefMigrationReport:
    """Walk all ``photo_refs`` collections and normalise their references.

    Defaults to ``dry_run=True``: the report is computed but no document is
    written. Writing is irreversible (the original reference is not retained) and
    this migration's premise was wrong once already (#1438), so a caller that
    omits the keyword gets the report rather than a rewrite. Pass
    ``dry_run=False`` to apply.
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


def dry_run_from_argv(args: list[str]) -> bool:
    """Decide from the CLI arguments whether this is a report-only run.

    ``--write`` is the only way to write; ``--dry-run`` is still accepted and wins
    when both are given, so a script that passed it before this change keeps
    behaving identically. Before #1438 the polarity was the other way round and an
    irreversible rewrite was what a bare invocation did.
    """
    if "--dry-run" in args:
        return True
    return "--write" not in args


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI glue
    from app.config.logging import setup_logging

    setup_logging()
    args = argv if argv is not None else sys.argv[1:]
    dry_run = dry_run_from_argv(args)
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
