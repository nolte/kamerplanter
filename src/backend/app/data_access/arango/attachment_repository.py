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

#: Which of the collections above are tenant-scoped, and may therefore have their
#: reference scan narrowed to one tenant.
#:
#: The narrowing exists because :meth:`task_photo_delete_state` runs **synchronously
#: inside the interactive photo-delete handler**, and the unfiltered prelude reads
#: every ``photo_refs`` array in nine collections installation-wide to answer a
#: question about one id. Restricting the scan to the caller's tenant is
#: sound because an attachment belongs to exactly one tenant (REQ-024): a document
#: of another tenant referencing it would itself be the defect, not a reference
#: worth honouring.
#:
#: **Membership here is load-bearing in the destructive direction, which is why it
#: is pinned.** ArangoDB is schemaless: ``FILTER d.tenant_key == @ref_tenant_key`` over
#: a collection whose documents have no such field compares ``null`` and matches
#: nothing, so naming a collection here that does not carry the field would make it
#: protect *no* photo at all — silently, and only for rows it alone protects.
#: ``test_tenant_scoped_ref_collections_match_the_models`` reads the field off the
#: models, so that mistake fails the lane instead of deleting a photo.
#:
#: ``harvest_observations``, ``storage_observations`` and ``pests`` are absent
#: because they genuinely have no ``tenant_key`` — they stay unfiltered and keep
#: protecting across the whole installation, which is the safe direction.
TENANT_SCOPED_REF_COLLECTIONS: frozenset[str] = frozenset(
    {
        col.TASKS,
        col.PLANT_INSTANCES,
        col.PLANT_DIARY_ENTRIES,
        col.INSPECTIONS,
        col.PEST_IMAGE_CONTRIBUTIONS,
    }
)


def aql_storage_key_stem(expression: str) -> str:
    """AQL yielding the **object id** a storage key ends in — the second identity.

    ``StorageKeyBuilder.build`` emits ``t/{tenant}/{cat}/{yyyy}/{mm}/{ulid}.{ext}``
    and mints that ULID itself, so it is unrelated to the attachment's numeric
    ``_key`` (NFR-013 §2.2, "two identities"). Comparing a ``photo_refs`` entry
    against an attachment's *own* ``storage_key`` is therefore the only way to
    connect the two, and this expression is the reduction both sides of that
    comparison run through: the last path segment, without its extension.

    **One definition, two consumers, on purpose.** The orphan sweep
    (:meth:`ArangoAttachmentRepository._aql_unreferenced`) asks with it whether an
    attachment is still referenced, and ``v0046_reconcile_photo_refs`` asks with it
    which attachment a reference denotes, applying it to the *reference* as well as
    to the attachment. Those two answering differently is exactly the root cause
    #1438 records — a sweep that deletes what the repair still points at — so the
    string is built here and transcribed nowhere.

    Deliberately narrow: no thumbnail-suffix stripping, no query-string handling.
    The wide, tolerant superset is :func:`aql_photo_ref_candidates`, whose output is
    only ever used to *protect* a row. An id that is merely plausible must not
    decide what a reference gets rewritten to — the candidate ``"320"`` derived from
    ``/attachments/{id}/thumbnails/320`` would equal a real numeric ``_key``.
    """
    return f'FIRST(SPLIT(LAST(SPLIT({expression}, "/")), "."))'


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
    resolves to the attachment's key or its storage-key stem
    (:meth:`ArangoAttachmentRepository._aql_unreferenced`), which every known spelling can
    escape, and this function only spares that pass for the overwhelming majority of
    rows. Getting a candidate wrong now costs a little work, not a photo.

    ``tests/integration/test_aql_reference_normalisation.py`` asserts that whatever
    ``normalize_photo_ref`` answers is always among these, and that the set never
    grows to something that would swallow an unrelated id.
    """
    # **Every** segment, not only the last. ``LAST`` was wrong for the one shape the
    # product builds itself: ``/attachments/{id}/thumbnails/320`` ends in the *size*,
    # so the identifier sat in the middle. That was patched by adding a substring
    # test alongside — see :meth:`ArangoAttachmentRepository._aql_unreferenced`, and
    # round 7 for why a substring test is not usable here at all.
    #
    # The query string is stripped first: ``…/{id}?download=1`` otherwise yields the
    # segment ``{id}?download=1``, which equals no key.
    base = f'FIRST(SPLIT({expression}, "?"))'
    segments = f'(FOR segment IN SPLIT({base}, "/") FILTER segment != "" RETURN segment)'
    # Each segment, its extension-stripped stem, and that stem without a ``_t{size}``
    # thumbnail suffix. ``FLATTEN`` because the comprehension yields one triple per
    # segment. The whole reference is included for the bare-id case, where there is
    # nothing to split.
    expanded = (
        f"(FOR segment IN {segments} "
        f'LET stem = FIRST(SPLIT(segment, ".")) '
        f'RETURN [segment, stem, REGEX_REPLACE(stem, "_t[0-9]+$", "")])'
    )
    return f"UNIQUE(FLATTEN([[{expression}], FLATTEN({expanded}, 1)], 1))"


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
          SORT DATE_TIMESTAMP(att.created_at) DESC
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

    def find_own_by_sha256(
        self, *, tenant_key: str, sha256: str, created_by: str, category: AttachmentCategory
    ) -> Attachment | None:
        query = """
        FOR att IN @@collection
          FILTER att.tenant_key == @tenant_key AND att.sha256 == @sha256
          FILTER att.created_by == @created_by AND att.category == @category
          SORT DATE_TIMESTAMP(att.created_at) ASC
          LIMIT 1
          RETURN att
        """
        bind_vars = {
            "@collection": self._collection_name,
            "tenant_key": tenant_key,
            "sha256": sha256,
            "created_by": created_by,
            "category": category.value,
        }
        doc = next(self._db.aql.execute(query, bind_vars=bind_vars), None)
        if doc is None:
            return None
        return Attachment(**self._from_doc(doc))

    def storage_keys_held_elsewhere(
        self, *, tenant_key: str, storage_keys: list[str], excluding: list[str]
    ) -> set[str]:
        if not storage_keys:
            return set()
        # Tenant-filtered on purpose, and the safe direction all the same: a
        # storage key embeds its tenant (``t/{tenant}/…``), so a record of another
        # tenant cannot hold it, and a legacy record without ``tenant_key`` is not
        # one this tenant's deletion may count on.
        query = """
        FOR att IN @@collection
          FILTER att.storage_key IN @storage_keys
          FILTER att.tenant_key == @tenant_key
          FILTER att._key NOT IN @excluding
          COLLECT storage_key = att.storage_key
          RETURN storage_key
        """
        bind_vars = {
            "@collection": self._collection_name,
            "storage_keys": list(storage_keys),
            "tenant_key": tenant_key,
            "excluding": list(excluding),
        }
        return set(self._db.aql.execute(query, bind_vars=bind_vars))

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
            // One object, one charge: records that share deduplicated bytes
            // (#1770) point at the same storage key.
            COLLECT storage_key = att.storage_key AGGREGATE size = MAX(att.byte_size)
            RETURN size
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
          SORT DATE_TIMESTAMP(att.created_at) DESC
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

    def _aql_referenced_prelude(self, *, ignore_task_key: bool = False, tenant_scoped: bool = False) -> str:
        """AQL that binds ``referenced`` to every id anything in the tenant links.

        Shared by the orphan sweep and :meth:`unreferenced_among`, because the two
        must agree about what "referenced" means. They did not when the eager
        deletion was written: ``TaskService.delete_task`` forwarded every id in the
        task's ``photo_refs`` verbatim, and ``AttachmentService.upload``
        **deduplicates by sha256 across the whole tenant and across categories** — so
        a photo whose bytes were also uploaded to another task, or to a plant
        gallery, was destroyed with the task and left a dangling reference behind.

        ``photo_refs`` entries may be ids, API URIs or storage keys, so every candidate
        spelling is resolved through :func:`aql_photo_ref_candidates`. Note that
        ``migrate_photo_refs`` does **not** collapse those spellings into one:
        ``v0003`` runs it on every installation at startup, but since #1438 it only
        rewrites the ``/attachments/{id}`` URI shape and leaves a storage key
        verbatim — because the storage key's ULID is not a document key, so mapping
        it needs this very catalogue. A storage-key entry therefore reaches this
        query unchanged and is resolved here, by the ``storage_key`` comparison in
        :meth:`_aql_unreferenced`.
        """
        # ``@ignored_task_key`` discounts one task's own references, for the route
        # that deletes a photo *from* that task. Applied to the tasks collection
        # only; every other carrier still protects the photo.
        skip = " FILTER d._key != @ignored_task_key" if ignore_task_key else ""

        def tenant(collection: str) -> str:
            """The tenant narrowing, for the collections that can carry it.

            Emitted only when the caller passes a tenant (the interactive delete
            route). The nightly sweep is installation-wide and passes none, so it
            keeps reading every tenant's references — it has no tenant to narrow to
            and no interactive latency to answer for.
            """
            if not tenant_scoped or collection not in TENANT_SCOPED_REF_COLLECTIONS:
                return ""
            # An *unstamped* row still protects. ``tenant_key`` defaults to ``""`` on
            # ``Task``, ``PlantDiaryEntry`` and ``Inspection``, so a legacy or imported
            # carrier written before the tenant backfill carries no value — and a
            # strict equality would drop it from the scan, reporting a photo it still
            # references as unreferenced. That is the direction that destroys data, so
            # the narrowing gives up its saving for those rows rather than its
            # correctness. (#1393 round 7, finding 3)
            return ' FILTER d.tenant_key == @ref_tenant_key OR d.tenant_key == null OR d.tenant_key == ""'

        parts = [
            f"          (FOR d IN @@ref_col_{index}"
            f"{tenant(PHOTO_REF_COLLECTIONS[index])}"
            f"{skip if PHOTO_REF_COLLECTIONS[index] == col.TASKS else ''}"
            f" RETURN d.photo_refs || [])"
            for index in range(len(PHOTO_REF_COLLECTIONS))
        ]
        # ``IS_ARRAY`` so one expression serves both a list field and a scalar one.
        # The field name is interpolated rather than bound because AQL binds
        # collections (``@@``) and values (``@``), not attribute names; every name
        # comes from the module-level tuple above, never from a caller.
        parts += [
            f"          (FOR d IN @@extra_col_{index}{tenant(collection)} "
            f"RETURN IS_ARRAY(d.{field}) ? d.{field} : (d.{field} == null ? [] : [d.{field}]))"
            for index, (collection, field) in enumerate(ATTACHMENT_REF_FIELDS)
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
    def _aql_unreferenced(candidates_expression: str, attachment_expression: str) -> str:
        """AQL: is this attachment mentioned by **none** of the resolved candidates?

        Matched on exact candidates, against **both** identities an attachment has.

        *The document key.* Not a ULID — round 7 measured it: ``_to_doc`` pops
        ``_key`` before the insert and no key generator is configured, so ArangoDB's
        traditional generator assigns a short **numeric** key (``1024799``). The
        previous version was a ``CONTAINS`` substring test justified by "a ULID is 26
        characters from Crockford's alphabet, so an incidental match is not a
        practical concern". Against numeric keys that argument collapses: a key is a
        substring of a longer sibling id, of a ``/thumbnails/320`` size, of a
        ``…/2026/01/…`` date partition. Every coincidence reported the photo as
        shared, which makes it undeletable by the route *and* unsweepable — the quota
        leak this whole change exists to close.

        *The storage key's stem.* ``StorageKeyBuilder.build`` mints its own ULID when
        the caller passes none, and ``upload`` passes none, so the ULID in
        ``t/{tenant}/task/2026/01/{ulid}.jpg`` is unrelated to ``_key``. Deriving a
        key from such a reference is therefore impossible in either direction; the
        only way to connect them is to compare the reference against the attachment's
        *own* ``storage_key``. Without this half a ``photo_refs`` entry holding a
        storage key protected nothing and the sweep destroyed a referenced photo.

        Exact rather than fuzzy is affordable because the write path is narrow:
        ``TaskService._verify_photo_refs`` resolves every new reference through
        ``attachment_repo.get(ref, tenant_key)``, a document-key lookup, so nothing
        but a bare key can enter ``task.photo_refs`` today. The other spellings are
        legacy rows and other carriers' writers, and each of those shapes is a path
        whose segments this resolves.
        """
        storage_stem = aql_storage_key_stem(f"{attachment_expression}.storage_key")
        return (
            f"{attachment_expression}._key NOT IN {candidates_expression}"
            f" AND ({attachment_expression}.storage_key == null"
            f" OR {storage_stem} NOT IN {candidates_expression})"
        )

    def _reference_bind_vars(self) -> dict[str, Any]:
        """The collection bindings :meth:`_aql_referenced_prelude` needs."""
        bind_vars: dict[str, Any] = {}
        for index, collection in enumerate(PHOTO_REF_COLLECTIONS):
            bind_vars[f"@ref_col_{index}"] = collection
        for index, (collection, _field) in enumerate(ATTACHMENT_REF_FIELDS):
            bind_vars[f"@extra_col_{index}"] = collection
        return bind_vars

    def task_photo_delete_state(self, attachment_id: str, tenant_key: str, *, task_key: str) -> tuple[str, str | None]:
        """What ``DELETE /tasks/{task_key}/photos/{attachment_id}`` needs to know (#1393).

        Returns ``(state, created_by)`` where *state* is one of:

        ``"shared"``
            Some carrier other than the named task references it. Never deletable
            here — sha256 deduplication gives one stored object to several carriers,
            and destroying it would leave a plant gallery or another task pointing at
            nothing.
        ``"task"``
            The named task references it and nothing else does. This is the task's
            own documentation; whoever may delete the tenant's attachments may delete
            it.
        ``"staged"``
            Nothing anywhere references it — an upload whose form has not been
            submitted. The task key in the path constrains nothing for such a photo
            (it is in no task's list, so "no *other* task references it" is true
            through every task of the tenant), so the caller falls back to
            ``created_by``.
        ``"missing"``
            No such attachment in this tenant; *created_by* is ``None``.

        **One round trip, one prelude.** The service used to ask
        :meth:`unreferenced_among` twice — once ignoring the task and once not — and
        then call :meth:`by_keys`. The two questions differ only in whether the named
        task counts, but each call re-ran the whole nine-collection reference scan, so
        a single click on "remove photo" cost roughly eighteen collection scans inside
        an interactive request. Here the expensive half runs once, with the task
        excluded, and the task's own list is fetched by primary key — a lookup, not a
        scan — which is what makes the second question nearly free.
        """
        query = f"""
{self._aql_referenced_prelude(ignore_task_key=True, tenant_scoped=True)}
        LET own_refs = FIRST(
          FOR t IN @@task_collection
            FILTER t._key == @ignored_task_key AND t.tenant_key == @ref_tenant_key
            RETURN t.photo_refs || []
        ) || []
        FOR att IN @@collection
          FILTER att._key == @attachment_id AND att.tenant_key == @tenant_key
          LET own_candidates = UNIQUE(FLATTEN(
            (FOR ref IN own_refs RETURN {aql_photo_ref_candidates("ref")}), 2
          ))
          LET unshared = {self._aql_unreferenced("referenced", "att")}
          LET absent_from_task = {self._aql_unreferenced("own_candidates", "att")}
          RETURN {{
            state: !unshared ? "shared" : (absent_from_task ? "staged" : "task"),
            created_by: att.created_by
          }}
        """
        bind_vars: dict[str, Any] = {
            "@collection": self._collection_name,
            "@task_collection": col.TASKS,
            "attachment_id": attachment_id,
            "tenant_key": tenant_key,
            "ref_tenant_key": tenant_key,
            "ignored_task_key": task_key,
            **self._reference_bind_vars(),
        }
        row = next(iter(self._db.aql.execute(query, bind_vars=bind_vars)), None)
        if row is None:
            return "missing", None
        return str(row["state"]), row.get("created_by")

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
            AND DATE_TIMESTAMP(att.created_at) != null
            AND DATE_TIMESTAMP(att.created_at) < DATE_TIMESTAMP(@cutoff)
            AND {self._aql_unreferenced("referenced", "att")}
          SORT DATE_TIMESTAMP(att.created_at) ASC
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
