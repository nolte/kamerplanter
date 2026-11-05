"""ArangoDB writes of a bed's photos (REQ-053 GP-FR-051, WP 8.18), see the interface module of the same name."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from arango.database import StandardDatabase

from app.common.enums import AttachmentCategory
from app.data_access.arango import collections as col
from app.data_access.arango.transactions import StreamTransaction, stream_transaction
from app.domain.interfaces.location_photo_repository import (
    ILocationPhotoRepository,
    LocationPhotoState,
    LocationPhotoWrite,
)

#: The bed **through its site's tenant** (a location carries no ``tenant_key``, #2107): a key of another tenant's
#: bed finds no row, exactly like an absent one.
_OWNED_LOCATION = """
FOR l IN @@locations
    FILTER l._key == @location_key
    FOR s IN @@sites
        FILTER s._key == l.site_key AND s.tenant_key == @tenant_key
        LIMIT 1
        RETURN {photo_refs: l.photo_refs || [], cover_photo_ref: l.cover_photo_ref}
"""

#: The tenant's own ``location`` attachment, touched so a concurrent removal of the record conflicts (#2545).
_TOUCH_ATTACHMENT = """
FOR a IN @@attachments
    FILTER a._key == @attachment_key AND a.tenant_key == @tenant_key AND a.category == @category
    UPDATE a WITH { updated_at: @now } IN @@attachments
    RETURN 1
"""

_WRITE_PHOTOS = """
UPDATE { _key: @location_key }
    WITH { photo_refs: @photo_refs, cover_photo_ref: @cover_photo_ref, updated_at: @now }
    IN @@locations
    OPTIONS { keepNull: false }
"""


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ArangoLocationPhotoRepository(ILocationPhotoRepository):
    def __init__(self, db: StandardDatabase) -> None:
        self._db = db

    @staticmethod
    def _require_tenant(tenant_key: str, operation: str) -> None:
        if not tenant_key:
            raise ValueError(f"{operation} needs a tenant_key (an empty tenant is no tenant, #2107).")

    @staticmethod
    def _read(txn: StreamTransaction, location_key: str, tenant_key: str) -> LocationPhotoState | None:
        rows: list[dict[str, Any]] = list(
            txn.aql.execute(
                _OWNED_LOCATION,
                bind_vars={
                    "@locations": col.LOCATIONS,
                    "@sites": col.SITES,
                    "location_key": location_key,
                    "tenant_key": tenant_key,
                },
            )
        )
        if not rows:
            return None
        refs = rows[0].get("photo_refs") or []
        return LocationPhotoState(
            photo_refs=tuple(str(ref) for ref in refs),
            cover_photo_ref=rows[0].get("cover_photo_ref"),
        )

    @staticmethod
    def _write(txn: StreamTransaction, location_key: str, state: LocationPhotoState) -> None:
        txn.aql.execute(
            _WRITE_PHOTOS,
            bind_vars={
                "@locations": col.LOCATIONS,
                "location_key": location_key,
                "photo_refs": list(state.photo_refs),
                "cover_photo_ref": state.cover_photo_ref,
                "now": _now(),
            },
        )

    def add_photo(
        self, location_key: str, *, tenant_key: str, attachment_key: str, max_photos: int
    ) -> LocationPhotoWrite:
        self._require_tenant(tenant_key, "add_photo")
        with stream_transaction(
            self._db, write=(col.LOCATIONS, col.ATTACHMENTS), read=(col.SITES,), entity="location"
        ) as txn:
            stored = self._read(txn, location_key, tenant_key)
            if stored is None:
                return LocationPhotoWrite("location_not_found")
            touched = list(
                txn.aql.execute(
                    _TOUCH_ATTACHMENT,
                    bind_vars={
                        "@attachments": col.ATTACHMENTS,
                        "attachment_key": attachment_key,
                        "tenant_key": tenant_key,
                        "category": AttachmentCategory.LOCATION.value,
                        "now": _now(),
                    },
                )
            )
            if not touched:
                return LocationPhotoWrite("attachment_not_found")
            if attachment_key in stored.photo_refs:
                return LocationPhotoWrite("unchanged", stored)
            if len(stored.photo_refs) >= max_photos:
                return LocationPhotoWrite("limit_reached", stored)
            written = LocationPhotoState(
                photo_refs=(attachment_key, *stored.photo_refs),
                cover_photo_ref=stored.cover_photo_ref or attachment_key,
            )
            self._write(txn, location_key, written)
        return LocationPhotoWrite("written", written)

    def remove_photo(self, location_key: str, *, tenant_key: str, attachment_key: str) -> LocationPhotoWrite:
        self._require_tenant(tenant_key, "remove_photo")
        with stream_transaction(self._db, write=(col.LOCATIONS,), read=(col.SITES,), entity="location") as txn:
            stored = self._read(txn, location_key, tenant_key)
            if stored is None:
                return LocationPhotoWrite("location_not_found")
            if attachment_key not in stored.photo_refs:
                return LocationPhotoWrite("not_a_photo", stored)
            written = LocationPhotoState(
                photo_refs=tuple(ref for ref in stored.photo_refs if ref != attachment_key),
                cover_photo_ref=None if stored.cover_photo_ref == attachment_key else stored.cover_photo_ref,
            )
            self._write(txn, location_key, written)
        return LocationPhotoWrite("written", written)

    def set_cover(self, location_key: str, *, tenant_key: str, attachment_key: str | None) -> LocationPhotoWrite:
        self._require_tenant(tenant_key, "set_cover")
        with stream_transaction(self._db, write=(col.LOCATIONS,), read=(col.SITES,), entity="location") as txn:
            stored = self._read(txn, location_key, tenant_key)
            if stored is None:
                return LocationPhotoWrite("location_not_found")
            if attachment_key is not None and attachment_key not in stored.photo_refs:
                return LocationPhotoWrite("not_a_photo", stored)
            if stored.cover_photo_ref == attachment_key:
                return LocationPhotoWrite("unchanged", stored)
            written = LocationPhotoState(photo_refs=stored.photo_refs, cover_photo_ref=attachment_key)
            self._write(txn, location_key, written)
        return LocationPhotoWrite("written", written)


__all__ = ["ArangoLocationPhotoRepository"]
