"""v0046_reconcile_photo_refs — the one owner of "which attachment is this reference".

#1438 part 2. Every ``photo_refs`` entry names an attachment, but until now no
component owned the mapping. Three of them guessed:

* ``v0003_normalize_photo_refs`` reduced a storage key to the ULID in its last path
  segment. That ULID is **not** a document key (NFR-013 §2.2 — ``StorageKeyBuilder``
  mints its own, ArangoDB assigns a numeric ``_key``), so on every installation that
  booted since v0003 the rewrite turned references the readers resolved into
  references that resolve to nothing. v0003 stays applied and untouched in the
  ledger; this version repairs what it wrote.
* the task-photo delete route (``DELETE /tasks/{key}/photos/{id}``) and a manual
  ``DELETE /attachments/{id}`` both leave the carrier's list pointing at a row that
  no longer exists.
* the orphan sweep answers the opposite question — *which attachment does nobody
  reference* — and ships disabled.

Exactly two rules, over every carrier in
:data:`~app.data_access.arango.attachment_repository.PHOTO_REF_COLLECTIONS` and every
field in :data:`~app.data_access.arango.attachment_repository.ATTACHMENT_REF_FIELDS`
(``cover_photo_ref`` and friends — the same pinned lists the sweep reads, so a
seventh carrier reaches this migration without anyone remembering it exists):

1. **Repair.** An entry that is no attachment ``_key`` of the same tenant, but names
   **exactly one** attachment of the same tenant, is rewritten to that attachment's
   ``_key``. Matching several is reported as ``ambiguous`` and left alone — a rewrite
   that picks one of two candidates is a silent, irreversible guess.

   "Names" is deliberately narrow, and each identity answers only for itself: an API
   URI is read through ``migrate_photo_refs.normalize_photo_ref`` and its ``{id}``
   segment compared **verbatim** against ``_key``; any other spelling is reduced to
   its storage-key stem and compared against ``storage_key``'s stem — never against
   ``_key``. Document keys are short numeric strings, so the stem of a reference
   (``…/attachments/{id}/thumbnails/320`` reduces to ``"320"``, a storage layout's
   year segment to ``"2026"``) collides with a live key routinely, and accepting such
   a hit would rewrite the reference onto a *different, existing* photo.
2. **Report, never drop.** An entry that resolves to nothing is left **verbatim** and
   counted as ``unresolved`` (with collection, document key and tenant). Deleting a
   reference is the orphan sweep's question and needs its own release decision; the
   same never-drop rule ``migrate_photo_refs.test_never_drops_values`` pins.

**Neither answer is duplicated.** The stem comparison runs both its halves through
:func:`~app.data_access.arango.attachment_repository.aql_storage_key_stem`, the
expression the orphan sweep itself uses, and the URI is read by the only other
component that answers "what does this reference mean",
:func:`~app.migrations.migrate_photo_refs.normalize_photo_ref`. Those two answering
differently — the normaliser taking the *first* segment after ``/attachments/``,
this migration the *last* — is precisely the root cause of #1438.

**Idempotent (M-3):** a repaired entry equals a live ``_key`` on the next run and is
classified ``canonical`` — a re-run reports ``changed=0``. **Dry-run (M-5):** the full
report is computed and nothing is written; that is the mode this migration was first
run in against the dev cluster.

**Irreversible (M-6), and safe anyway.** The prior spelling is not retained, so there
is no honest inverse. What makes that acceptable is the narrowness of the write: the
only value ever written is the ``_key`` of an attachment that *exists*, belongs to
the same tenant, and is the *unique* attachment the reference denotes. Nothing is
deleted, no document without a matching reference is touched, and the value replaced
was — by construction of rule 1 — one that resolved to no document key.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import (
    ATTACHMENT_REF_FIELDS,
    PHOTO_REF_COLLECTIONS,
    aql_storage_key_stem,
)
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport
from app.migrations.migrate_photo_refs import normalize_photo_ref

logger = structlog.get_logger()

#: The list-valued reference field every photo carrier holds.
PHOTO_REFS_FIELD = "photo_refs"

#: Every ``(collection, field)`` pair that can hold an attachment reference.
#:
#: Both halves come from the pinned module-level tuples in the repository, never from
#: a copy: ``test_photo_ref_carriers.py`` asserts them against the models that declare
#: the fields, so this migration widens with the carriers instead of drifting behind
#: them. Scalar and list fields are both here; the scan normalises the two shapes.
REFERENCE_FIELDS: tuple[tuple[str, str], ...] = tuple(
    [(collection, PHOTO_REFS_FIELD) for collection in PHOTO_REF_COLLECTIONS] + list(ATTACHMENT_REF_FIELDS)
)

#: How many references are reduced to their stem in one AQL round trip.
_STEM_BATCH = 1000

#: How many ``ambiguous`` / ``unresolved`` rows the report carries verbatim.
#:
#: The counts are always exact (``*_total``); only the itemised lists are capped, so a
#: pathological installation cannot turn one report document into a memory problem.
_REPORT_SAMPLE_LIMIT = 500


@dataclass(frozen=True)
class AttachmentIdentity:
    """The two identities one attachment answers to, plus its tenant."""

    key: str
    tenant_key: str | None
    storage_stem: str | None


@dataclass(frozen=True)
class ReferenceVerdict:
    """What a single reference turned out to denote.

    ``verdict`` is one of ``canonical`` (already an attachment key of this tenant —
    nothing to do), ``repaired``, ``ambiguous`` or ``unresolved``; ``matches`` holds
    the attachment keys the reference denotes, sorted for a stable report.
    """

    verdict: str
    matches: tuple[str, ...] = ()


def build_identity_index(
    attachments: Sequence[AttachmentIdentity],
) -> dict[str, list[AttachmentIdentity]]:
    """Index attachments by **both** identities they answer to.

    One attachment is reachable under its ``_key`` and under its storage-key stem;
    an attachment without a ``storage_key`` contributes only the former.

    The index is deliberately *not* the decision: a lookup hit says "some attachment
    answers to this string", never "under which identity". :func:`plan_reference`
    re-checks that, because the two identities must not be interchangeable — a
    reference's stem may match a ``storage_stem`` and never a ``_key`` (B-1).
    """
    index: dict[str, list[AttachmentIdentity]] = {}
    for attachment in attachments:
        for identity in (attachment.key, attachment.storage_stem):
            if identity:
                index.setdefault(identity, []).append(attachment)
    return index


def _belongs_to(attachment: AttachmentIdentity, tenant_key: str | None) -> bool:
    """May *attachment* answer for a carrier document of *tenant_key*?

    A carrier that carries no ``tenant_key`` at all (``harvest_observations``,
    ``storage_observations``, ``pests`` — measured, not assumed: the field is read
    off the document, so a carrier gaining one later needs no edit here) accepts an
    attachment of any tenant, which makes the uniqueness demand of rule 1
    installation-wide for those rows rather than per tenant. That is the strict
    direction: it reports ``ambiguous`` where a tenant-scoped question would have
    rewritten.
    """
    if not tenant_key:
        return True
    return attachment.tenant_key == tenant_key


def _matching_key(
    lookup: str,
    tenant_key: str | None,
    index: Mapping[str, list[AttachmentIdentity]],
) -> str | None:
    """The attachment whose **document key** is *lookup*, if this tenant owns it."""
    for attachment in index.get(lookup, ()):
        if attachment.key == lookup and _belongs_to(attachment, tenant_key):
            return attachment.key
    return None


def plan_reference(
    reference: str,
    stem: str | None,
    tenant_key: str | None,
    index: Mapping[str, list[AttachmentIdentity]],
) -> ReferenceVerdict:
    """Decide what one reference denotes — the whole rule, free of any database.

    Three ways a reference can name an attachment, and **each identity is compared
    only against its own counterpart** (B-1):

    a. the entry *is* a document key of this tenant → ``canonical``. It wins
       outright: no stem coincidence may promote the target form to ``ambiguous``
       and stall a re-run's idempotency.
    b. the entry is an API URI → the ``{id}`` segment
       :func:`~app.migrations.migrate_photo_refs.normalize_photo_ref` reads out of
       it, compared **verbatim against ``_key``**. That function is the other
       consumer of "what does this reference mean", and the two disagreeing on one
       string is the root cause this migration exists for, so the answer is taken
       from it rather than re-derived. A URI whose id names no live row is
       ``unresolved`` — deliberately *not* falling through to (c), because the stem
       of ``…/attachments/{id}/thumbnails/320`` is the **size**.
    c. the entry's storage-key stem matches ``storage_stem`` — and only
       ``storage_stem``, never ``_key``. Document keys are short numeric strings, so
       a stem such as ``"320"`` or a year segment equals a live key routinely; a hit
       there would rewrite the reference onto a *different, existing* photo,
       irreversibly.
    """
    canonical = _matching_key(reference, tenant_key, index)
    if canonical is not None:
        return ReferenceVerdict("canonical", (canonical,))

    carried = normalize_photo_ref(reference)
    if carried != reference.strip():
        # An API URI, and nothing else — ``normalize_photo_ref`` leaves every other
        # spelling (storage key, s3 URL, ULID, unparseable legacy value) untouched.
        key = _matching_key(carried, tenant_key, index)
        return ReferenceVerdict("repaired", (key,)) if key else ReferenceVerdict("unresolved")

    matched: dict[str, AttachmentIdentity] = {}
    if stem:
        for attachment in index.get(stem, ()):
            if attachment.storage_stem == stem and _belongs_to(attachment, tenant_key):
                matched[attachment.key] = attachment

    keys = tuple(sorted(matched))
    if not keys:
        return ReferenceVerdict("unresolved")
    if len(keys) > 1:
        return ReferenceVerdict("ambiguous", keys)
    return ReferenceVerdict("repaired", keys)


class ReconcilePhotoRefsMigration(Migration):
    version = "0046"
    name = "reconcile_photo_refs"
    description = (
        "Rewrite a photo_refs entry onto the _key of the single attachment it denotes, "
        "and report every entry that resolves to nothing (#1438)."
    )
    reversible = False

    # ── reads (AQL-only, no-op-safe on an empty database) ─────────────────────

    def _attachments(self, db: StandardDatabase) -> list[AttachmentIdentity]:
        """Project every attachment onto ``(key, tenant, storage-key stem)``.

        The stem is computed **in the database**, by the same expression the orphan
        sweep compares against, so the migration never holds a second definition of
        what a storage key reduces to.
        """
        if not db.has_collection(col.ATTACHMENTS):
            return []
        query = (
            f"FOR a IN {col.ATTACHMENTS} "
            f"RETURN {{key: a._key, tenant_key: a.tenant_key, "
            f"stem: {aql_storage_key_stem('a.storage_key')}}}"
        )
        return [
            AttachmentIdentity(
                key=str(row["key"]),
                tenant_key=row.get("tenant_key"),
                storage_stem=row.get("stem") or None,
            )
            for row in db.aql.execute(query)
        ]

    def _stems(self, db: StandardDatabase, references: Sequence[str]) -> dict[str, str | None]:
        """Reduce each reference through the very same expression, batched."""
        query = f"FOR ref IN @refs RETURN {{ref: ref, stem: {aql_storage_key_stem('ref')}}}"
        stems: dict[str, str | None] = {}
        for start in range(0, len(references), _STEM_BATCH):
            batch = list(references[start : start + _STEM_BATCH])
            if not batch:
                continue
            for row in db.aql.execute(query, bind_vars={"refs": batch}):
                stems[str(row["ref"])] = row.get("stem") or None
        return stems

    @staticmethod
    def _carrier_query(collection: str, field: str) -> str:
        """The scan of one carrier: filtered **and** projected in the database.

        This runs under the migration lock in the startup path, so every document it
        pulls across is memory the migrating replica holds while the others wait on
        the barrier (:class:`~app.migrations.framework.report.MigrationBarrierTimeoutError`).
        ``FOR d IN <carrier> RETURN d`` handed the whole of ``tasks``,
        ``plant_instances`` and five more collections to Python to then discard the
        overwhelming majority — on an installation without photos, *all* of them.
        Filtered here, that installation costs zero rows; projected, a carrier with
        photos costs three fields per row instead of a whole document.

        The collection and the attribute name are interpolated because AQL binds
        collections and values, not attribute names. Both come from the pinned
        module-level tuples, never from a caller.
        """
        return (
            f"FOR d IN {collection} "
            f"FILTER d.{field} != null "
            f"RETURN {{_key: d._key, tenant_key: d.tenant_key, value: d.{field}}}"
        )

    @staticmethod
    def _references_of(value: Any) -> tuple[list[str], bool]:
        """Return the projected field's references and whether it is list-valued."""
        is_list = isinstance(value, list)
        raw = value if is_list else [value]
        return [item for item in raw if isinstance(item, str) and item], is_list

    # ── entry point ───────────────────────────────────────────────────────────

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        index = build_identity_index(self._attachments(db))

        scanned = 0
        changed = 0
        repaired = 0
        ambiguous: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []
        ambiguous_total = 0
        unresolved_total = 0
        per_collection: dict[str, dict[str, int]] = {}

        for collection, field in REFERENCE_FIELDS:
            # A carrier can legitimately be absent: ``ensure_collections`` runs before
            # the migration runner on a normal boot, but a partially bootstrapped or
            # restored database is exactly the state a repair migration meets, and an
            # AQL 1203 there would fail startup instead of reporting.
            if not db.has_collection(collection):
                continue

            carriers: list[tuple[Mapping[str, Any], list[str], bool]] = []
            distinct: set[str] = set()
            # Streamed, not ``list(...)``-ed: only the rows that actually carry a
            # reference are kept, and the filter above already dropped the rest.
            for row in db.aql.execute(self._carrier_query(collection, field)):
                references, is_list = self._references_of(row.get("value"))
                if not references:
                    continue
                carriers.append((row, references, is_list))
                distinct.update(references)
            if not carriers:
                continue

            stems = self._stems(db, sorted(distinct))
            stats = per_collection.setdefault(
                collection,
                {"scanned": 0, "changed": 0, "repaired": 0, "ambiguous": 0, "unresolved": 0},
            )

            for document, references, is_list in carriers:
                scanned += 1
                stats["scanned"] += 1
                tenant_key = document.get("tenant_key") or None
                rewritten: list[str] = []
                document_changed = False

                for reference in references:
                    verdict = plan_reference(reference, stems.get(reference), tenant_key, index)
                    if verdict.verdict == "repaired":
                        # Values are never dropped and never reordered — the entry is
                        # replaced in place, so a list whose other entries are already
                        # canonical keeps them exactly where the carrier wrote them.
                        rewritten.append(verdict.matches[0])
                        document_changed = True
                        repaired += 1
                        stats["repaired"] += 1
                        continue

                    rewritten.append(reference)
                    if verdict.verdict == "ambiguous":
                        ambiguous_total += 1
                        stats["ambiguous"] += 1
                        self._record(
                            ambiguous,
                            collection,
                            field,
                            document,
                            tenant_key,
                            reference,
                            matches=list(verdict.matches),
                        )
                    elif verdict.verdict == "unresolved":
                        unresolved_total += 1
                        stats["unresolved"] += 1
                        self._record(unresolved, collection, field, document, tenant_key, reference)

                if not document_changed:
                    continue
                changed += 1
                stats["changed"] += 1
                if dry_run:
                    continue

                # Interpolated for the same reason as the scan above.
                db.aql.execute(
                    f"UPDATE {{_key: @key, {field}: @value}} IN {collection}",
                    bind_vars={"key": document["_key"], "value": rewritten if is_list else rewritten[0]},
                )

        logger.info(
            "reconcile_photo_refs",
            scanned=scanned,
            changed=changed,
            repaired=repaired,
            ambiguous=ambiguous_total,
            unresolved=unresolved_total,
            dry_run=dry_run,
        )
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=scanned,
            changed=changed,
            dry_run=dry_run,
            details={
                "repaired": repaired,
                "ambiguous": ambiguous,
                "ambiguous_total": ambiguous_total,
                "unresolved": unresolved,
                "unresolved_total": unresolved_total,
                "per_collection": per_collection,
            },
        )

    @staticmethod
    def _record(
        sink: list[dict[str, Any]],
        collection: str,
        field: str,
        document: Mapping[str, Any],
        tenant_key: str | None,
        reference: str,
        *,
        matches: list[str] | None = None,
    ) -> None:
        """Append one report row, up to :data:`_REPORT_SAMPLE_LIMIT`."""
        if len(sink) >= _REPORT_SAMPLE_LIMIT:
            return
        row: dict[str, Any] = {
            "collection": collection,
            "document": document.get("_key"),
            "field": field,
            "tenant_key": tenant_key,
            "reference": reference,
        }
        if matches is not None:
            row["matches"] = matches
        sink.append(row)


migration = ReconcilePhotoRefsMigration()
