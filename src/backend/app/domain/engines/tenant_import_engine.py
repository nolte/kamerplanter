"""Key remapping of a tenant import (REQ-056 §8.4, #2138).

Pure logic, no I/O. An archive carries its source installation's keys. ArangoDB
generates ``_key`` per collection and it is unique across tenants, so a document
written back with its old key would collide with — or overwrite — a row of
another tenant in a shared database. The import therefore gives **every**
document a new key and rewrites every reference through one mapping table per
collection; which fields are references is declared once, in
:class:`~app.domain.engines.tenant_export_engine.TenantExportEngine`.

Rules per reference kind (``TenantReference.kind``):

* ``tenant`` — the source tenant's key becomes the new tenant's; empty stays
  empty; any other tenant key refuses the archive (it names a tenant the archive
  does not own).
* ``internal`` — a row of the archive → its new key. A key the archive does not
  hold: a global catalogue row of the target when a target collection is a
  (hybrid) catalogue — collected first and checked by the service
  (``IMPORT_MISSING_CATALOG_ENTRIES``); otherwise a dangling pointer of the
  source, which is **cleared**, never kept (a kept key could name a row of
  another tenant in the target database).
* ``global`` — kept; collected for the catalogue check.
* ``account`` — an account the admin mapped → that account; anything else
  becomes the pseudonym ``_anonymized`` (§8.4 step 4). A pseudonym or an erasure
  tombstone stays as it is.
* ``storage`` / ``attachment`` — ``t/<source>/…`` becomes ``t/<new>/…``; an
  attachment id is mapped like an internal reference.
* ``polymorphic`` — the sibling discriminator names the collection, then as
  ``internal``; an unknown discriminator clears the reference.

A ``*_key`` path no declaration covers refuses the archive
(``IMPORT_UNDECLARED_REFERENCE``): writing it unchanged is the one thing the
import must never do.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from app.domain.engines.tenant_export_engine import (
    ANONYMIZED_ACCOUNT,
    TenantArchiveError,
    TenantExportEngine,
    TenantReference,
    is_tombstone_or_pseudonym,
)
from app.domain.models.tenant_export import TenantArchive

#: Sentinel for "drop this value" while rewriting.
_CLEARED = object()


def new_document_key() -> str:
    """A fresh document key: random, so it can never equal a key the source or the target already uses."""
    return uuid.uuid4().hex


class TenantImportEngine:
    """Plans and applies the key mapping of one import."""

    def __init__(
        self,
        archive: TenantArchive,
        *,
        target_tenant_key: str,
        member_accounts: dict[str, str],
        key_factory: Callable[[], str] = new_document_key,
    ) -> None:
        self._archive = archive
        self._source = archive.source_tenant_key
        self._target = target_tenant_key
        self._members: dict[str, str] = dict(member_accounts)
        self._exported = set(TenantExportEngine.exported_collections())
        self._catalogues = TenantExportEngine.global_catalogues()
        self._hybrid = TenantExportEngine.HYBRID_CATALOGUES
        self.mapping: dict[str, dict[str, str]] = {}
        self.nulled_references = 0
        for collection, documents in archive.collections.items():
            table: dict[str, str] = {}
            for row in documents:
                document: dict[str, Any] = row
                old = document.get("_key")
                if isinstance(old, str) and old:
                    table[old] = key_factory()
            self.mapping[collection] = table

    # ── validation (before anything is written) ─────────────────────────

    @staticmethod
    def validate_structure(archive: TenantArchive) -> None:
        """Refuse an archive whose collections, keys or reference paths the import cannot place."""
        exported = set(TenantExportEngine.exported_collections())
        unknown = sorted(set(archive.collections) - exported)
        if unknown:
            raise TenantArchiveError(
                "IMPORT_FORMAT_UNSUPPORTED",
                "the archive carries collections a tenant import does not write",
                entries=unknown,
            )
        undeclared: set[str] = set()
        for collection, documents in archive.collections.items():
            seen: set[str] = set()
            for row in documents:
                document: dict[str, Any] = row
                key = document.get("_key")
                if not isinstance(key, str) or not key or key in seen:
                    raise TenantArchiveError(
                        "IMPORT_FORMAT_UNSUPPORTED", f"{collection}: a document without a unique _key"
                    )
                seen.add(key)
                undeclared.update(
                    f"{collection}.{path}"
                    for path in TenantExportEngine.undeclared_reference_paths(collection, document)
                )
        for name, edges in archive.edges.items():
            for row in edges:
                edge: dict[str, Any] = row
                if not isinstance(edge.get("_from"), str) or not isinstance(edge.get("_to"), str):
                    raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", f"{name}: an edge without _from/_to")
                fields: list[str] = list(edge)
                undeclared.update(
                    f"{name}.{field}"
                    for field in fields
                    if field[:1] != "_" and TenantExportEngine.looks_like_reference(field) and field != "tenant_key"
                )
        if undeclared:
            raise TenantArchiveError(
                "IMPORT_UNDECLARED_REFERENCE",
                "the archive carries reference fields this installation does not know how to rewrite",
                entries=sorted(undeclared),
            )

    def catalogue_requirements(self) -> dict[str, set[str]]:
        """Every global catalogue row the archive points at: ``collection -> keys`` (to be checked by the store)."""
        needed: dict[str, set[str]] = {}
        for collection, documents in self._archive.collections.items():
            for row in documents:
                document: dict[str, Any] = row
                for reference, value in self._references_in(collection, document):
                    self._require_catalogue(needed, reference, value, document)
        for edges in self._archive.edges.values():
            for row in edges:
                edge: dict[str, Any] = row
                for end in ("_from", "_to"):
                    document_id: str = str(edge[end])
                    collection, _, key = document_id.partition("/")
                    if collection in self._catalogues or (
                        collection in self._hybrid and key not in self._table(collection)
                    ):
                        needed.setdefault(collection, set()).add(key)
        return needed

    def _table(self, collection: str) -> dict[str, str]:
        return self.mapping.get(collection, {})

    def _require_catalogue(
        self, needed: dict[str, set[str]], reference: TenantReference, value: str, document: dict[str, Any]
    ) -> None:
        targets = self._targets_of(reference, document)
        if reference.kind == "global":
            needed.setdefault("|".join(targets), set()).add(value)
        elif reference.kind == "internal" and not any(value in self._table(t) for t in targets):
            capable = tuple(t for t in targets if t in self._hybrid or t in self._catalogues)
            if capable:
                needed.setdefault("|".join(capable), set()).add(value)

    # ── rewriting ──────────────────────────────────────────────────────

    def remap_document(self, collection: str, document: dict[str, Any], *, existing_global: set[str]) -> dict[str, Any]:
        """The document as the target stores it: new ``_key``, every declared reference rewritten.

        ``existing_global`` holds ``"<collection>/<key>"`` of every catalogue row the
        target has (the service resolved :meth:`catalogue_requirements`).
        """
        old_key = str(document["_key"])
        rewritten = {name: value for name, value in document.items() if name not in ("_id", "_rev")}
        rewritten["_key"] = self.mapping[collection][old_key]
        references = TenantExportEngine.references_of(collection)
        for path, reference in references.items():
            dotted: str = path
            segments: list[str] = dotted.split(".")
            self._rewrite_path(rewritten, segments, reference, rewritten, existing_global)
        return rewritten

    def remap_edge(self, edge: dict[str, Any], *, existing_global: set[str]) -> dict[str, Any] | None:
        """The edge with both ends rewritten, or ``None`` when an end has no place in the target."""
        ends: dict[str, str] = {}
        for end in ("_from", "_to"):
            resolved = self._resolve_id(str(edge[end]), existing_global)
            if resolved is None:
                return None
            ends[end] = resolved
        rewritten = {name: value for name, value in edge.items() if name not in ("_id", "_rev", "_key", "_from", "_to")}
        rewritten.update(ends)
        if "tenant_key" in rewritten:
            rewritten["tenant_key"] = self._rewrite_tenant(rewritten["tenant_key"])
        return rewritten

    def rewrite_storage_key(self, value: str) -> str:
        prefix = f"t/{self._source}/"
        if value.startswith(prefix):
            return f"t/{self._target}/{value[len(prefix) :]}"
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "an object key outside the source tenant's namespace")

    # ── internals ──────────────────────────────────────────────────────

    def _targets_of(self, reference: TenantReference, document: dict[str, Any]) -> tuple[str, ...]:
        if reference.kind == "polymorphic":
            target = reference.by_value.get(str(document.get(reference.discriminator or "")))
            return (target,) if target else ()
        return reference.targets

    def _references_in(self, collection: str, document: dict[str, Any]) -> list[tuple[TenantReference, str]]:
        """Every non-empty string value at a declared reference path of *document*."""
        found: list[tuple[TenantReference, str]] = []
        for path, reference in TenantExportEngine.references_of(collection).items():
            dotted: str = path
            for value in _values_at(document, dotted.split(".")):
                if isinstance(value, str) and value:
                    found += [(reference, value)]
        return found

    def _rewrite_path(
        self,
        node: Any,
        segments: list[str],
        reference: TenantReference,
        document: dict[str, Any],
        existing_global: set[str],
    ) -> None:
        if isinstance(node, list):
            for item in node:
                self._rewrite_path(item, segments, reference, document, existing_global)
            return
        if not isinstance(node, dict) or segments[0] not in node:
            return
        head, rest = segments[0], segments[1:]
        if rest:
            self._rewrite_path(node[head], rest, reference, document, existing_global)
            return
        value = node[head]
        if isinstance(value, list):
            kept = [self._rewrite_value(item, reference, document, existing_global) for item in value]
            node[head] = [item for item in kept if item is not _CLEARED]
        else:
            result = self._rewrite_value(value, reference, document, existing_global)
            node[head] = None if result is _CLEARED else result

    def _rewrite_value(
        self, value: Any, reference: TenantReference, document: dict[str, Any], existing_global: set[str]
    ) -> Any:
        if not isinstance(value, str) or not value:
            return value
        kind = reference.kind
        if kind == "opaque":
            return value
        if kind == "tenant":
            return self._rewrite_tenant(value)
        if kind == "account":
            if is_tombstone_or_pseudonym(value):
                return value
            return self._members.get(value, ANONYMIZED_ACCOUNT)
        text: str = value
        if kind == "storage":
            return self.rewrite_storage_key(text) if text.startswith("t/") else text
        if kind == "attachment":
            if text.startswith("t/"):
                return self.rewrite_storage_key(value)
            return self._internal(value, ("attachments",), existing_global)
        if kind == "global":
            return value
        targets = self._targets_of(reference, document)
        if not targets:
            self.nulled_references += 1
            return _CLEARED
        return self._internal(value, targets, existing_global)

    def _internal(self, value: str, targets: tuple[str, ...], existing_global: set[str]) -> Any:
        for target in targets:
            mapped = self.mapping.get(target, {}).get(value)
            if mapped is not None:
                return mapped
        if any(f"{target}/{value}" in existing_global for target in targets):
            return value
        self.nulled_references += 1
        return _CLEARED

    def _rewrite_tenant(self, value: Any) -> Any:
        if value in (None, ""):
            return value
        if value == self._source:
            return self._target
        raise TenantArchiveError("IMPORT_FORMAT_UNSUPPORTED", "the archive carries a row of another tenant")

    def _resolve_id(self, document_id: str, existing_global: set[str]) -> str | None:
        collection, _, key = document_id.partition("/")
        if collection == "tenants":
            return f"tenants/{self._target}" if key == self._source else None
        mapped = self.mapping.get(collection, {}).get(key)
        if mapped is not None:
            return f"{collection}/{mapped}"
        if document_id in existing_global:
            return document_id
        return None


def _values_at(node: Any, segments: list[str]) -> list[Any]:
    """Every value at *segments* in *node*, walking lists transparently (lists at the leaf are flattened)."""
    if isinstance(node, list):
        return [value for item in node for value in _values_at(item, segments)]
    if not isinstance(node, dict) or segments[0] not in node:
        return []
    value = node[segments[0]]
    if len(segments) > 1:
        return _values_at(value, segments[1:])
    return list(value) if isinstance(value, list) else [value]
