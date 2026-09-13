"""NFR-013 §2.2 — ArangoDB repository for the ``attachments`` collection."""

from datetime import UTC, date, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.enums import AttachmentCategory
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.attachment_repository import UNSET, IAttachmentRepository, _Unset
from app.domain.models.attachment import Attachment, QualityAssessment

# REQ-025 §3.1 — value written to ``created_by`` when a user is erased but the
# attachment must stay attached to the tenant record (Scope
# ``user_diary_attachments``). Must match the spec marker exactly (AK-OS-02).
ANONYMIZED_MARKER = "_anonymized"

#: Every collection whose documents can reference an attachment through
#: ``photo_refs``.
#:
#: The orphan sweep below deletes what nothing in this list references, so a
#: collection missing here means **deleting a referenced photo**. It is therefore
#: the full set, not just ``tasks``: the sweep only considers ``category == task``
#: attachments, and a task-category row *should* only ever be referenced by a task,
#: but "should" is not a property a destructive query may rest on. Checking all six
#: costs a daily subquery; being wrong costs a photo.
#:
#: ``test_photo_ref_carriers_match_the_models`` pins this against the models that
#: actually declare ``photo_refs``, so a seventh carrier fails the lane rather than
#: silently widening what the sweep may delete.
PHOTO_REF_COLLECTIONS: tuple[str, ...] = (
    col.TASKS,
    col.PLANT_INSTANCES,
    col.PLANT_DIARY_ENTRIES,
    col.HARVEST_OBSERVATIONS,
    col.INSPECTIONS,
    col.STORAGE_OBSERVATIONS,
)

#: Every other field anywhere that holds an attachment id, with the collection it
#: sits on. Scalar or list — the query normalises both.
#:
#: These do **not** carry ``photo_refs``, and none of them holds a ``task``-category
#: attachment today, so on paper the sweep could ignore them. That is the same "on
#: paper" the six-collection design above refuses to accept: the whole point is that
#: a destructive query does not rest on a category assumption holding. Checking them
#: costs one more pass in the collect phase and nothing per candidate.
#:
#: ``test_photo_ref_carriers.py`` pins this against the models, so a field added
#: here or there fails the lane rather than widening what may be deleted.
ATTACHMENT_REF_FIELDS: tuple[tuple[str, str], ...] = (
    (col.PLANT_INSTANCES, "cover_photo_ref"),
    (col.PEST_IMAGE_CONTRIBUTIONS, "attachment_id"),
    (col.PESTS, "reference_image_refs"),
)


def aql_photo_ref_candidates(expression: str) -> str:
    """AQL yielding **every** id one ``photo_refs`` entry might denote.

    A set, not a single answer, and that is the whole design. This feeds a query
    whose output gets **deleted**, so the cost of the two directions is not
    symmetric: protecting an id nothing turns out to reference leaves one photo
    uncollected until someone removes the stale reference, while failing to protect
    one destroys a photo a task still shows. The set is therefore deliberately a
    superset of what ``migrate_photo_refs.normalize_photo_ref`` resolves to.

    Trying to match that function exactly is what the previous two versions did, and
    both were wrong in a way that deleted photos:

    * the first took ``LAST(SPLIT(ref, "/"))`` and stopped, so a real storage key
      ``…/{ulid}.{ext}`` yielded ``{ulid}.{ext}`` and matched no document key;
    * the second stripped the extension and a ``_t{size}`` suffix, which fixed that
      and then produced the **empty string** for a reference with a trailing slash —
      unprotected again — while also disagreeing with ``normalize_photo_ref`` on an
      API URI carrying a thumbnail suffix.

    The candidates, all kept:

    1. the entry verbatim (it may already be an attachment id);
    2. the last **non-empty** path segment (tolerates a trailing slash);
    3. that with the extension dropped;
    4. that with a ``_t{size}`` thumbnail suffix dropped as well.

    **This is the fast path, not the safety net.** Enumerating spellings was tried
    four times and was wrong four times, each round finding one the list did not
    know — most recently ``/attachments/{ulid}/thumbnails/320``, which
    ``_photo_response`` builds and hands to clients itself, and which resolves here
    to ``"320"``. The set of spellings that have ever reached ``photo_refs`` is not
    closed: it depends on what every client version ever wrote.

    So the sweep does **not** rely on this. It also asks whether any reference string
    *contains* the attachment's key (:meth:`_aql_mentions_key`), which no spelling can
    escape, and this function only spares that pass for the overwhelming majority of
    rows. Getting a candidate wrong now costs a little work, not a photo.

    ``tests/integration/test_aql_reference_normalisation.py`` asserts that whatever
    ``normalize_photo_ref`` answers is always among these, and that the set never
    grows to something that would swallow an unrelated id.
    """
    # `` (FOR s IN SPLIT(x, "/") FILTER s != "" RETURN s) `` rather than ``LAST``:
    # ``LAST(SPLIT("a/b/", "/"))`` is the empty string, and an empty candidate
    # protects nothing.
    segments = f'(FOR segment IN SPLIT({expression}, "/") FILTER segment != "" RETURN segment)'
    tail = f"LAST({segments})"
    stem = f'FIRST(SPLIT({tail}, "."))'
    return f'[{expression}, {tail}, {stem}, REGEX_REPLACE({stem}, "_t[0-9]+$", "")]'


class ArangoAttachmentRepository(BaseArangoRepository[Attachment], IAttachmentRepository):
    """ArangoDB-backed repository for ``attachments``."""

    _model_cls = Attachment

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.ATTACHMENTS)

    def get(self, key: str, tenant_key: str) -> Attachment | None:
        attachment = super().get_by_key(key)
        if attachment is None or attachment.tenant_key != tenant_key:
            return None
        return attachment

    def delete(self, key: str, tenant_key: str) -> bool:
        existing = self.get(key, tenant_key)
        if existing is None:
            return False
        return super().delete(key)

    def update_metadata(
        self,
        key: str,
        tenant_key: str,
        *,
        caption: str | None | _Unset = UNSET,
        taken_on: date | None | _Unset = UNSET,
    ) -> Attachment | None:
        """REQ-034 §2.1 v1.2 — patch ``caption`` / ``taken_on`` (tenant-scoped, AQL).

        True PATCH: only the explicitly-passed fields are written. The patch doc
        is assembled in Python and bound as a single ``@patch`` object so the AQL
        stays fully parametrized (no f-string interpolation) and an explicit
        ``None`` is preserved (it would otherwise be impossible to *clear* a
        field with ArangoDB's default ``mergeObjects``/``keepNull`` semantics).
        """
        patch: dict[str, Any] = {}
        if not isinstance(caption, _Unset):
            patch["caption"] = caption
        if not isinstance(taken_on, _Unset):
            # AQL has no native date type — store the ISO date string, matching
            # how Pydantic serialises ``date`` everywhere else in the catalog.
            patch["taken_on"] = taken_on.isoformat() if isinstance(taken_on, date) else None
        if not patch:
            # Nothing to change — return the current document (tenant-scoped).
            return self.get(key, tenant_key)

        patch["updated_at"] = datetime.now(UTC).isoformat()
        query = """
        FOR att IN @@collection
          FILTER att._key == @key AND att.tenant_key == @tenant_key
          UPDATE att WITH @patch IN @@collection
            OPTIONS { keepNull: true }
          RETURN NEW
        """
        bind_vars = {
            "@collection": self._collection_name,
            "key": key,
            "tenant_key": tenant_key,
            "patch": patch,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        doc = next(cursor, None)
        if doc is None:
            return None
        return Attachment(**self._from_doc(doc))

    def update_quality_assessment(
        self,
        key: str,
        tenant_key: str,
        assessment: QualityAssessment,
    ) -> Attachment | None:
        """REQ-034 §4a.2 — persist (overwrite) a photo's quality assessment (AQL).

        The verdict is serialised to a JSON-safe dict (``mode="json"`` so the
        nested ``assessed_at`` datetime becomes an ISO string) and bound as a
        single ``@assessment`` object — the AQL stays fully parametrized.
        """
        patch: dict[str, Any] = {
            "quality_assessment": assessment.model_dump(mode="json"),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        query = """
        FOR att IN @@collection
          FILTER att._key == @key AND att.tenant_key == @tenant_key
          UPDATE att WITH @patch IN @@collection
            OPTIONS { keepNull: true }
          RETURN NEW
        """
        bind_vars = {
            "@collection": self._collection_name,
            "key": key,
            "tenant_key": tenant_key,
            "patch": patch,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        doc = next(cursor, None)
        if doc is None:
            return None
        return Attachment(**self._from_doc(doc))

    def find_by_user(
        self,
        tenant_key: str,
        user_key: str,
        categories: list[AttachmentCategory] | None = None,
    ) -> list[Attachment]:
        category_values = [c.value for c in categories] if categories else None
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key AND att.created_by == @user_key
          FILTER @categories == null OR att.category IN @categories
          SORT att.created_at DESC
          RETURN att
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "user_key": user_key,
            "categories": category_values,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Attachment(**self._from_doc(doc)) for doc in cursor]

    def anonymize_user_metadata(
        self,
        tenant_key: str,
        user_key: str,
        categories: list[AttachmentCategory] | None = None,
    ) -> int:
        """REQ-025 Phase 0 — set ``created_by = '_anonymized'`` (tenant-scoped, AQL).

        Only touches documents that still carry the user's ``created_by`` (so a
        re-run after a partial failure is idempotent and stays a no-op once
        everything is anonymised). Returns the number of documents updated.
        """
        category_values = [c.value for c in categories] if categories else None
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key AND att.created_by == @user_key
          FILTER @categories == null OR att.category IN @categories
          UPDATE att WITH { created_by: @marker } IN @@collection
          COLLECT WITH COUNT INTO updated
          RETURN updated
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "user_key": user_key,
            "categories": category_values,
            "marker": ANONYMIZED_MARKER,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

    def delete_all_for_tenant(self, tenant_key: str) -> int:
        """REQ-024/-025 — delete every attachment metadata document of a tenant."""
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key
          REMOVE att IN @@collection
          COLLECT WITH COUNT INTO removed
          RETURN removed
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

    def find_by_sha256(self, tenant_key: str, sha256: str) -> Attachment | None:
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key AND att.sha256 == @sha256
          LIMIT 1
          RETURN att
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "sha256": sha256,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        doc = next(cursor, None)
        if doc is None:
            return None
        return Attachment(**self._from_doc(doc))

    def count_by_tenant(self, tenant_key: str) -> int:
        query = """
        RETURN LENGTH(
          FOR att IN @@collection
            FILTER att.tenant_key == @tenant_key
            RETURN 1
        )
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return next(cursor, 0)

    def sum_bytes_by_tenant(self, tenant_key: str) -> int:
        query = """
        RETURN SUM(
          FOR att IN @@collection
            FILTER att.tenant_key == @tenant_key
            RETURN att.byte_size
        )
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return int(next(cursor, 0) or 0)

    def list_by_tenant(
        self,
        tenant_key: str,
        category: AttachmentCategory | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Attachment], int]:
        category_value = category.value if category else None
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key
          FILTER @category == null OR att.category == @category
          SORT att.created_at DESC
          LIMIT @offset, @limit
          RETURN att
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "category": category_value,
            "offset": offset,
            "limit": limit,
        }
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        items = [Attachment(**self._from_doc(doc)) for doc in cursor]

        count_query = """
        RETURN LENGTH(
          FOR att IN @@collection
            FILTER att.tenant_key == @tenant_key
            FILTER @category == null OR att.category == @category
            RETURN 1
        )
        """
        count_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "category": category_value,
        }
        count_cursor = self._db.aql.execute(count_query, bind_vars=count_vars)
        total = int(next(count_cursor, 0) or 0)
        return items, total

    def _aql_referenced_prelude(self, *, ignore_task_key: bool = False) -> str:
        """AQL that binds ``referenced`` to every id anything in the tenant links.

        Shared by the orphan sweep and :meth:`unreferenced_among`, because the two
        must agree about what "referenced" means. They did not when the eager
        deletion was written: ``TaskService.delete_task`` forwarded every id in the
        task's ``photo_refs`` verbatim, and ``AttachmentService.upload``
        **deduplicates by sha256 across the whole tenant and across categories** — so
        a photo whose bytes were also uploaded to another task, or to a plant
        gallery, was destroyed with the task and left a dangling reference behind.

        ``photo_refs`` entries may be ids, API URIs or storage keys (``migrate_photo_refs``
        exists for that, and is manual), so every candidate spelling is resolved
        through :func:`aql_photo_ref_candidates`.
        """
        # ``@ignored_task_key`` discounts one task's own references, for the route
        # that deletes a photo *from* that task. Applied to the tasks collection
        # only; every other carrier still protects the photo.
        skip = " FILTER d._key != @ignored_task_key" if ignore_task_key else ""
        parts = [
            f"          (FOR d IN @@ref_col_{index}"
            f"{skip if PHOTO_REF_COLLECTIONS[index] == col.TASKS else ''}"
            f" RETURN d.photo_refs || [])"
            for index in range(len(PHOTO_REF_COLLECTIONS))
        ]
        # ``IS_ARRAY`` so one expression serves both a list field and a scalar one.
        # The field name is interpolated rather than bound because AQL binds
        # collections (``@@``) and values (``@``), not attribute names; every name
        # comes from the module-level tuple above, never from a caller.
        parts += [
            f"          (FOR d IN @@extra_col_{index} "
            f"RETURN IS_ARRAY(d.{field}) ? d.{field} : (d.{field} == null ? [] : [d.{field}]))"
            for index, (_collection, field) in enumerate(ATTACHMENT_REF_FIELDS)
        ]
        collected = ",\n".join(parts)
        return f"""        LET raw_refs = UNIQUE(FLATTEN([
{collected}
        ], 2))
        LET referenced = UNIQUE(FLATTEN([
          raw_refs,
          (FOR ref IN raw_refs RETURN {aql_photo_ref_candidates("ref")})
        ], 2))"""

    @staticmethod
    def _aql_mentions_key(refs_expression: str, key_expression: str) -> str:
        """AQL: does any reference string mention this attachment key at all?

        The safety net under :func:`aql_photo_ref_candidates`, and the reason the
        sweep stopped being one spelling away from destroying a photo.

        Four review rounds each found a reference shape the candidate list did not
        know — a storage key with an extension, a trailing slash, a query string, a
        ``/thumbnails/{size}`` path the product builds itself. Every fix enumerated
        one more shape, and the next round found another, because the set of things
        that have ever been written into ``photo_refs`` is open: it spans every
        client version and an unrun manual migration.

        A substring test closes the class instead of its fourth instance. Any
        reference that mentions the key — however it is spelled, wrapped or
        suffixed — protects the photo. A ULID is 26 characters from Crockford's
        alphabet, so an incidental match is not a practical concern, and the
        direction of the residual error is the safe one: an attachment is kept, not
        destroyed.

        Runs only for rows the fast path did not already clear, which are the
        orphans — a handful per night — so the cost is a string scan over an
        in-memory array rather than anything touching a collection.
        """
        return f"LENGTH(FOR ref IN {refs_expression} FILTER CONTAINS(ref, {key_expression}) LIMIT 1 RETURN 1) == 0"

    def _reference_bind_vars(self) -> dict[str, Any]:
        """The collection bindings :meth:`_aql_referenced_prelude` needs."""
        bind_vars: dict[str, Any] = {}
        for index, collection in enumerate(PHOTO_REF_COLLECTIONS):
            bind_vars[f"@ref_col_{index}"] = collection
        for index, (collection, _field) in enumerate(ATTACHMENT_REF_FIELDS):
            bind_vars[f"@extra_col_{index}"] = collection
        return bind_vars

    def by_keys(self, attachment_ids: list[str], tenant_key: str) -> list[Attachment]:
        """The tenant's attachments among *attachment_ids*, skipping what does not exist.

        Lets a caller tell "this id is shared with another carrier" apart from "this
        id resolves to nothing at all" — an un-migrated installation's ``photo_refs``
        holds URIs and storage keys, and reporting those as *shared* sends whoever
        reads the audit line hunting a problem that is not there.
        """
        if not attachment_ids:
            return []
        query = """
        FOR att IN @@collection
          FILTER att._key IN @keys AND att.tenant_key == @tenant_key
          RETURN att
        """
        cursor = self._db.aql.execute(
            query,
            bind_vars={
                "@collection": self._collection_name,
                "keys": list(attachment_ids),
                "tenant_key": tenant_key,
            },
        )
        return [Attachment(**self._from_doc(doc)) for doc in cursor]

    def unreferenced_among(
        self, attachment_ids: list[str], tenant_key: str, *, ignoring_task_key: str | None = None
    ) -> list[str]:
        """Which of *attachment_ids* nothing in the tenant links any more (#1393).

        Asked before the eager deletion that follows a task deletion. Deleting a
        task's ``photo_refs`` outright destroys a photo that sha256 deduplication
        gave to a second task or a plant gallery as well — the reference survives,
        the bytes do not.

        ``ignoring_task_key`` discounts one task's own references, which is what the
        task-photo DELETE route needs: a photo *this* task links may be deleted
        through it, one another carrier links may not. Without it that route asked a
        tasks-only, exact-match question and so missed both a plant gallery holding
        the same deduplicated object and any legacy spelling of the reference.

        Returns the ids safe to delete. Anything still linked is left to whoever owns
        that link, and the nightly sweep picks it up if that link goes away later.
        """
        if not attachment_ids:
            return []
        query = f"""
{self._aql_referenced_prelude(ignore_task_key=ignoring_task_key is not None)}
        FOR att IN @@collection
          FILTER att._key IN @candidates
            AND att.tenant_key == @tenant_key
            AND att._key NOT IN referenced
            AND {self._aql_mentions_key("raw_refs", "att._key")}
          RETURN att._key
        """
        bind_vars: dict[str, Any] = {
            "@collection": self._collection_name,
            "candidates": list(attachment_ids),
            "tenant_key": tenant_key,
            **self._reference_bind_vars(),
        }
        if ignoring_task_key is not None:
            bind_vars["ignored_task_key"] = ignoring_task_key
        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return list(cursor)

    def find_orphaned_task_photos(self, *, older_than: datetime, limit: int = 500) -> list[Attachment]:
        """Task-category attachments older than *older_than* that nothing references.

        The three ways a task photo is orphaned (#1393), all of which this covers:
        an upload whose form was never submitted, a photo removed from the staging
        area before submitting, and a photo whose task was deleted.

        **The age floor is what makes this safe.** An upload is written to the
        attachment catalogue before the form that will reference it is submitted, so
        every photo is briefly an orphan by design. Sweeping without a floor would
        delete the photo a user is still filling in the form around; the floor is a
        wide margin over the longest plausible form-filling session, and it is
        configurable.

        **Reference-checked against every carrier, not just tasks** — see
        :data:`PHOTO_REF_COLLECTIONS` for why a destructive query does not rest on
        "a task-category row should only be referenced by a task".

        Installation-wide on purpose: the sweep is housekeeping, not a tenant
        operation, and it returns rows of every tenant. The caller deletes them
        through ``AttachmentService``, which is tenant-scoped and therefore gets the
        row's own ``tenant_key`` back from here.
        """
        # One pass over each carrier, not one per candidate attachment.
        #
        # The first version asked, for every candidate, ``att._key IN d.photo_refs``
        # inside six subqueries. Nothing indexes ``photo_refs``, so each of those
        # scanned its collection to completion — and for an orphan, the case with no
        # match anywhere, all six ran in full. That is O(candidates x documents), and
        # the outer ``LIMIT`` could not prune it because the reference filter runs
        # first: a few thousand task photos against tens of thousands of tasks and
        # plant instances is hundreds of millions of document reads a night.
        #
        # Collecting the referenced ids once makes it O(N + M).
        query = f"""
{self._aql_referenced_prelude()}
        FOR att IN @@collection
          FILTER att.category == @category
            AND att.created_at != null
            AND att.created_at < @cutoff
            AND att._key NOT IN referenced
            AND {self._aql_mentions_key("raw_refs", "att._key")}
          SORT att.created_at ASC
          LIMIT @limit
          RETURN att
        """
        bind_vars: dict[str, Any] = {
            "@collection": self._collection_name,
            "category": AttachmentCategory.TASK.value,
            "cutoff": older_than.isoformat(),
            "limit": int(limit),
        }
        bind_vars.update(self._reference_bind_vars())

        cursor = self._db.aql.execute(query, bind_vars=bind_vars)
        return [Attachment(**self._from_doc(doc)) for doc in cursor]
