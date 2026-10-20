"""ArangoDB persistence of the bed templates (REQ-053 §20.12; WP 7.8, #2474).

``bed_templates`` (migration v0093) holds two kinds of row: a tenant's own (``tenant_key`` = the tenant) and the
system templates (``tenant_key`` absent / ``null``, written by migration v0101 under a fixed ``_key``). Every read
filters on the tenant **inside** the query and admits exactly those two arms; every write names the row's owner
and matches on it, so a tenant's write can never land on a system row (or the reverse) and another tenant's row
answers like an absent one.

The index ``(tenant_key, name)`` (v0101) leads with ``tenant_key`` like every tenant-bearing index
(``test_tenant_unique_indexes_are_scoped``); it is not unique - two templates may share a name.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from arango.cursor import Cursor
from arango.database import StandardDatabase

from app.common.exceptions import NotFoundError
from app.common.types import BedTemplateKey
from app.data_access.arango import collections as col
from app.data_access.arango.base_repository import BaseArangoRepository
from app.domain.interfaces.bed_template_repository import IBedTemplateRepository
from app.domain.models.bed_template import BedTemplate

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
        owner = "t.tenant_key == @owner" if owner_tenant_key is not None else "t.tenant_key == null"
        bind_vars: dict[str, Any] = {"@templates": col.BED_TEMPLATES, "key": key}
        if owner_tenant_key is not None:
            bind_vars["owner"] = owner_tenant_key
        cursor = cast(
            "Cursor",
            self._db.aql.execute(
                f"""
            FOR t IN @@templates
                FILTER t._key == @key AND {owner}
                REMOVE t IN @@templates
                RETURN 1
            """,
                bind_vars=bind_vars,
            ),
        )
        return next(cursor, None) is not None

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
