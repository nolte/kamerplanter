"""v0062 — give every pest-image contributor their own attachment record (#1770).

Until #1770 ``AttachmentService.upload`` handed a second upload of the same
bytes the *first* uploader's catalog record. A pest-image contribution whose
bytes someone in the tenant had uploaded before therefore points at a record
that is not the contributor's: ``created_by`` names another member, or the
category is a documentation one (``diary``, ``ipm`` …). Erasure selects records
by ``created_by`` and ``category``, so

* erasing the record's owner applied *their* storage rule to the contributor's
  image — a ``pest_reference`` record is hard-deleted, bytes and all, which
  took the second contributor's image (and any diary entry sharing it) along;
* erasing the contributor found nothing attributed to them, and withdrawing
  the contribution (``PestImageService.delete``) deleted another member's
  record and bytes.

Upload now gives every uploader a record of their own over one stored object,
and bytes go only with the last record that holds them. This migration brings
existing data to that shape, as far as existing data says who holds what.

**What it changes, in order:**

1. **The ``storage_key`` index becomes non-unique.** Records of several
   uploaders share one object, so the unique index ``ensure_collections``
   created before #1770 would refuse them. ``ensure_collections`` now creates a
   non-unique one; this drops the unique one an existing volume still carries.
2. **Contributions get their own record.** Every ``pest_image_contributions``
   document names its contributor, which is what makes this half
   reconstructible. A contribution keeps the record it points at only if that
   record is the contributor's own ``pest_reference`` record and no earlier
   contribution kept it already; any other gets a new record — the
   contributor's, category ``pest_reference``, over the same object — under the
   deterministic key ``pic-<contribution key>``, and is repointed to it. The
   other uploader's filename is not copied into it.
3. **A ``pest_reference`` record a documentation carrier references becomes a
   documentation record.** A diary entry, task, inspection, harvest or storage
   observation, or plant gallery (``photo_refs`` / ``cover_photo_ref``) that
   points at a ``pest_reference`` record would lose its photo when the record's
   owner is erased (that category is hard-deleted). Such a record takes the
   category of the first carrier found, so it is anonymised and kept like every
   documentation photo; every contribution that pointed at it gets its own
   record by step 2.

**What it cannot reconstruct.** Two *documentation* uploads of the same bytes
by two members left one record and no trace of the second uploader: the
carriers hold record keys, and most carry no per-photo owner. Those records
stay as they are — their bytes are never hard-deleted (the documentation
rule anonymises and keeps), so nothing is lost; the second uploader's Art. 15
export simply does not list a record they never had. Where uploads keep their
EXIF (``STORAGE_STRIP_EXIF=false``), the second uploader's erasure does not strip
such a shared photo either — the first uploader's erasure does.

**Idempotent (M-3).** The split key is deterministic and written with an
``UPSERT``; a contribution already pointing at its own ``pest_reference``
record is left alone; recategorising is a plain overwrite. A run interrupted
between writing a split record and repointing its contribution finishes both
on the next run.

**Dry run (M-5).** Computes every change and writes nothing — the index is
reported, not dropped.

**Not reversible (M-6).** Merging split records back would re-create exactly
the shared ownership this removes.

**Lock.** Runs under the framework's advisory lock like every migration, before
the backend serves; the writes are per document, so a crash leaves a state the
next run completes.
"""

from __future__ import annotations

from typing import Any

import structlog
from arango.database import StandardDatabase

from app.data_access.arango import collections as col
from app.data_access.arango.attachment_repository import (
    TENANT_SCOPED_REF_COLLECTIONS,
    aql_photo_ref_candidates,
    aql_storage_key_stem,
)
from app.migrations.framework.base import Migration
from app.migrations.framework.report import MigrationReport

logger = structlog.get_logger(__name__)

_PEST_REFERENCE = "pest_reference"
_INDEX_FIELDS = ["storage_key"]

#: The documentation category a ``pest_reference`` record takes when a carrier
#: of this collection references it. Every ``photo_refs`` carrier is named
#: (``test_v0062…`` pins this against ``PHOTO_REF_COLLECTIONS``); the plant
#: gallery's ``cover_photo_ref`` maps to the gallery category as well.
CARRIER_CATEGORY: dict[str, str] = {
    col.TASKS: "task",
    col.PLANT_INSTANCES: "plant",
    col.PLANT_DIARY_ENTRIES: "diary",
    col.HARVEST_OBSERVATIONS: "harvest",
    col.INSPECTIONS: "ipm",
    col.STORAGE_OBSERVATIONS: "post_harvest",
}


def split_key(contribution_key: str) -> str:
    """The deterministic key of a contribution's own record."""
    return f"pic-{contribution_key}"


class SplitSharedAttachmentOwnershipMigration(Migration):
    version = "0062"
    name = "split_shared_attachment_ownership"
    description = (
        "Drop the unique storage_key index and give every pest-image contributor their own "
        "attachment record over shared deduplicated bytes (#1770)."
    )
    reversible = False

    _CONTRIBUTIONS_QUERY = """
    FOR c IN @@contributions
      SORT c.created_at ASC, c._key ASC
      RETURN {
        key: c._key, tenant_key: c.tenant_key, attachment_id: c.attachment_id,
        contributed_by: c.contributed_by, created_at: c.created_at
      }
    """

    _ATTACHMENTS_QUERY = """
    FOR key IN @keys
      LET att = DOCUMENT(@@attachments, key)
      FILTER att != null
      RETURN att
    """

    _UPSERT_QUERY = """
    UPSERT { _key: @doc._key }
    INSERT @doc
    UPDATE {}
    IN @@attachments
    """

    def _storage_key_indexes(self, attachments: Any) -> list[dict[str, Any]]:
        return [
            idx
            for idx in attachments.indexes()
            if isinstance(idx, dict) and idx.get("type") == "persistent" and idx.get("fields") == _INDEX_FIELDS
        ]

    def _documentation_category(self, db: StandardDatabase, attachment: dict[str, Any]) -> str | None:
        """The category of the first documentation carrier referencing *attachment*, if any.

        Matched as the orphan sweep matches (``aql_photo_ref_candidates`` against
        the record key and the storage-key stem). A carrier that carries a tenant
        counts only in the record's tenant (or unstamped, as the interactive
        delete route reads it): recategorising turns a hard-delete into
        anonymise-and-keep, so a stray reference from another tenant must not
        decide it. Carriers without a ``tenant_key`` (harvest and storage
        observations) count wherever they are.
        """
        stem = aql_storage_key_stem("@storage_key")
        for collection, category in CARRIER_CATEGORY.items():
            if not db.has_collection(collection):
                continue
            tenant_filter = (
                'FILTER d.tenant_key == @tenant_key OR d.tenant_key == null OR d.tenant_key == ""'
                if collection in TENANT_SCOPED_REF_COLLECTIONS
                else ""
            )
            query = f"""
            FOR d IN @@carrier
              {tenant_filter}
              LET refs = APPEND(d.photo_refs || [], d.cover_photo_ref == null ? [] : [d.cover_photo_ref])
              FILTER LENGTH(refs) > 0
              FILTER LENGTH(
                FOR ref IN refs
                  LET candidates = {aql_photo_ref_candidates("ref")}
                  FILTER @key IN candidates OR (@storage_key != null AND {stem} IN candidates)
                  LIMIT 1
                  RETURN 1
              ) > 0
              LIMIT 1
              RETURN 1
            """
            bind_vars = {
                "@carrier": collection,
                "key": attachment["_key"],
                "storage_key": attachment.get("storage_key"),
            }
            if tenant_filter:
                bind_vars["tenant_key"] = attachment.get("tenant_key")
            if next(iter(db.aql.execute(query, bind_vars=bind_vars)), None) is not None:
                return category
        return None

    def _plan(self, db: StandardDatabase) -> dict[str, Any]:
        contributions = list(
            db.aql.execute(self._CONTRIBUTIONS_QUERY, bind_vars={"@contributions": col.PEST_IMAGE_CONTRIBUTIONS})
        )
        keys = sorted({c["attachment_id"] for c in contributions if c.get("attachment_id")})
        attachments = {
            doc["_key"]: doc
            for doc in db.aql.execute(
                self._ATTACHMENTS_QUERY, bind_vars={"@attachments": col.ATTACHMENTS, "keys": keys}
            )
        }
        recategorise: dict[str, str] = {}
        for key, doc in attachments.items():
            # A split record is the contributor's by construction. It shares its
            # storage key — and so its stem — with the record it was split from,
            # so a carrier reference by storage key would otherwise match it too.
            if doc.get("category") == _PEST_REFERENCE and not key.startswith(split_key("")):
                category = self._documentation_category(db, doc)
                if category is not None:
                    recategorise[key] = category

        claimed: set[str] = set()
        splits: list[tuple[dict[str, Any], dict[str, Any]]] = []
        unresolved = 0
        for contribution in contributions:
            attachment = attachments.get(contribution.get("attachment_id") or "")
            if attachment is None or attachment.get("tenant_key") != contribution.get("tenant_key"):
                unresolved += 1
                continue
            key = attachment["_key"]
            own = (
                attachment.get("created_by") == contribution.get("contributed_by")
                and attachment.get("category") == _PEST_REFERENCE
                and key not in recategorise
                and key not in claimed
            )
            if own:
                claimed.add(key)
                continue
            splits.append((contribution, attachment))
        return {
            "contributions": len(contributions),
            "unresolved": unresolved,
            "recategorise": recategorise,
            "splits": splits,
        }

    @staticmethod
    def _split_document(contribution: dict[str, Any], attachment: dict[str, Any]) -> dict[str, Any]:
        same_owner = attachment.get("created_by") == contribution.get("contributed_by")
        return {
            "_key": split_key(contribution["key"]),
            "tenant_key": attachment["tenant_key"],
            "mime_type": attachment.get("mime_type"),
            "byte_size": attachment.get("byte_size"),
            "sha256": attachment.get("sha256"),
            # Another member's filename is theirs, not the contributor's.
            "original_filename": attachment.get("original_filename", "") if same_owner else "",
            "created_by": contribution["contributed_by"],
            "category": _PEST_REFERENCE,
            "storage_key": attachment.get("storage_key"),
            # Like the filename, the other member's device hint is theirs.
            "capture_device": attachment.get("capture_device", "unknown") if same_owner else "unknown",
            "created_at": contribution.get("created_at") or attachment.get("created_at"),
        }

    def up(self, db: StandardDatabase, *, dry_run: bool = False) -> MigrationReport:
        if not db.has_collection(col.ATTACHMENTS):
            return MigrationReport(version=self.version, name=self.name, dry_run=dry_run, details={"skipped": True})
        attachments = db.collection(col.ATTACHMENTS)
        unique_indexes = [idx for idx in self._storage_key_indexes(attachments) if idx.get("unique")]
        has_plain_index = any(not idx.get("unique") for idx in self._storage_key_indexes(attachments))

        plan: dict[str, Any] = {"contributions": 0, "unresolved": 0, "recategorise": {}, "splits": []}
        if db.has_collection(col.PEST_IMAGE_CONTRIBUTIONS):
            plan = self._plan(db)

        details = {
            "unique_storage_key_indexes_dropped": len(unique_indexes),
            "contributions_scanned": plan["contributions"],
            "contributions_unresolved": plan["unresolved"],
            "records_recategorised": len(plan["recategorise"]),
            "records_split": len(plan["splits"]),
        }
        if dry_run:
            logger.info("split_shared_attachment_ownership_dry_run", **details)
            return MigrationReport(
                version=self.version,
                name=self.name,
                scanned=plan["contributions"],
                changed=0,
                dry_run=True,
                details=details,
            )

        # 1. Index first: the split records share a storage key.
        if not has_plain_index:
            attachments.add_persistent_index(fields=_INDEX_FIELDS, unique=False)
        for idx in unique_indexes:
            attachments.delete_index(idx["id"], ignore_missing=True)

        # 3. A recategorised record is never kept by a contribution — ``_plan``
        #    split them all — so the order of 2 and 3 does not matter.
        for key, category in plan["recategorise"].items():
            db.aql.execute(
                "UPDATE { _key: @key, category: @category } IN @@attachments",
                bind_vars={"key": key, "category": category, "@attachments": col.ATTACHMENTS},
            )

        # 2. Record first, then the pointer: a crash in between leaves a record the
        #    re-run finds by its key and a contribution it repoints.
        for contribution, attachment in plan["splits"]:
            document = self._split_document(contribution, attachment)
            db.aql.execute(self._UPSERT_QUERY, bind_vars={"doc": document, "@attachments": col.ATTACHMENTS})
            db.aql.execute(
                "UPDATE { _key: @key, attachment_id: @attachment_id } IN @@contributions",
                bind_vars={
                    "key": contribution["key"],
                    "attachment_id": document["_key"],
                    "@contributions": col.PEST_IMAGE_CONTRIBUTIONS,
                },
            )

        changed = len(unique_indexes) + len(plan["recategorise"]) + len(plan["splits"])
        logger.info("split_shared_attachment_ownership_applied", **details)
        return MigrationReport(
            version=self.version,
            name=self.name,
            scanned=plan["contributions"],
            changed=changed,
            dry_run=False,
            details=details,
        )


migration = SplitSharedAttachmentOwnershipMigration()
