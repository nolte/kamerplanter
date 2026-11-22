"""Doubles for the bed photos (REQ-053 WP 8.18): the photo repository over a :class:`FakePlanRepo`'s locations, and
one object that is the attachment repository and the ``delete_if_unreferenced`` slice of ``AttachmentService``.

The photo repository applies the same rules as ``ArangoLocationPhotoRepository`` (the bed through its site's
tenant, the tenant's own ``location`` record, newest first, the bound) - the transaction itself is measured
against ArangoDB in ``tests/integration/test_location_photo_repository.py``.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from app.common.enums import AttachmentCategory
from app.domain.interfaces.location_photo_repository import (
    ILocationPhotoRepository,
    LocationPhotoState,
    LocationPhotoWrite,
    without_photo,
)
from app.domain.models.attachment import Attachment
from app.domain.services.attachment_service import ObjectReleaseError
from tests.support.garden_plan_fakes import FakePlanRepo


class FakePhotoAttachments:
    """``get`` is tenant-scoped; ``delete_if_unreferenced`` keeps a record any bed still names, like the real scan."""

    def __init__(self, repo: FakePlanRepo) -> None:
        self._repo = repo
        self.rows: dict[str, Attachment] = {}
        self.deleted: list[str] = []
        self.kept: list[str] = []
        #: Set to make every ``delete_if_unreferenced`` raise (storage down, the scan's budget exhausted).
        self.fail_with: Exception | None = None
        #: Ids another carrier (a plant gallery, a task, a bed of another site …) still names.
        self.held_elsewhere: set[str] = set()
        #: Keys read one by one, and the key lists read in one round trip.
        self.reads: list[str] = []
        self.batch_reads: list[list[str]] = []
        #: Set to make the batch's object release fail after its records went (#2715 review SEC-S02).
        self.objects_fail = False
        #: The id lists handed to ``delete_many_if_unreferenced``, one entry per call.
        self.batch_deletes: list[list[str]] = []

    def add(
        self,
        key: str,
        *,
        tenant_key: str,
        category: AttachmentCategory = AttachmentCategory.LOCATION,
        created_by: str = "u_sabine",
    ) -> Attachment:
        row = Attachment(
            _key=key,
            tenant_key=tenant_key,
            mime_type="image/jpeg",
            byte_size=10,
            sha256="0" * 64,
            original_filename="beet.jpg",
            created_by=created_by,
            category=category,
            storage_key=f"t/{tenant_key}/{category.value}/2026/11/{key}.jpg",
        )
        self.rows[key] = row
        return row

    def get(self, key: str, tenant_key: str) -> Attachment | None:
        self.reads.append(key)
        row = self.rows.get(key)
        return row if row is not None and row.tenant_key == tenant_key else None

    def get_many(self, keys: Sequence[str], *, tenant_key: str) -> dict[str, Attachment]:
        """One round trip, as the ArangoDB repository answers it (#2715 item 7)."""
        self.batch_reads.append(list(keys))
        return {key: row for key in keys if (row := self.rows.get(key)) is not None and row.tenant_key == tenant_key}

    def releasable_after_location_delete(
        self, attachment_ids: Sequence[str], *, tenant_key: str, location_keys: Sequence[str]
    ) -> list[str]:
        """The rule of :meth:`delete_if_unreferenced`, asked with *location_keys* already gone (#2715 review F)."""
        gone = set(location_keys)
        named = {
            ref
            for key, loc in self._repo.locations.items()
            if key not in gone
            for ref in [*loc.photo_refs, *([loc.cover_photo_ref] if loc.cover_photo_ref else [])]
        }
        return [
            key
            for key in dict.fromkeys(attachment_ids)
            if (row := self.get(key, tenant_key)) is not None
            and row.category == AttachmentCategory.LOCATION
            and key not in named
            and key not in self.held_elsewhere
        ]

    async def delete_if_unreferenced(self, attachment_id: str, tenant_key: str) -> bool:
        if self.fail_with is not None:
            raise self.fail_with
        named = any(
            attachment_id in loc.photo_refs or loc.cover_photo_ref == attachment_id
            for loc in self._repo.locations.values()
        )
        if named or attachment_id in self.held_elsewhere or self.get(attachment_id, tenant_key) is None:
            self.kept.append(attachment_id)
            return False
        self.rows.pop(attachment_id)
        self.deleted.append(attachment_id)
        return True

    async def delete_many_if_unreferenced(
        self, attachment_ids: Iterable[str], tenant_key: str, *, category: AttachmentCategory
    ) -> int:
        """One call for the batch (#2715 item 6), the rule of :meth:`delete_if_unreferenced` for each of *category*."""
        ids = list(dict.fromkeys(attachment_ids))
        self.batch_deletes.append(ids)
        if self.fail_with is not None:
            raise self.fail_with
        deleted: list[str] = []
        for attachment_id in ids:
            row = self.get(attachment_id, tenant_key)
            if row is None or row.category != category:
                continue
            if await self.delete_if_unreferenced(attachment_id, tenant_key):
                deleted.append(attachment_id)
        if deleted and self.objects_fail:
            # The records went; the storage did not (no retry store) - as ``AttachmentService`` reports it.
            raise ObjectReleaseError(removed=len(deleted), attachment_ids=deleted, objects=len(deleted))
        return len(deleted)


class FakeLocationPhotoRepo(ILocationPhotoRepository):
    def __init__(self, repo: FakePlanRepo, attachments: FakePhotoAttachments) -> None:
        self._repo = repo
        self._attachments = attachments

    def _owned(self, location_key: str, tenant_key: str) -> LocationPhotoState | None:
        location = self._repo.locations.get(location_key)
        if location is None:
            return None
        site = self._repo._sites.get_site_by_key(location.site_key)
        if site is None or site.tenant_key != tenant_key or not tenant_key:
            return None
        return LocationPhotoState(tuple(location.photo_refs), location.cover_photo_ref)

    def _write(self, location_key: str, state: LocationPhotoState) -> None:
        stored = self._repo.locations[location_key]
        self._repo.locations[location_key] = stored.model_copy(
            update={"photo_refs": list(state.photo_refs), "cover_photo_ref": state.cover_photo_ref}
        )

    def add_photo(
        self, location_key: str, *, tenant_key: str, attachment_key: str, max_photos: int
    ) -> LocationPhotoWrite:
        stored = self._owned(location_key, tenant_key)
        if stored is None:
            return LocationPhotoWrite("location_not_found")
        row = self._attachments.get(attachment_key, tenant_key)
        if row is None or row.category != AttachmentCategory.LOCATION:
            return LocationPhotoWrite("attachment_not_found")
        if attachment_key in stored.photo_refs:
            return LocationPhotoWrite("unchanged", stored)
        if len(stored.photo_refs) >= max_photos:
            return LocationPhotoWrite("limit_reached", stored)
        written = LocationPhotoState((attachment_key, *stored.photo_refs), stored.cover_photo_ref or attachment_key)
        self._write(location_key, written)
        return LocationPhotoWrite("written", written)

    def remove_photo(self, location_key: str, *, tenant_key: str, attachment_key: str) -> LocationPhotoWrite:
        stored = self._owned(location_key, tenant_key)
        if stored is None:
            return LocationPhotoWrite("location_not_found")
        if attachment_key not in stored.photo_refs:
            return LocationPhotoWrite("not_a_photo", stored)
        written = without_photo(stored, attachment_key)
        self._write(location_key, written)
        return LocationPhotoWrite("written", written)

    def set_cover(self, location_key: str, *, tenant_key: str, attachment_key: str | None) -> LocationPhotoWrite:
        stored = self._owned(location_key, tenant_key)
        if stored is None:
            return LocationPhotoWrite("location_not_found")
        if attachment_key is not None and attachment_key not in stored.photo_refs:
            return LocationPhotoWrite("not_a_photo", stored)
        written = LocationPhotoState(stored.photo_refs, attachment_key)
        self._write(location_key, written)
        return LocationPhotoWrite("written", written)
