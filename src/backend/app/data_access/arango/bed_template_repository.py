"""ArangoDB persistence of the bed templates (REQ-053 §20.12; WP 7.8, #2474).

``bed_templates`` (migration v0093) holds two kinds of row: a tenant's own (``tenant_key`` = the tenant) and the
system templates (``tenant_key`` absent / ``null``, written by migration v0101 under a fixed ``_key``). Every read
filters on the tenant **inside** the query and admits exactly those two arms; every write names the row's owner
and matches on it, so a tenant's write can never land on a system row (or the reverse) and another tenant's row
answers like an absent one. Deleting a template also unsets ``locations.template_key`` on the beds placed from it,
in the same stream transaction (#2528).

The index ``(tenant_key, name)`` (v0101) leads with ``tenant_key`` like every tenant-bearing index
(``test_tenant_unique_indexes_are_scoped``); it is not unique - two templates may share a name.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import structlog
from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.common.exceptions import NotFoundError
from app.common.types import BedTemplateKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.data_access.arango.transactions import StreamTransaction, stream_transaction
from app.domain.interfaces.bed_template_repository import IBedTemplateRepository
from app.domain.models.bed_template import BedTemplate

logger = structlog.get_logger()

#: A row the tenant may read: its own or a system one (``tenant_key`` is ``null`` or absent).
_VISIBLE = "(t.tenant_key == @tenant_key OR t.tenant_key == null)"


class ArangoBedTemplateRepository(BaseArangoRepository[BedTemplate], IBedTemplateRepository):
    """``bed_templates`` (v0093)."""

    _model_cls = BedTemplate
    is_tenant_scoped = True

    def __init__(self, db: StandardDatabase) -> None:
        super().__init__(db, col.BED_TEMPLATES)

    def _wrapped(self, doc: dict[str, Any]) -> BedTemplate:
        return BedTemplate(**self._from_doc(doc))

    # ── Reads ─────────────────────────────────────────────────────────────

    def list_visible(self, *, tenant_key: str, offset: int, limit: int) -> list[BedTemplate]:
        self._require_tenant_key(tenant_key, "list_visible")
        bind_vars: dict[str, Any] = {
            "@templates": col.BED_TEMPLATES,
            "tenant_key": tenant_key,
            "offset": offset,
            "limit": limit,
        }
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            FOR t IN @@templates
                FILTER {_VISIBLE}
                SORT t.name ASC, t._key ASC
                LIMIT @offset, @limit
                RETURN t
            """,
                bind_vars=bind_vars,
            ),
        )
        return [self._wrapped(doc) for doc in cursor]

    def get_visible_by_key(self, key: BedTemplateKey, *, tenant_key: str) -> BedTemplate | None:
        self._require_tenant_key(tenant_key, "get_visible_by_key")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            FOR t IN @@templates
                FILTER t._key == @key AND {_VISIBLE}
                LIMIT 1
                RETURN t
            """,
                bind_vars={"@templates": col.BED_TEMPLATES, "key": key, "tenant_key": tenant_key},
            ),
        )
        doc = next(cursor, None)
        return self._wrapped(doc) if doc is not None else None

    def visible_keys(self, keys: list[BedTemplateKey], *, tenant_key: str) -> set[BedTemplateKey]:
        self._require_tenant_key(tenant_key, "visible_keys")
        if not keys:
            return set()
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            FOR t IN @@templates
                FILTER t._key IN @keys AND {_VISIBLE}
                RETURN t._key
            """,
                bind_vars={"@templates": col.BED_TEMPLATES, "keys": sorted(set(keys)), "tenant_key": tenant_key},
            ),
        )
        return {str(key) for key in cursor}

    def count_owned(self, *, tenant_key: str) -> int:
        self._require_tenant_key(tenant_key, "count_owned")
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                "RETURN LENGTH(FOR t IN @@templates FILTER t.tenant_key == @tenant_key RETURN 1)",
                bind_vars={"@templates": col.BED_TEMPLATES, "tenant_key": tenant_key},
            ),
        )
        return int(next(iter(cursor), 0) or 0)

    # ── Writes ────────────────────────────────────────────────────────────

    def create_template(self, template: BedTemplate) -> BedTemplate:
        return self.create(template)

    def update_template(
        self, key: BedTemplateKey, fields: dict[str, Any], *, owner_tenant_key: str | None
    ) -> BedTemplate:
        owner = "t.tenant_key == @owner" if owner_tenant_key is not None else "t.tenant_key == null"
        bind_vars: dict[str, Any] = {
            "@templates": col.BED_TEMPLATES,
            "key": key,
            "fields": {**fields, "updated_at": datetime.now(UTC).isoformat()},
        }
        if owner_tenant_key is not None:
            bind_vars["owner"] = owner_tenant_key
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            FOR t IN @@templates
                FILTER t._key == @key AND {owner}
                UPDATE t WITH @fields IN @@templates OPTIONS {{ keepNull: false, mergeObjects: false }}
                RETURN NEW
            """,
                bind_vars=bind_vars,
            ),
        )
        doc = next(cursor, None)
        if doc is None:
            raise NotFoundError("BedTemplate", key)
        return self._wrapped(doc)

    def delete_template(self, key: BedTemplateKey, *, owner_tenant_key: str | None) -> bool:
        """Remove the template of that owner and unset ``template_key`` on the beds placed from it, atomically.

        ``template_key`` is provenance (REQ-053 §20.12, #2528): once the template is gone it names nothing, and a
        dangling key would make a tenant-archive re-import refuse the archive. A tenant template releases only the
        beds whose **site** belongs to that tenant (``locations`` carry no ``tenant_key``; the site is the anchor,
        MT-010) - another tenant's row carrying the same key is not this delete's business. A system template (only
        a platform admin deletes one) releases the beds of every tenant. A refused delete (not the owner's row)
        touches no bed.
        """
        with stream_transaction(
            self._db,
            write=(col.BED_TEMPLATES, col.LOCATIONS),
            read=(col.SITES, col.CONTAINS),
            entity="bed_template",
        ) as txn:
            if not self._remove_owned_template(txn, key, owner_tenant_key=owner_tenant_key):
                return False
            released = self._unset_template_key(txn, key, owner_tenant_key=owner_tenant_key)
        # After the commit: the service logs ``bed_template.deleted``; the released-bed count is only known here.
        logger.info("bed_template.beds_released", template_key=key, released_beds=released)
        return True

    @staticmethod
    def _remove_owned_template(txn: StreamTransaction, key: BedTemplateKey, *, owner_tenant_key: str | None) -> bool:
        owner = "t.tenant_key == @owner" if owner_tenant_key is not None else "t.tenant_key == null"
        bind_vars: dict[str, Any] = {"@templates": col.BED_TEMPLATES, "key": key}
        if owner_tenant_key is not None:
            bind_vars["owner"] = owner_tenant_key
        cursor = txn.aql.execute(
            f"""
            FOR t IN @@templates
                FILTER t._key == @key AND {owner}
                REMOVE t IN @@templates
                RETURN 1
            """,
            bind_vars=bind_vars,
        )
        return next(iter(cursor), None) is not None

    @staticmethod
    def _unset_template_key(txn: StreamTransaction, key: BedTemplateKey, *, owner_tenant_key: str | None) -> int:
        """Unset ``template_key == key`` on the owner's beds (every tenant's for a system template); the count."""
        bind_vars: dict[str, Any] = {"@locations": col.LOCATIONS, "key": key}
        site_clause = ""
        if owner_tenant_key is not None:
            # A nested legacy bed may carry no ``site_key`` (#2513): its site is then the first site above it on the
            # ``contains`` graph (site -> location, parent location -> child, so the walk goes INBOUND).
            site_clause = """
                LET site = DOCUMENT(@@sites, l.site_key) || FIRST(
                    FOR v IN 1..20 INBOUND l @@contains
                        FILTER IS_SAME_COLLECTION(@@sites, v)
                        LIMIT 1
                        RETURN v
                )
                FILTER site.tenant_key == @owner"""
            bind_vars["@sites"] = col.SITES
            bind_vars["@contains"] = col.CONTAINS
            bind_vars["owner"] = owner_tenant_key
        cursor = txn.aql.execute(
            f"""
            FOR l IN @@locations
                FILTER l.template_key == @key {site_clause}
                UPDATE l WITH {{ template_key: null }} IN @@locations OPTIONS {{ keepNull: false }}
                RETURN OLD._key
            """,
            bind_vars=bind_vars,
        )
        return len(list(cursor))

    # ── References of a template ──────────────────────────────────────────

    def bed_type_flags(self, location_type_keys: list[str]) -> dict[str, bool]:
        if not location_type_keys:
            return {}
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                "FOR t IN @@col FILTER t._key IN @keys RETURN {key: t._key, is_bed: t.is_bed == true}",
                bind_vars={"@col": col.LOCATION_TYPES, "keys": sorted(set(location_type_keys))},
            ),
        )
        return {row["key"]: row["is_bed"] for row in cursor}

    def visible_task_template_keys(self, keys: list[str], *, tenant_key: str) -> set[str]:
        self._require_tenant_key(tenant_key, "visible_task_template_keys")
        if not keys:
            return set()
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                """
            FOR t IN @@templates
                FILTER t._key IN @keys AND (t.tenant_key == @tenant_key OR t.tenant_key == "" OR t.tenant_key == null)
                RETURN t._key
            """,
                bind_vars={"@templates": col.TASK_TEMPLATES, "keys": sorted(set(keys)), "tenant_key": tenant_key},
            ),
        )
        return {str(key) for key in cursor}
